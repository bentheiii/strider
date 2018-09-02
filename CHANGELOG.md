#Strider
## 0.6.3- unreleased
### Added
* added --raise flag to raise exceptions in normally catching environments (currently, only special command execution)
* dev flag and warnings if strider is used in dev mode
### Changed
* The entire special command input has been reworked, now supports going back and arrows 
* in the INFO, quick tags now display as a list
* jumping to start and end now uses home and end
### Fixed
* User could click the image while entering special command input
* Special commands would crash if the arguments have a leading comma in full form
* Exceptions are now caught when executing special commands  
* Crash when zooming in too much
* Importing calibration wouldn't work

## 0.6.2- 28/08/18
### Added
* The t command also counts the tracks
* All the Key commands are now registered, making managing them easier
* The help message is now programmatically generated
* Jumping now reports time as well as frame jumped to
* Multiple arguments can now be used in short special command syntax 
### Removed
* The new_track special command must now be called with an id argument
### Fixed
* -t flag can properly take multiple paths
* parenthesis can now be entered in the input

## 0.6.1- 27/08/18
### Added
* Tracks can now have tags
* Quick Tags using the -t flag and the g keys
* --pointradius and --linewidth flags
* j and shift+j to jump to begining and end of a track
* This changelog ;)
* --force_flush flag to make transit on 4k videos easier
### Changed
* All keys are now absorbed by the cv2 window, never focus on the console.
* Tracks now displays more information about the tracks
* Enable all and disable all now expect tags to enable or disable (use space to select all)
* Track Jsons now have indentations
* Unless run with "all", --calibrate will skip all ascii-code keys
* Info is now run with i
* program is now run by running the module, not strider.py 
### Fixed
* Crash when going past video source end.
* Crash when deleting a point
* Crash when running from outside directory