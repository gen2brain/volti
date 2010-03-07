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

class Config:

    def __init__(self):
        self.APP_NAME = "volti"
        self.APP_VERSION = "0.1.8"
        self.RES_DIR = None
        self.LOCALE_DIR = None

        for base in ["/usr/share", "/usr/local/share"]:
            if os.path.isdir(os.path.join(base, self.APP_NAME)):
                self.RES_DIR = os.path.join(base, self.APP_NAME)
                self.LOCALE_DIR = os.path.join(base, "locale")
                break

        if not self.RES_DIR:
            self.RES_DIR = "data"

        self.CONFIG_DIR = os.path.expanduser(os.path.join("~", ".config", self.APP_NAME))
        self.CONFIG_FILE = os.path.join(self.CONFIG_DIR, "config")
