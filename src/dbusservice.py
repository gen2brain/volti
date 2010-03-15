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

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop

class DBusService(dbus.service.Object):
    """ DBus Service """

    def __init__(self, main_instance):
        """ Constructor """
        loop=DBusGMainLoop()
        self.main = main_instance
        session_bus = dbus.SessionBus(mainloop=loop)
        bus_name = dbus.service.BusName('com.google.code.Volti', bus=session_bus)
        dbus.service.Object.__init__(self, bus_name, '/com/google/code/Volti')

        obj = session_bus.get_object('com.google.code.Volti', '/com/google/code/Volti')
        iface = dbus.Interface(obj, 'com.google.code.Volti')
        iface.connect_to_signal("signal", self.signal_handler)

    @dbus.service.signal('com.google.code.Volti', signature='s')
    def signal(self, signal):
        """ DBus signal """
        return signal

    @dbus.service.method('com.google.code.Volti', in_signature='s', out_signature=None)
    def emit(self, signal):
        """ DBus method to emit signal """
        self.signal(signal)

    def signal_handler(self, signal):
        """ Handle dbus signals and pass them to main app """
        if signal == 'volume-up':
            self.main.change_volume('up', True)
        elif signal == 'volume-down':
            self.main.change_volume('down', True)
        elif signal == 'mute':
            self.main.change_volume('mute', True)
