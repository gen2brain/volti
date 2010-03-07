#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Milan Nikolic <gen2brain@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import gettext
from subprocess import Popen,PIPE
from signal import SIGTERM

try:
    import gtk
    import gobject
    assert gtk.pygtk_version >= (2, 16, 0)
except ImportError, AssertionError:
    sys.stderr.write("This program needs pygtk 2.16 or higher\nExiting\n")
    sys.exit(1)

try:
    import alsaaudio as alsa
except ImportError:
    sys.stderr.write("This program needs pyalsaaudio 0.6 or higher\nExiting\n")
    sys.exit(1)

try:
    from config import Config
    import preferences
    from alsactrl import AlsaControl
    from scale import VolumeScale
    from menu import PopupMenu
    from utils import which
except ImportError:
    sys.stderr.write("Can't import application modules\nExiting\n")
    sys.exit(1)

config = Config()
gettext.bindtextdomain(config.APP_NAME, config.LOCALE_DIR)
gettext.textdomain(config.APP_NAME)

import __builtin__
__builtin__._ = gettext.gettext

class VolumeTray(gtk.StatusIcon):

    def __init__(self):
        gtk.StatusIcon.__init__(self)

        self.config = config
        self.preferences = preferences.Preferences(self)

        self.toggle = preferences.prefs["toggle"]
        self.mixer = preferences.prefs["mixer"]
        self.show_tooltip = bool(int(preferences.prefs["show_tooltip"]))
        self.run_in_terminal = bool(int(preferences.prefs["run_in_terminal"]))
        self.scale_increment = float(preferences.prefs["scale_increment"])
        self.scale_show_value = bool(int(preferences.prefs["scale_show_value"]))
        self.keys = bool(int(preferences.prefs["keys"]))
        self.keys_backend = preferences.prefs["keys_backend"]
        self.show_notify = bool(int(preferences.prefs["show_notify"]))
        self.notify_timeout = float(preferences.prefs["notify_timeout"])
        self.notify_position = bool(int(preferences.prefs["notify_position"]))
        self.notify_body = preferences.prefs["notify_body"]

        self.alsactrl = AlsaControl(preferences.prefs)
        self.menu = PopupMenu(self)
        self.scale = VolumeScale(self)

        self.notify = None
        self.keys_events = None
        if self.keys:
            self.init_keys_events()
            self.init_notify()

        self.set_from_icon_name("audio-volume-high")

        self.connect("button_press_event", self.on_button_press_event)
        self.connect("scroll_event", self.on_scroll_event)
        self.connect("popup_menu", self.on_popup_menu)

        # set current volume
        self.update()

        # watch for changes
        fd, eventmask = self.alsactrl.get_descriptors()
        gobject.io_add_watch(fd, eventmask, self.update)

    def init_keys_events(self):
        if self.keys_events:
            if hasattr(self.keys_events, "stop"):
                self.keys_events.stop()
            del self.keys_events
            self.keys_events = None

        if not self.keys:
            return

        try:
            import dbus
            self.has_dbus = True
        except ImportError:
            self.has_dbus = False
        try:
            from Xlib import X
            self.has_xlib = True
        except ImportError:
            self.has_xlib = False

        self.key_press = False
        if self.keys_backend == "hal":
            if self.has_dbus:
                try:
                    from dbusevent import DbusEvent
                    self.keys_events = DbusEvent(self)
                except Exception, e:
                    sys.stderr.write("%s.%s: %s\n" % (__name__, sys._getframe().f_code.co_name, str(e)))
                    self.keys_events = None
            else:
                sys.stderr.write("Hal backend needs python-dbus module\n")
                self.keys_events = None
        elif self.keys_backend == "xlib":
            if self.has_xlib:
                try:
                    from xlibevent import XlibEvent
                    self.keys_events = XlibEvent(self)
                    self.keys_events.start()
                except Exception, e:
                    sys.stderr.write("%s.%s: %s\n" % (__name__, sys._getframe().f_code.co_name, str(e)))
                    self.keys_events = None
            else:
                sys.stderr.write("Xlib backend needs python-xlib 0.15rc1 or higher\n")
                self.keys_events = None

    def init_notify(self):
        if self.notify:
            self.notify.close()
            del self.notify
            self.notify = None

        if not self.keys:
            return

        if self.show_notify:
            if self.has_dbus:
                try:
                    from notification import Notification
                    self.notify = Notification(self)
                except Exception, e:
                    sys.stderr.write("%s.%s: %s\n" % (__name__, sys._getframe().f_code.co_name, str(e)))
                    self.notify = None
            else:
                sys.stderr.write("Desktop notifications needs python-dbus module\n")
                self.notify = None

    def on_button_press_event(self, widget, event, data=None):
        if event.button == 1:
            self.scale.toggle_window()
        elif event.button == 2:
            if self.toggle == "mute":
                self.change_volume("mute")
            elif self.toggle == "mixer":
                self.menu.toggle_mixer.set_active(not self.menu.toggle_mixer.get_active())

    def on_scroll_event(self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            self.change_volume("up")
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.change_volume("down")
        if self.keys:
            if self.show_notify and self.notify:
                self.notify.close()

    def on_popup_menu(self, status, button, time):
        self.menu.toggle_mixer.handler_block(self.menu.mixer_handler_id)
        self.menu.toggle_mixer.set_active(self.mixer_get_active())
        self.menu.toggle_mixer.handler_unblock(self.menu.mixer_handler_id)

        self.menu.toggle_mute.handler_block(self.menu.mute_handler_id)
        self.menu.toggle_mute.set_active(self.alsactrl.is_muted())
        self.menu.toggle_mute.handler_unblock(self.menu.mute_handler_id)

        self.menu.popup(None, None, gtk.status_icon_position_menu, button, time, self)

    def change_volume(self, event, key_press=False):
        self.key_press = key_press
        volume = self.scale.get_value()

        if event == "up":
            volume = min(100, volume + self.scale_increment)
        elif event == "down":
            volume = max(0, volume - self.scale_increment)

        if event == "mute":
            self.menu.toggle_mute.set_active(not self.menu.toggle_mute.get_active())
            if self.key_press and self.alsactrl.mute_switch:
                self.scale.emit("value_changed")
        else:
            self.menu.toggle_mute.set_active(False)
            self.scale.set_value(volume)

    def get_icon_name(self, volume):
        if volume == 0 or volume == _("Muted"):
            icon = "audio-volume-muted"
        elif volume <= 33:
            icon = "audio-volume-low"
        elif volume <= 66:
            icon = "audio-volume-medium"
        elif volume > 66:
            icon = "audio-volume-high"
        return icon

    def get_status_info(self, volume):
        var = "" if volume == _("Muted") else "%"
        card_name = self.alsactrl.get_card_name()
        mixer_name = self.alsactrl.get_mixer_name()
        return var, card_name, mixer_name

    def update_icon(self, volume):
        self.set_from_icon_name(self.get_icon_name(volume))

    def update_tooltip(self, volume):
        var, card_name, mixer_name = self.get_status_info(volume)
        tooltip = "<b>%s: %s%s </b>\n<small>%s: %s\n%s: %s</small>" % (
                _("Output"), volume, var, _("Card"), card_name, _("Mixer"), mixer_name)
        self.set_tooltip_markup(tooltip)

    def update_notify(self, volume):
        icon = self.get_icon_name(volume)
        self.notify.show(icon, self.notify_body, self.notify_timeout, volume)

    def update(self, source=None, condition=None):
        if self.scale.lock:
            return True
        try:
            self.alsactrl = AlsaControl(preferences.prefs)
            volume = self.alsactrl.get_volume()
            scale_value = self.scale.get_value()
            gtk.gdk.threads_enter()
            if volume != scale_value:
                self.scale.set_value(volume)
            else:
                self.scale.emit("value_changed")
            gtk.gdk.threads_leave()
            return True
        except Exception, e:
            sys.stderr.write("%s.%s: %s\n" % (__name__, sys._getframe().f_code.co_name, str(e)))
            return False

    def toggle_mixer(self, widget=None):
        try:
            pid = self.mixer_get_pid()
            if pid:
                os.kill(pid, SIGTERM)
            else:
                if self.run_in_terminal:
                    term = os.getenv("TERM")
                    term_full = which(term)
                    if term == "rxvt" and not term_full:
                        term = "urxvt"
                        term_full = which(term)
                    cmd = [term_full, "-e", self.mixer]
                else:
                    cmd = which(self.mixer)
                Popen(cmd, shell=False)
        except Exception, e:
            sys.stderr.write("%s.%s: %s\n" % (__name__, sys._getframe().f_code.co_name, str(e)))

    def mixer_get_pid(self):
        pid = Popen(["pidof", "-x", self.mixer], stdout=PIPE).communicate()[0]
        if pid:
            try:
                return int(pid)
            except ValueError:
                return None
        return None

    def mixer_get_active(self):
        if self.mixer_get_pid():
            return True
        return False

    def main(self):
        gobject.threads_init()
        try:
            gtk.main()
        except KeyboardInterrupt:
            pass

    def quit(self, widget=None):
        gtk.main_quit()

if __name__ == "__main__":
    v = VolumeTray()
    v.main()
