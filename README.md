# Strider
(c) 2018 Ben Avrahami
## About
Strider is a pure-python program and module to view and manually track objects along a video. Strider processes video using the OpenCV library
## Installation
* Strider requires a python distribution of at least version 3.6
* Strider requires both sortedContainers and openCV be installed in the python environment
* install the Strider module
    * If you have the setup.py file, run ```python setup.py install```
    * If you have access to the ```.whl``` file, run ```python -m pip install <.whl> file```
* check that everything works with ```python -m strider --version```
## Running
* Strider is a runnable module and can be run with ```python -m strider```
* Strider takes 2 main arguments
    1. video source: A video file to be opened and run
    2. track file: A json file to load and store the tracks. This file need not exist at first 
* run ```strider --help``` to see all arguments
### Tracks
* Each track has a unique string id that identifies it.
* A track can be in three states:
    1. Disabled: The track is not shown on the screen, it still exists and is saved as normal.
    2. Enabled: The track is shown on the screen.
    3. Active: The track is shown on the screen, and is also the track to be edited when editing occurs. There need not be an active track, but there can only be one active track at a time.
### Tags
* Tracks can have tags that make categorizing them easier.
* Each track can have any subset of tags.
* Tags are simply strings and can be of any form, although all tags are converted to lowercase.
    * It is highly recommended that tags have at least one english letter.
* Aside from this, a program can have quick tags. These are tags that can be quickly applied and filtered.
    * Quick tags can be added as an argument with the flag ```-qt bee fly butterfly```
    * Quick tags can also be loaded from a file ```-t tags.txt``` Where tags.txt can be:
        ```text
        fly
        bee
        bumble bee
        ```
### Using
* The program produces two windows, one displaying the video and the tracks, the other (the standard output stream/ console) providing text feedback.
* Pressing ```h``` at any point displays all the commands and keys available.
* Common actions:
    * left click: add a point to the clicked location, at the current frame, to the active track.
    * right click: print data of th the point(s) clicked.
    * space: advance to the next frame of the video.
    * n: create a new track with a random id and color and activate it.
    * g: add a tag, from the quick tags, to the active track.
    * u: delete the most recent point from the active track. Only deletes the last VISIBLE point form the active track.
    * z: zoom in on the video.
    * shift+z: zoom out on the video.
    * w/a/s/d (when zoomed in): move the view window
    * right/left arrow: advance 1/2 a second forward/ backwards
    * p: save the tracks to file
    * esc: exit
    * c: start a special command. Type into the display window a command and hit enter.
        * commands can be entered via C call syntax, for example: ```activate("0")``` will activate the track with id 0.
        * commands can also be entered via short syntax, for example ```tag butterfly 12``` is equivelant to ```tag("butterfly","12")``` and will apply tag "butterfly" to track with id 12.
### Saving and Exiting
* due to openCV limitations, closing the display window will cause the program to hang. Press esc to exit the program normally.
* By design, the program does not auto-save. You must remember to press p to save the tracks.         

## Output File
The Output file (the track file given in the arguments) is meant to be easy to read for programs to analyse the tracks. It is a json dict with following structure:
* "tracks": a list of tracks, each track is a dict:
    * "id": the unique name of the track (string)
    * "color": the color to display in the OpenCV window (list of 3 ints in GRB format)
    * "tags": a list of tags associated to the track
    * "point": a list of points of the track, each point is a list:
        * \[0]: the index of the frame where the point appeared
        * \[1]: a list representing the x,y coordinates of the point in pixels 