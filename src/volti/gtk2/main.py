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
from subprocess import Popen, PIPE
from signal import SIGTERM

import gtk
import gobject
from dbus.exceptions import DBusException

try:
    from volti.config import Config
    from volti.alsactrl import AlsaControl
    from volti.dbusservice import DBusService
    from volti.utils import log, which, find_term, get_pid_app
    from volti.gtk2.scale import VolumeScale
    from volti.gtk2.menu import PopupMenu
    from volti.gtk2.preferences import Preferences, PREFS
except ImportError:
    sys.stderr.write("Can't import application modules\nExiting\n")
    sys.exit(1)

try:
    from Xlib import X
    HAS_XLIB = True
except ImportError:
    HAS_XLIB = False

CONFIG = Config()
gettext.bindtextdomain(CONFIG.app_name, CONFIG.locale_dir)
gettext.textdomain(CONFIG.app_name)

import __builtin__
__builtin__._ = gettext.gettext

class VolumeTray(gtk.StatusIcon):
    """ GTK+ application for controlling audio volume
    from system tray/notification area """

    def __init__(self):
        """ Constructor """
        gtk.StatusIcon.__init__(self)

        self.config = CONFIG
        self.preferences = Preferences(self)

        self.card_index = int(PREFS["card_index"])
        self.control = PREFS["control"]
        self.toggle = PREFS["toggle"]
        self.mixer = PREFS["mixer"]
        self.mixer_internal = bool(int(PREFS["mixer_internal"]))
        self.icon_theme = PREFS["icon_theme"]
        self.show_tooltip = bool(int(PREFS["show_tooltip"]))
        self.run_in_terminal = bool(int(PREFS["run_in_terminal"]))
        self.scale_increment = float(PREFS["scale_increment"])
        self.scale_show_value = bool(int(PREFS["scale_show_value"]))
        self.keys = bool(int(PREFS["keys"]))
        self.show_notify = bool(int(PREFS["show_notify"]))
        self.notify_timeout = float(PREFS["notify_timeout"])
        self.notify_position = bool(int(PREFS["notify_position"]))
        self.notify_body = PREFS["notify_body"]

        self.lock = False
        self.lockid = None
        self.notify = None
        self.key_press = False
        self.keys_events = None
        self.pid_app = get_pid_app()

        self.alsactrl = AlsaControl(self.card_index, self.control, self)
        self.menu = PopupMenu(self)
        self.scale = VolumeScale(self)
        self.dbus = DBusService(self)

        if self.keys:
            self.init_keys_events()
        if self.show_notify:
            self.init_notify()

        self.connect("button_press_event", self.on_button_press_event)
        self.connect("scroll_event", self.on_scroll_event)
        self.connect("popup_menu", self.on_popup_menu)

        # set current volume
        self.update(reopen=False)

        # watch for changes
        fd, eventmask = self.alsactrl.get_descriptors()
        self.watchid = gobject.io_add_watch(fd, eventmask, self.update)

    def init_keys_events(self):
        """ Initialize keys events """
        if self.keys_events:
            if hasattr(self.keys_events, "stop"):
                self.keys_events.stop()
            del self.keys_events
            self.keys_events = None

        if not self.keys:
            return

        if HAS_XLIB:
            try:
                from volti.xlibevent import XlibEvent
                self.keys_events = XlibEvent(self)
                self.keys_events.start()
            except Exception, err:
                log.exception(str(err))
                self.keys_events = None
        else:
            log.warn("Xlib backend needs python-xlib 0.15rc1 or higher\n")
            self.keys_events = None

    def init_notify(self):
        """ Initialize desktop notifications """
        if self.notify:
            self.notify.close()
            del self.notify
            self.notify = None

        if self.show_notify:
            try:
                from notification import Notification
                self.notify = Notification(self)
            except Exception, err:
                log.exception(str(err))
                self.notify = None

    def on_volume_changed(self, widget=None, data=None):
        """ Callback for scale value_changed signal """
        if self.lock:
            return

        if self.lockid:
            gobject.source_remove(self.lockid)
            self.lockid = None

        self.lock = True
        volume = int(self.scale.slider.get_value())
        self.alsactrl.set_volume(volume)
        vol = self.get_volume()

        icon = self.get_icon_name(vol)
        self.update_icon(vol, icon)
        if self.show_tooltip:
            self.update_tooltip(vol)

        if self.key_press:
            if self.show_notify and self.notify:
                self.update_notify(vol, icon)

        self.lockid = gobject.timeout_add(10, self._unlock)

    def _unlock(self):
        """ Unlock scale """
        self.lock = False
        self.lockid = None
        self.key_press = False
        return False

    def on_button_press_event(self, widget, event, data=None):
        """ Callback for button_press_event """
        if event.button == 1:
            self.scale.toggle_window()
        elif event.button == 2:
            if self.toggle == "mute":
                self.change_volume("mute")
            elif self.toggle == "mixer":
                self.menu.toggle_mixer.set_active(
                        not self.menu.toggle_mixer.get_active())

    def on_scroll_event(self, widget, event):
        """ Callback for scroll_event """
        if event.direction == gtk.gdk.SCROLL_UP:
            self.change_volume("up")
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.change_volume("down")
        if self.show_notify and self.notify:
            self.notify.close()

    def on_popup_menu(self, status, button, time):
        """ Show popup menu """
        self.menu.toggle_mixer.handler_block(self.menu.mixer_handler_id)
        self.menu.toggle_mixer.set_active(self.mixer_get_active())
        self.menu.toggle_mixer.handler_unblock(self.menu.mixer_handler_id)

        self.menu.toggle_mute.handler_block(self.menu.mute_handler_id)
        self.menu.toggle_mute.set_active(self.alsactrl.is_muted())
        self.menu.toggle_mute.handler_unblock(self.menu.mute_handler_id)

        self.menu.popup(None, None, gtk.status_icon_position_menu, button, time, self)

    def change_volume(self, event, key_press=False):
        """ Change volume """
        self.key_press = key_press
        volume = self.scale.slider.get_value()

        if event == "up":
            volume = min(100, volume + self.scale_increment)
        elif event == "down":
            volume = max(0, volume - self.scale_increment)

        if event == "mute":
            self.menu.toggle_mute.set_active(
                    not self.menu.toggle_mute.get_active())
        else:
            self.menu.toggle_mute.set_active(False)
            self.set_volume(volume)

    def get_icon_name(self, volume):
        """ Returns icon name for current volume """
        if volume == 0 or volume == _("Muted"):
            icon = "audio-volume-muted"
        elif volume <= 33:
            icon = "audio-volume-low"
        elif volume <= 66:
            icon = "audio-volume-medium"
        elif volume > 66:
            icon = "audio-volume-high"
        return icon

    def get_icon_themes(self):
        themes = ["Default"]
        icons_dir = os.path.join(CONFIG.res_dir, "icons")
        try:
            for file in os.listdir(icons_dir):
                if os.path.isdir(os.path.join(icons_dir, file)):
                    if not file.startswith("."):
                        themes.append(file)
        except OSError:
            pass
        return themes

    def get_status_info(self, volume):
        """ Returns status information """
        var = "" if volume == _("Muted") else "%"
        card_name = self.alsactrl.get_card_name()
        mixer_name = self.alsactrl.get_mixer_name()
        return var, card_name, mixer_name

    def set_volume(self, volume):
        """ Set volume """
        if volume != self.scale.slider.get_value():
            self.scale.slider.set_value(volume)
        else:
            self.scale.slider.emit("value_changed")

    def get_volume(self):
        """ Get volume """
        if self.alsactrl.is_muted():
            return _("Muted")
        else:
            return self.alsactrl.get_volume()

    def update_icon(self, volume, icon):
        """ Update icon """
        if self.icon_theme != "Default":
            icon = os.path.abspath(os.path.join(
                    CONFIG.res_dir, "icons", self.icon_theme, "32x32", icon+".png"))
            self.set_from_file(icon)
        else:
            self.set_from_icon_name(icon)

    def update_tooltip(self, volume):
        """ Update tooltip """
        var, card_name, mixer_name = self.get_status_info(volume)
        tooltip = "<b>%s: %s%s </b>\n<small>%s: %s\n%s: %s</small>" % (
                _("Output"), volume, var, _("Card"), card_name, _("Mixer"), mixer_name)
        self.set_tooltip_markup(tooltip)

    def update_notify(self, volume, icon):
        """ Update notification """
        if self.icon_theme != "Default":
            icon = os.path.abspath(os.path.join(
                    CONFIG.res_dir, "icons", self.icon_theme, "48x48", icon+".png"))
        try:
            self.notify.show(icon, self.notify_body, self.notify_timeout, volume)
        except DBusException:
            del self.notify
            self.notify = None
            self.init_notify()
            self.notify.show(icon, self.notify_body, self.notify_timeout, volume)

    def update(self, source=None, condition=None, reopen=True):
        """ Update volume """
        if self.lock:
            return True
        try:
            if reopen:
                self.alsactrl.reopen(self.card_index, self.control)
            volume = self.alsactrl.get_volume()
            gtk.gdk.threads_enter()
            self.set_volume(volume)
            gtk.gdk.threads_leave()
            return True
        except Exception, err:
            log.exception(str(err))
            return False

    def toggle_mute(self, widget=None):
        """ Toggle mute status """
        self.alsactrl.set_mute(widget.get_active())
        volume = self.get_volume()
        icon = self.get_icon_name(volume)
        self.update_icon(volume, icon)
        if self.show_tooltip:
            self.update_tooltip(volume)

    def toggle_mixer(self, widget=None):
        """ Toggle mixer application """
        mixer = "volti-mixer" if self.mixer_internal else self.mixer
        if not mixer:
            return
        try:
            pid = self.mixer_get_pid()
            if pid:
                os.kill(pid, SIGTERM)
            else:
                if self.run_in_terminal and not self.mixer_internal:
                    term = find_term()
                    cmd = [term, "-e", mixer]
                else:
                    cmd = which(mixer)
                Popen(cmd, shell=False)
        except Exception, err:
            log.debug(cmd)
            log.exception(str(err))

    def mixer_get_pid(self):
        """ Get process id of mixer application """
        mixer = "volti-mixer" if self.mixer_internal else self.mixer
        pid = Popen(self.pid_app + " " + os.path.basename(mixer),
                stdout=PIPE, shell=True).communicate()[0]
        if pid:
            try:
                return int(pid)
            except ValueError:
                return None
        return None

    def mixer_get_active(self):
        """ Returns status of mixer application """
        if self.mixer_get_pid():
            return True
        return False

    def main(self):
        """ Main loop """
        gobject.threads_init()
        try:
            gtk.main()
        except KeyboardInterrupt:
            pass

    def quit(self, widget=None):
        """ Quit main loop """
        gtk.main_quit()
