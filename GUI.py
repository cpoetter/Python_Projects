import multiprocessing
import threading
import time
import Tkinter
import sys
from PIL import Image, ImageTk, ImageEnhance
import copy
import scipy.misc
import numpy as np
from ctypes import c_char_p
import tkMessageBox as messagebox

def close_GUI(app):
    time.sleep(2)
    print 'Shutdown GUI Thread.'
    app.q.put((None, ['GUI Shutdown']))
    time.sleep(3)
    print 'Shutdown GUI Process.'
    app.join()
    print 'GUI successfully closed.'
    return True

def push_image(app, img, txt=['']):
    app.q.put((img, txt))

class create_GUI(multiprocessing.Process):
    def __init__(self, window_size=None, max_photos_in_gui=100, len_queue=1000, debug=False):
        print 'Open GUI.'

        self.window_size = window_size
        self.max_photos_in_gui = max_photos_in_gui
        self.len_queue = len_queue
        self.debug = debug

        self.q = multiprocessing.Queue()
        self.manager = multiprocessing.Manager()
        self.photo_list = self.manager.list()
        self.message = self.manager.Value(c_char_p, "Waiting for data.")

        multiprocessing.Process.__init__(self)
        self.start()

    def get_photo(self):
        photo, label = self.q.get()

        if photo == None:
            if label[0] == 'GUI Shutdown':
                self.stop = True
                self.root.event_generate("<<shutdown>>", when="tail")
                time.sleep(1)
                self.gui.join()
            else:
                self.message.value = label[0]
                self.root.event_generate("<<message>>", when="tail")
        else:
            self.photo_list.append((photo, label))
            if self.debug == True:
                print"GUI Step 1: Image received, appended to current GUI image list"

            if len(self.photo_list) > self.max_photos_in_gui:
                self.photo_list.pop(0)

            try:
                self.root.event_generate("<<Put>>", when="tail")
            except:
                if self.debug == True:
                    print">>Warning in GUI Step 1: Informing GUI about new image in list failed<<"
                True

    def run(self):
        self.gui = GUI(self.window_size, self.max_photos_in_gui, self.len_queue, self.photo_list, self.message, self.debug, self)

        # wait for window to be created
        while True:
            try:
                self.root = self.gui.get_root()
            except:
                time.sleep(0.01)
                continue
            break

        self.stop = False
        while self.stop == False:
            self.get_photo()

class GUI(threading.Thread):

    def __init__(self, window_size, max_photos_in_gui, len_queue, photo_list, message, debug, parent):
        self.window_size = window_size
        self.max_photos_in_gui = max_photos_in_gui
        self.len_queue = len_queue
        self.photo_list = photo_list
        self.message = message
        self.overlay_message_visible = False
        self.debug = debug
        self.parent = parent

        threading.Thread.__init__(self)
        self.start()

    def close_window(self, *args):
        messagebox.showwarning("Quit", "You can not close this window")

    def callback(self, *args):
        self.root.destroy()

    def get_photo(self, event):
        if self.debug == True:
            print"GUI Step 2: New image in GUI List event triggered"
        if self.overlay_message_visible == True:
            self.text_overlay()
        if self.autoview_mode == True:
            self.update_photos()
        else:
            self.images_left_in_queue += 1
            # If maximum length of queue is exeeded
            if self.images_left_in_queue > self.len_queue:
                self.images_left_in_queue = 0
                self.toggle_autoview()

    def make_Tk_photo(self, img, label_content):
        if self.debug == True:
            print"GUI Step 4: New image rendered and canvas updated"
        
        if self.auto_contrast_on.get() == True:
            self.brightness_value = 0.0
            max_value = np.percentile(img, 99)
            auto_contrast_value = (255.0-self.brightness_value)/max_value
            self.contrast_value = auto_contrast_value

        img_converted = (img*self.contrast_value + self.brightness_value).clip(0,255).astype(np.uint8)
        if self.debug == True:
            print"GUI Step 4: Mean Image Value %.2f, Max %0.2f, Min %0.2f" % (np.mean(img_converted), np.max(img_converted), np.min(img_converted))
            print"GUI Step 4: Contrast %.2f, Brightness %.2f" % (self.contrast_value, self.brightness_value)
        max_sz = min(self.window_width/float(img_converted.shape[0]), self.window_height/float(img_converted.shape[1]))
        image = scipy.misc.imresize(img_converted, max_sz, interp='bilinear')
        im = Image.fromarray(image)
        (w, h) = im.size
        photo = ImageTk.PhotoImage(master = self.view_canvas, image=im, width=w, height=h)
        self.view_canvas.config(width=photo.width(), height=photo.height())
        self.view_canvas.create_image(0,0,image=photo,anchor=Tkinter.NW)
        self.view_canvas.image = photo # don't loose reference of image
        for l in range(len(label_content)):
            self.labels[l].config(text = label_content[l])
        self.current = (img, label_content)

    def update_photos(self):
        try: #sometimes list has 101 elements resulting from multithreading
            if self.debug == True:
                print"GUI Step 3: Update method called"
                print"GUI Step 3: Scrollbar position: %d" % self.scale.get()

            # First update scrollbar, then canvas, otherwise scrollbar can end up with list_len length and not list_len-1
            list_len = len(self.photo_list)
            if list_len != (self.scale.cget("to")+1):
                self.scale.config(to=list_len-1)
                self.scale.set(list_len-1)

            (img, label_content) = self.photo_list[self.scale.get()]
            self.make_Tk_photo(img, label_content)
        except:
            if self.debug == True:
                print">>Warning in GUI Step 3: Getting new image in updating method failed<<"
            pass

    def scrollbar_moved(self, value):
        try: #sometimes list has 101 elements
            if self.autoview_mode == False:
                (photo, label) = self.photos_autoview_off[int(value)]
            else:
                (photo, label) = self.photo_list[int(value)]
            self.make_Tk_photo(photo, label)
        except:
            pass

    def keyUp(self, event):
        self.scale.set(self.scale.get()-1)

    def keyDown(self, event):
        self.scale.set(self.scale.get()+1)

    def mouse_wheel(self, event):
        if event.num == 4:
            self.keyUp(event)
        if event.num == 5:
            self.keyDown(event)

    def mouse_pressed(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def mouse_press_and_move(self, event):
        widget = self.root.winfo_containing(event.x_root, event.y_root)

        if widget == self.view_canvas: # check if mouse click was over image or scrollbar
            movement_x = event.x - self.mouse_x
            movement_y = event.y - self.mouse_y

            self.contrast_value = self.contrast_value + movement_x/float(self.contrast_pixel_factor)
            self.brightness_value = self.brightness_value - movement_y/float(self.brightness_pixel_factor)

            if self.contrast_value > 2.0:
                self.contrast_value = 2.0
            elif self.contrast_value < -2.0:
                self.contrast_value = -2.0

            if self.brightness_value > 255.0:
                self.brightness_value = 255.0
            elif self.brightness_value < -255.0:
                self.brightness_value = -255.0

            self.mouse_x = event.x
            self.mouse_y = event.y

            self.scrollbar_moved(self.scale.get())
        else:
            pass

    def toggle_autoview(self, *args):
        if self.debug == True:
            print"Autoview toogled"
        if self.autoview_mode == True:
            try:
                self.autoview_mode = False
                self.autoview_button.config(text="Copy Data...", bg="yellow")
                self.autoview_button.update_idletasks()
                self.photos_autoview_off = copy.deepcopy(self.photo_list)
                self.autoview_button.config(text="Start Autoview", bg="green")
                # correction of position necessary, because list changed while copying due to multithreading
                position_of_element_while_stopping = [i for i,element in enumerate(self.photos_autoview_off) if np.array_equal(element[0],self.current[0])][0]
                self.scale.set(position_of_element_while_stopping)
            except:
                self.toggle_autoview()
        else:
            self.autoview_mode = True
            self.autoview_button.config(text="Stop Autoview", bg="red")
            # Jump to the newest image when turning on Autoview
            self.scale.set(self.scale.cget("to"))

    def text_overlay(self, *args):
        if self.overlay_message_visible == False:
            self.message_label.config(text = self.message.value)
            self.message_label.pack(expand=True)
            self.overlay_message_visible = True
        else:
            self.message_label.pack_forget()
            self.overlay_message_visible = False

    def received_text(self, *args):
        self.overlay_message_visible = False
        self.text_overlay()

    def checkbox_toogled(self, *args):
        # Draw Image new with new contrast if you activate auto contrast while no new images are comming
        if self.auto_contrast_on.get() == True:
            self.scrollbar_moved(self.scale.get())

    def run(self):
        self.photos_autoview_off = []
        self.images_left_in_queue = 0
        self.current = 0
        self.contrast_value = 1.0
        self.brightness_value = 0.0
        self.mouse_x = 0
        self.mouse_y = 0
        self.contrast_pixel_factor = 750.0
        self.brightness_pixel_factor = 2.0

        self.root = Tkinter.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        self.root.title('Muxrecon Autoviewer')
        #self.root.overrideredirect(1) #Remove Title bar

        scale_width = 16 #default width of scale is 16px

        if self.window_size is None:
            self.root.attributes('-fullscreen', True)
            self.window_width = self.root.winfo_screenwidth() - scale_width
            self.window_height = self.root.winfo_screenheight()
        else:
            self.root.resizable(0,0)
            self.window_width = self.window_size - scale_width
            self.window_height = self.window_size - scale_width

        self.frame = Tkinter.Frame(self.root, width=(self.window_width + scale_width), height=self.window_height, bg="black", name='frame')
        self.frame.pack_propagate(0)
        self.frame.pack(anchor=Tkinter.NW)

        self.scale = Tkinter.Scale(self.frame, from_=0, to=0, command=self.scrollbar_moved, length=self.window_height, showvalue=0, name='scale')
        self.scale.pack(side=Tkinter.RIGHT)

        self.inner_frame = Tkinter.Frame(self.frame, width=self.window_width, height=self.window_height, bg="black")
        self.inner_frame.pack_propagate(0)
        self.inner_frame.pack(anchor=Tkinter.NW)

        self.view_canvas = Tkinter.Canvas(self.inner_frame, width=self.window_width, height=self.window_height, name='view_canvas', bg="black", highlightbackground="black")
        self.view_canvas.place(relx=0.5, rely=0.5, anchor=Tkinter.CENTER)

        self.labels = []
        for i in range(4):
            self.labels.append(Tkinter.Label(self.inner_frame, fg="white", bg="black"))

        self.labels[0].place(relx=0, rely = 0, anchor = Tkinter.NW)
        self.labels[1].place(relx=1, rely = 0, anchor = Tkinter.NE)
        self.labels[2].place(relx=1, rely = 1, anchor = Tkinter.SE)
        self.labels[3].place(relx = 0, rely = 1, anchor = Tkinter.SW)

        self.message_label = Tkinter.Label(self.inner_frame, fg="white", bg="black")
        self.text_overlay()

        self.autoview_mode = True
        self.autoview_button = Tkinter.Button(self.inner_frame, text="Stop Autoview", command=self.toggle_autoview, bg="red", width=10, highlightthickness=0)
        self.autoview_button.pack(side = Tkinter.BOTTOM)

        self.auto_contrast_on = Tkinter.BooleanVar()
        self.auto_contrast_on.set(True)
        self.auto_contrast_box = Tkinter.Checkbutton(self.inner_frame, text="Auto Contrast", command=self.checkbox_toogled, variable=self.auto_contrast_on, selectcolor="gray", fg="white", activeforeground="white", activebackground="black",  width=10, bg="black", highlightthickness=0)
        self.auto_contrast_box.pack(side = Tkinter.BOTTOM)

        self.root.bind("<Up>", self.keyUp)
        self.root.bind("<Down>", self.keyDown)
        self.root.bind("<Button-4>", self.mouse_wheel)
        self.root.bind("<Button-5>", self.mouse_wheel)
        self.root.bind("<<Put>>", self.get_photo)
        self.root.bind("<space>", self.toggle_autoview)
        self.root.bind("<<shutdown>>", self.callback)
        self.root.bind("<B3-Motion>", self.mouse_press_and_move)
        self.root.bind("<Button-3>", self.mouse_pressed)
        self.root.bind("<<message>>", self.received_text)

        self.root.mainloop()

    def get_root(self):
        return self.root

