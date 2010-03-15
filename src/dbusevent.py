# -*- coding: utf-8 -*-

# Author: Jon Nettleton <jon.nettleton@gmail.com>
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

import dbus
from dbus.mainloop.glib import DBusGMainLoop

class DBusEvent:
    """ Handle multimedia keys via dbus/hal """

    def __init__(self, main_instance):
        """ Constructor """
        loop = DBusGMainLoop()
        self.main = main_instance
        bus = dbus.SystemBus(mainloop=loop)
        for udi in self.get_inputs():
            obj = bus.get_object('org.freedesktop.Hal', udi)
            iface = dbus.Interface(obj, 'org.freedesktop.Hal.Device')
            iface.connect_to_signal("Condition", self.button_handler, path_keyword="path")

    def hal_manager(self):
        """ Hal manager """
        bus = dbus.SystemBus()
        obj = bus.get_object('org.freedesktop.Hal', '/org/freedesktop/Hal/Manager')
        return dbus.Interface(obj, 'org.freedesktop.Hal.Manager')

    def get_inputs(self):
        """ Get keys """
        return self.hal_manager().FindDeviceByCapability("input.keys")

    def button_handler(self, sender, destination, path):
        """ Handle button events and pass them to main app """
        if sender == 'ButtonPressed':
            if destination == 'volume-up':
                self.main.change_volume('up', True)
            elif destination == 'volume-down':
                self.main.change_volume('down', True)
            elif destination.startswith('mute'):
                self.main.change_volume('mute', True)
