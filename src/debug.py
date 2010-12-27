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
import sys
import traceback

class log:

    @staticmethod
    def _get_trace(msg, depth):
        exc_traceback = traceback.extract_stack()
        exc_traceback.reverse()
        (filename, linenumber, functionname, text) = exc_traceback[2 + depth]
        filename = os.path.basename(filename)
        return "[%s:%s:%s] %s\n" % (filename, functionname, linenumber, msg)

    @staticmethod
    def Notice(msg, depth = 0):
        sys.stdout.write(log._get_trace(msg, depth))

    @staticmethod
    def Warn(msg, depth = 0):
        sys.stderr.write(log._get_trace(msg, depth))

    @staticmethod
    def Error(msg, depth = 0, exit_code = 1):
        log.Warn(msg + "\nExiting", depth + 1)
        sys.exit(exit_code)
