This repository contains files and algorithms that I created over the time while working on little python projects. These contain but are not limited to:

Image_Viewer_GUI
---------------------
The interactive 2D Image Viewer is a small GUI which displays 16 bit Numpy arrays. After initiating an instance of the GUI class a spereate process is lunched to enable a fluent and uninterrupted user facing experienct, while simultaniously running heavy calculations in the main python file. The second process is every time in communication with the calling file over a queue. Images, text or commands can be pushed to the viewer.
The Viewer itself can be described as interactive. The user can scroll back in the images history, change contrast and brightness, and start and stop autoviewing.

Parallelization_in_Python
---------------------
Python is combination with packages like numpy or scipy is a very powerfull language. I use it very often to make calculations on large datasets. While doing so I developed my own parallisation class which tries to share the workload equally over all CPUs. While doing so it prints the current state of the calculation in percent. This small iPython Notebook should demonstrate my Python Parallelization Class.

FVTK_in_iPython
---------------------
FVTK is a 3D renderer for python. Like probably most other python programmers I work regulary with iPython Notebooks. Unfortunately iPython does not support inline display option for VTK. With the script, however, it does.

Hex2Float
---------------------
This script converts space seperated, hexadecimal arrays stored in a file into float decimal arrays and saves it into a file again.

motion_correction
---------------------
This Notebook takes two Diffusion weighted images as an input and alignes the second one to the first one. Additionally it also rotates the bvecs of the second image according to the performed rotation of the image itself.
