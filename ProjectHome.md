![http://lh5.ggpht.com/_POq2QHWhExk/TRvB_jQbiQI/AAAAAAAAATk/2KvcO9wrCa0/volti-640.png](http://lh5.ggpht.com/_POq2QHWhExk/TRvB_jQbiQI/AAAAAAAAATk/2KvcO9wrCa0/volti-640.png)

## Features ##

  * no pulseaudio, gstreamer, phonon etc. only alsa is needed

  * internal mixer application, but you can choose any mixer app you prefer

  * left click opens volume scale (slider)

  * scroll wheel on tray icon changes volume, increment in percents is configurable

  * you can configure middle click to toggle 'mute' or 'show mixer'

  * nice tooltip with card and volume info

  * support for multimedia keys on keyboard

  * support desktop notifications on keys events

  * control volti from command line or bind keys within your window manager

### Dependencies ###

  * pygtk 2.16.0 or later

  * pyalsaaudio 0.6 or later

  * dbus-python 0.80.0 or later

  * python-xlib 0.15rc1 or later (optional, used for keys events as an alternative to hal)

### Install ###

#### Manually ####
Run 'python setup.py install'.
You can also start application from source dir, just run ./volti.

#### Arch ####
volti is in [aur](http://aur.archlinux.org/packages.php?ID=33525)

#### Gentoo ####
volti is in [portage](http://packages.gentoo.org/package/media-sound/volti)

#### Slackware ####
GNOME SlackBuild has volti in [extra](http://mirrors.gnomeslackbuild.org/gsb/gsb-current_slackware-13.1/extra/volti/)

#### Debian/Ubuntu ####
deb package can be found at [downloads page](http://code.google.com/p/volti/downloads/list)

#### PCLinuxOS ####
volti is in the repos

### Screenshots ###

  * [Gallery](http://picasaweb.google.com/gen2brain/Volti#slideshow/5445983247350698802)

### Changes ###

v0.2.3 Dec 29, 2010:

  * select visible controls in mixer application
  * support for soundcards with split master channel such as M-Audio 2496, thanks to Marc Brevoort
  * fix issue with awesome window manager
  * bug fixes

v0.2.2 Sep 1, 2010:

  * internal mixer application
  * only show channels that have Playback Volume capability
  * about page in preferences

v0.2.1 May 30, 2010:

  * scale now behaves correctly on vertically oriented panel, thanks to Fomin Denis for the patch
  * added Russian translation
  * Debian/Ubuntu package, thanks again to Fomin Denis
  * fix notifications in Ubuntu, also disable some features if we are dealing with notify-osd
  * fix bug when "Run in terminal" option is used
  * minor bug fixes and optimizations

v0.2.0 April 15, 2010:

  * icon themes combobox, choose your favourite theme beside system default
  * minor fixes

v0.1.9 March 22, 2010:

  * added volti-remote script, you can control volti from command line or bind keys within your wm
  * dbus-python is no longer optional
  * use pgrep if distribution installs pidof in /sbin
  * minor fixes and cleanup

### License ###

Author: Milan Nikolic (gen2brain)

Volti is free/libre software released under the terms of the GNU GPL license,
see the `COPYING' file for details.