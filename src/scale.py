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

import gtk
import gobject

class VolumeScale(gtk.VScale):

    def __init__(self, main_instance):
        gtk.VScale.__init__(self)
        self.main = main_instance

        self.lock = False
        self.lockid = None

        self.set_update_policy(gtk.UPDATE_CONTINUOUS)
        self.set_draw_value(self.main.scale_show_value)
        self.set_value_pos(gtk.POS_BOTTOM)
        self.set_inverted(True)
        self.set_digits(0)
        self.set_range(0, 100)
        self.set_increments(self.main.scale_increment, 10)
        self.add_events(gtk.gdk.SCROLL_MASK)
        self.set_size_request(-1, 128)

        self.win = gtk.Window(type=gtk.WINDOW_POPUP)
        self.win.resize(1, 1)

        align = gtk.Alignment()
        align.set_padding(10, 10, 4, 4)

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_OUT)

        align.add(self)
        frame.add(align)
        self.win.add(frame)

        self.posx, self.posy = None, None
        self.screen, self.rectangle, self.orientation = self.main.get_geometry()

        self.connect("value_changed", self.on_scale_value_changed)
        self.connect("button_press_event", self.on_scale_button_press_event)
        self.connect("button_release_event", self.on_scale_button_release_event)
        self.connect("scroll_event", self.on_scale_scroll_event)
        self.win.connect("button_press_event", self.on_window_button_press_event)
        self.win.connect("key_release_event", self.on_window_key_release_event)
        self.win.connect("scroll_event", self.on_window_scroll_event)
        self.win.connect_after("realize", self.on_realize)

    def on_scale_value_changed(self, widget=None, data=None):
        if self.lock:
            return

        if self.lockid:
            gobject.source_remove(self.lockid)
            self.lockid = None

        self.lock = True
        volume = int(self.get_value())
        self.main.alsactrl.set_volume(volume)
        vol = _("Muted") if self.main.alsactrl.is_muted() else volume

        self.main.update_icon(vol)
        if self.main.show_tooltip:
            self.main.update_tooltip(vol)

        if self.main.keys:
            if self.main.key_press:
                if self.main.show_notify and self.main.notify:
                    self.main.update_notify(vol)

        self.lockid = gobject.timeout_add(10, self._unlock)

    def _unlock(self):
        self.lock = False
        self.lockid = None
        self.main.key_press = False
        return False

    def on_scale_button_press_event(self, widget, event):
        # we want the behaviour you get with the middle button
        if event.button == 1:
            event.button = 2
        return False

    def on_scale_button_release_event(self, widget, event):
        # we want the behaviour you get with the middle button
        if event.button == 1:
            event.button = 2
        return False

    def on_scale_scroll_event(self, widget, event):
        # forward event to the statusicon
        self.main.on_scroll_event(widget, event)
        return True

    def on_window_button_press_event(self, widget, event):
        # if clicked somewhere else release window
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.release_grab()
            return True
        return False

    def on_window_key_release_event(self, widget, event):
        # on escape key release window
        if event.keyval == gtk.gdk.keyval_from_name("Escape"):
            self.release_grab()
            return True
        return True

    def on_window_scroll_event(self, widget, event):
        # forward event to the statusicon
        self.main.on_scroll_event(widget, event)
        return True

    def on_realize(self, widget):
        # move window when realized
        self.move_window()

    def toggle_window(self):
        if self.win.get_property("visible"):
            self.release_grab()
        else:
            self.win.show_all()
            self.move_window()
            self.grab_window()

    def move_window(self):
        screen, rectangle, orientation = self.main.get_geometry()
        if self.posx and rectangle.x == self.rectangle.x and rectangle.y == self.rectangle.y:
            self.win.move(self.posx, self.posy)
        else:
            posx, posy = self.get_position()
            self.win.move(posx, posy)
            # save window position
            self.rectangle = rectangle
            self.posx, self.posy = posx, posy

    def grab_window(self):
        self.win.grab_add()
        gtk.gdk.pointer_grab(self.win.window, True,
            gtk.gdk.BUTTON_PRESS_MASK |
            gtk.gdk.BUTTON_RELEASE_MASK |
            gtk.gdk.POINTER_MOTION_MASK |
            gtk.gdk.SCROLL_MASK)

        if gtk.gdk.pointer_is_grabbed():
            if gtk.gdk.keyboard_grab(self.win.window, True) != gtk.gdk.GRAB_SUCCESS:
                self.release_grab()
                return False
        else:
            self.win.grab_remove()
            self.win.hide()
            return False

        self.win.grab_focus()
        return True

    def release_grab(self):
        display = self.win.get_display()
        display.keyboard_ungrab()
        display.pointer_ungrab()
        self.win.grab_remove()
        self.win.hide()

    def get_position(self):
        screen, rectangle, orientation = self.main.get_geometry()
        self.win.set_screen(screen)
        monitor_num = screen.get_monitor_at_point(rectangle.x, rectangle.y)
        monitor = screen.get_monitor_geometry(monitor_num)
        window = self.win.allocation

        if (rectangle.y + rectangle.height + window.height <= monitor.y + monitor.height):
            posy = rectangle.y + rectangle.height
        else:
            posy = rectangle.y - window.height

        if (rectangle.x + window.width <= monitor.x + monitor.width):
            posx = rectangle.x
        else:
            posx = monitor.x + monitor.width - window.width

        return posx, posy
