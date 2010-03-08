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

import sys
import threading

import gtk
import gobject
from Xlib.display import Display
from Xlib import X, XK


class XlibEvent(gobject.GObject, threading.Thread):
    """ Handle multimedia keys via Xlib """

    __gsignals__ = {
            'volume-up': (gobject.SIGNAL_RUN_FIRST, None, ()),
            'volume-down': (gobject.SIGNAL_RUN_FIRST, None, ()),
            'mute': (gobject.SIGNAL_RUN_FIRST, None, ())
        }

    def __init__(self, main_instance):
        """ Constructor """
        gobject.GObject.__init__(self)
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.running = False
        self.main = main_instance

        try:
            XK.load_keysym_group("xf86")
        except ImportError, err:
            sys.stderr.write("Xlib backend needs python-xlib 0.15rc1 or higher\n")
            raise ImportError(str(err))

        self.display = Display()
        self.screen = self.display.screen()
        self.root = self.screen.root
        self.root.change_attributes(event_mask = X.KeyPressMask)

        self.up_keys = self.get_keycodes(self.display.keysym_to_keycodes(XK.XK_XF86_AudioRaiseVolume))
        self.down_keys = self.get_keycodes(self.display.keysym_to_keycodes(XK.XK_XF86_AudioLowerVolume))
        self.mute_keys = self.get_keycodes(self.display.keysym_to_keycodes(XK.XK_XF86_AudioMute))
        self.keycodes = [self.up_keys, self.down_keys, self.mute_keys]

        self.grab()

        self.connect("volume-up", self.button_handler, "volume-up")
        self.connect("volume-down", self.button_handler, "volume-down")
        self.connect("mute", self.button_handler, "mute")

    def get_keycodes(self, keys):
        """ Returns keycodes without modifiers """
        keycodes = []
        for keycode, index in keys:
            if keycode not in keycodes:
                keycodes.append(keycode)
        return keycodes

    def grab(self):
        """ Grab keys, will print error if some other app already have those keys grabbed """
        for keys in self.keycodes:
            for keycode in keys:
                self.root.grab_key(keycode, X.AnyModifier, True, X.GrabModeAsync, X.GrabModeAsync)

    def ungrab(self):
        """ Ungrab keys """
        for keys in self.keycodes:
            for keycode in keys:
                self.root.ungrab_key(keycode, X.AnyModifier, self.root)

    def button_handler(self, sender, event):
        """ Handle button events and pass them to main app """
        if event == 'volume-up':
            self.main.change_volume('up', True)
        elif event == 'volume-down':
            self.main.change_volume('down', True)
        elif event == 'mute':
            self.main.change_volume('mute', True)

    def signal(self, signal):
        """ Emit signal """
        gtk.gdk.threads_enter()
        self.emit(signal)
        gtk.gdk.threads_leave()
        return False

    def run(self):
        """ Start thread """
        self.running = True
        while self.running:
            event = self.display.next_event()
            if event.type == X.KeyPress:
                if event.detail in self.up_keys:
                    gobject.idle_add(self.signal, "volume-up")
                elif event.detail in self.down_keys:
                    gobject.idle_add(self.signal, "volume-down")
                elif event.detail in self.mute_keys:
                    gobject.idle_add(self.signal, "mute")

    def stop(self):
        """ Stop thread """
        self.running = False
        self.ungrab()
        self.display.close()
