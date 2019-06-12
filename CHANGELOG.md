# Strider Changelog
## 0.8.0- unreleased
### Changed
* in main: input the tracks file and video file arguments have been switched, this is to better accommodate embedding the video in the trackpack.
* The entire concept of tags has been overhauled, instead of a drop-down menu, now there's an autocomplete input, and quick tags are automatically added and removed by input.
* The help for commands now displays accurate values
### Added
* activate() now accepts int ids
* the trackpack file can now contain a default video source
* if a video or trackpack file is not provided in the arguments, a selection dialog will be issued using Tkinter
* added shift+g command to remove a tag
* special commands now have autocomplete
* `activate` special command can now receive now arguments and will activate the only enabled track, if available
### Fixed
* if a trackpack file does not exist, an empty one will be created
* can no longer jump to negative times
### Removed
* `--force_flush`: the value is now automatically calculated on whether we're using a 4k source

## 0.7.1- 2018-11-12
### Added
* tracks details now also list distance in pixels
* merge_tracks: added the -ir argument for inline rules
* merge_tracks: action(None) now results in an action that does nothing (useful for default rules)
* merge_tracks: default rule that accepts all and does nothing
* merge_tracks: members in rule files annotated with __rule do not undergo conversion to a rule
* merge_tracks: members in rule files annotated with rules or __rules are added as iterables of rules
* merge_tracks: both actions and triggers now accept the track, source pack, and destination pack.
### Changed
* merge_tracks: rule notifications now display the track's original id, as well as well as the output
* Better handling of trackpack's source

## 0.7.0- 2018-09-19 
### Added
* Links to required packages in README
* Clarification about tag arguments in README 
* Seek_time can now be entered with short syntax
* Load args from file with prefix @
* Added the merge_tracks module
* Trackpacks now remember their source file if one is provided
### Changed
* Date formats in the changelog to conform to ISO standard
* Time displayed is now pretty (well, prettier)
### Removed
* Manifest.in, turns out it's useless
* Check for positive arguments. If users want to enter negative arguments, it's their funeral.
### Fixed
* Typos and minor edits in README
* Support for commands with multi-line descriptions
* Deprecated arguments showed up in help

## 0.6.4- 2018-09-04
### Added
* Official copyright notice
* README
* -qt argument to add quick tags in the arguments
* press tab to enable auto-play
* right-arrow to jump forward by 1 sec
* all deprecated arguments are now listed
* info now also displays the view rectangle, and the zoom level
* remove_tag special command
* auto_play_wait argument
* during calibration, pressing esc wil quit the calibration
* the strider version is now saved to the json file
### Changed
* quick tags are now sorted and the keys are deterministic
* q and shift+q used without quick tags now automatically target all tracks
* --step has been changed to --frame_step
* --back_step has been changed to --seek_step, to accommodate forward steps
* right arrow no longer advanced by 1 frame, now advanced by 1 sec
* all tags are converted to lowercase, tags are to be considered case-insensitive from this point
* the tracks listed when using t are now sorted, first by active, then by enabled, then by id
### Fixed
* crash when q and shift+q was used without any quick tags.

## 0.6.3- 2018-09-02
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

## 0.6.2- 2018-08-28
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

## 0.6.1- 2018-08-27
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
