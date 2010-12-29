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

class VolumeScale():
    """ Volume scale/slider """

    def __init__(self, main_instance):
        """ Constructor """
        self.main = main_instance
        self.screen, self.rectangle, self.orientation = self.main.get_geometry()
        self.win = None
        self.init_window()

    def init_window(self):
        """ Initialize scale window """
        if self.win:
            self.win.unrealize()

        self.win = gtk.Window(type=gtk.WINDOW_POPUP)
        self.win.resize(1, 1)
        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_OUT)

        self.init_slider()

        self.align.add(self.slider)
        frame.add(self.align)
        self.win.add(frame)

        self.win.connect("button_press_event", self.on_window_button_press_event)
        self.win.connect("key_release_event", self.on_window_key_release_event)
        self.win.connect("scroll_event", self.on_window_scroll_event)
        self.win.connect_after("realize", self.on_realize)

    def init_slider(self):
        """ Initialize volume scale """
        if self.orientation == gtk.ORIENTATION_VERTICAL:
            self.slider = gtk.HScale()
        else:
            self.slider = gtk.VScale()

        self.align = gtk.Alignment()

        self.slider.set_update_policy(gtk.UPDATE_CONTINUOUS)
        self.slider.set_draw_value(self.main.scale_show_value)
        self.slider.set_digits(0)
        self.slider.set_range(0, 100)
        self.slider.set_increments(self.main.scale_increment, 10)
        self.slider.add_events(gtk.gdk.SCROLL_MASK)

        if isinstance(self.slider, gtk.VScale):
            self.align.set_padding(10, 10, 4, 4)
            self.slider.set_size_request(-1, 128)
            self.slider.set_value_pos(gtk.POS_BOTTOM)
            self.slider.set_inverted(True)
        else:
            self.align.set_padding(4, 4, 10, 10)
            self.slider.set_size_request(128, -1)
            self.slider.set_value_pos(gtk.POS_LEFT)

        self.slider.connect("value_changed", self.main.on_volume_changed)
        self.slider.connect("button_press_event", self.on_scale_button_press_event)
        self.slider.connect("button_release_event", self.on_scale_button_release_event)
        self.slider.connect("scroll_event", self.on_scale_scroll_event)

    def on_scale_button_press_event(self, widget, event):
        """ Callback for button_press_event. We want the behaviour you get with the middle button """
        if event.button == 1:
            event.button = 2
        return False

    def on_scale_button_release_event(self, widget, event):
        """ Callback for button_release_event. We want the behaviour you get with the middle button """
        if event.button == 1:
            event.button = 2
        return False

    def on_scale_scroll_event(self, widget, event):
        """ Callback for scroll_event. Forwards event to statusicon """
        self.main.on_scroll_event(widget, event)
        return True

    def on_window_button_press_event(self, widget, event):
        """ Callback for button_press_event. If clicked somewhere else release window """
        if event.type == gtk.gdk.BUTTON_PRESS:
            self.release_grab()
            return True
        return False

    def on_window_key_release_event(self, widget, event):
        """ Callback for key_release_event. On escape key release window """
        if event.keyval == gtk.gdk.keyval_from_name("Escape"):
            self.release_grab()
            return True
        return True

    def on_window_scroll_event(self, widget, event):
        """ Callback for scroll_event. Forwards event to statusicon """
        self.main.on_scroll_event(widget, event)
        return True

    def on_realize(self, widget):
        """ Callback for realize. Move window when realized """
        self.move_window()

    def toggle_window(self):
        """ Toggle scale window visibility """
        if self.win.get_property("visible"):
            self.release_grab()
        else:
            screen, rectangle, orientation = self.main.get_geometry()
            if orientation != self.orientation:
                self.orientation = orientation
                self.init_window()
                self.main.scale = self
                self.main.update()
            if rectangle.x != self.rectangle.x or rectangle.y != self.rectangle.y:
                self.rectangle = rectangle
                self.win.unrealize()
            self.win.show_all()
            self.grab_window()

    def move_window(self):
        """ Move scale window """
        posx, posy = self.get_position()
        self.win.move(posx, posy)

    def grab_window(self):
        """ Grab and focus window """
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
        """ Release grab from window """
        display = self.win.get_display()
        display.keyboard_ungrab()
        display.pointer_ungrab()
        self.win.grab_remove()
        self.win.hide()

    def get_position(self):
        """ Get coordinates to place scale window """
        screen, rectangle, orientation = self.main.get_geometry()
        self.win.set_screen(screen)
        monitor_num = screen.get_monitor_at_point(rectangle.x, rectangle.y)
        monitor = screen.get_monitor_geometry(monitor_num)
        window = self.win.allocation

        if orientation == gtk.ORIENTATION_VERTICAL:
            if monitor.width - rectangle.x == rectangle.width:
                # right panel
                posx = monitor.x + monitor.width - window.width - rectangle.width
            else:
                # left panel
                posx = rectangle.x + rectangle.width
            posy = rectangle.y
        else:
            if (rectangle.y + rectangle.height + window.height <= monitor.y + monitor.height):
                posy = rectangle.y + rectangle.height
            else:
                posy = rectangle.y - window.height

            if (rectangle.x + window.width <= monitor.x + monitor.width):
                posx = rectangle.x
            else:
                posx = monitor.x + monitor.width - window.width

        return posx, posy
