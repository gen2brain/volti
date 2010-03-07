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

    def show(self, icon, message, duration, volume):
        body = self.format(message, volume)
        hints = {"urgency": dbus.Byte(0), "desktop-entry": dbus.String("volti")}
        if self.main.notify_position:
            hints["x"], hints["y"] = self.get_position()
        self.last_id = self.notify.Notify('audiovolume', self.last_id, icon, '', body, [], hints, duration * 1000)

    def close(self):
        if self.last_id:
            self.notify.CloseNotification(self.last_id)

    def get_position(self):
        screen,rectangle,orientation = self.main.get_geometry()
        x = rectangle.x + rectangle.width/2
        y = rectangle.y + rectangle.height/2
        return x, y

    def format(self, message, volume):
        var, card_name, mixer_name = self.main.get_status_info(volume)
        message = message.replace('{volume}', '%s%s' % (volume, var))
        message = message.replace('{card}', '%s: %s' % (_("Card"), card_name))
        message = message.replace('{mixer}', '%s: %s' % (_("Mixer"), mixer_name))
        return message
