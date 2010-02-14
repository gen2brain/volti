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

import dbus

class Notification:

    def __init__(self, MainInstance=None):
        self.main = MainInstance
        bus = dbus.SessionBus()
        obj = bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        self.notify = dbus.Interface(obj, 'org.freedesktop.Notifications')
        self.last_id = dbus.UInt32()

    def show(self, icon, subject, msg, duration):
        hints = {"urgency": dbus.Byte(0), "desktop-entry": dbus.String("volti")}
        self.last_id = self.notify.Notify('audiovolume', self.last_id, icon, subject, msg, [], hints, duration * 1000)

    def close(self):
        if self.last_id:
            self.notify.CloseNotification(self.last_id)
