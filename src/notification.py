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
    """ Desktop notifications """

    def __init__(self, main_instance):
        """ Constructor """
        self.main = main_instance
        bus = dbus.SessionBus()
        obj = bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
        self.notify = dbus.Interface(obj, 'org.freedesktop.Notifications')
        self.server_capable = self.check_capabilities()
        self.title = '' if self.server_capable else 'volume'
        self.last_id = dbus.UInt32()

    def __del__(self):
        self.close()

    def check_capabilities(self):
        info = self.notify.GetServerInformation()
        if info[0] == "notify-osd":
            return False
        return True

    def show(self, icon, message, duration, volume):
        """ Show the notification """
        body = self.format(message, volume)
        hints = {"urgency": dbus.Byte(0), "desktop-entry": dbus.String("volti")}
        if self.main.notify_position and self.server_capable:
            hints["x"], hints["y"] = self.get_position()
        self.last_id = self.notify.Notify('volume', self.last_id, icon, self.title, body, [], hints, duration * 1000)

    def close(self):
        """ Close the notification """
        if self.last_id:
            self.notify.CloseNotification(self.last_id)

    def get_position(self):
        """ Returns status icon center coordinates """
        screen, rectangle, orientation = self.main.get_geometry()
        posx = rectangle.x + rectangle.width/2
        posy = rectangle.y + rectangle.height/2
        return posx, posy

    def format(self, message, volume):
        """ Format notification body """
        var, card_name, mixer_name = self.main.get_status_info(volume)
        message = message.replace('{volume}', '%s%s' % (volume, var))
        message = message.replace('{card}', '%s: %s' % (_("Card"), card_name))
        message = message.replace('{mixer}', '%s: %s' % (_("Mixer"), mixer_name))
        return message
