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
        """ Constructor """
        self.app_name = "volti"
        self.app_version = "0.2.0"
        self.res_dir = None
        self.locale_dir = None

        for base in ["/usr/share", "/usr/local/share"]:
            if os.path.isdir(os.path.join(base, self.app_name)):
                self.res_dir = os.path.join(base, self.app_name)
                self.locale_dir = os.path.join(base, "locale")
                break

        if not self.res_dir:
            self.res_dir = "data"

        self.config_dir = os.path.expanduser(os.path.join("~", ".config", self.app_name))
        self.config_file = os.path.join(self.config_dir, "config")
