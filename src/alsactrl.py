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
import alsaaudio as alsa

OLD_VOLUME = 0
MUTED = False

class AlsaControl():

    def __init__(self, prefs):
        """ Constructor """
        try:
            self.prefs = prefs
            self.muted = False
            self.mute_switch = True
            self.card_index = int(self.prefs["card_index"])
            self.control = self.prefs["control"]
            self.channel = alsa.MIXER_CHANNEL_ALL
            self.mixer = alsa.Mixer(control=self.control, cardindex=self.card_index)

            try:
                assert hasattr(self.mixer, "polldescriptors")
            except AssertionError:
                sys.stderr.write("This program needs pyalsaaudio 0.6 or higher\nExiting\n")
                sys.exit(1)

        except Exception, err:
            sys.stderr.write("%s.%s: can't open %s control for card %s\nerror: %s\n" % (
                __name__, sys._getframe().f_code.co_name, self.control, self.get_card_name(), str(err)))
            try:
                self.mixer = alsa.Mixer(control=self.get_mixers()[0], cardindex=self.card_index)
            except Exception, err:
                sys.stderr.write("%s.%s: can't open %s control for card %s\nerror: %s\nExiting\n" % (
                    __name__, sys._getframe().f_code.co_name, self.control, self.get_card_name(), str(err)))
                sys.exit(1)

    def get_descriptors(self):
        """ Returns file descriptors """
        try:
            return self.mixer.polldescriptors()[0]
        except Exception, err:
            sys.stderr.write("%s.%s: %s\n" % (
                __name__, sys._getframe().f_code.co_name, str(err)))
            return None

    def set_volume(self, volume):
        """ Set mixer volume """
        try:
            self.mixer.setvolume(volume, self.channel)
            return True
        except alsa.ALSAAudioError, err:
            sys.stderr.write("%s.%s: %s\n" % (
                __name__, sys._getframe().f_code.co_name, str(err)))
            return False

    def get_volume(self):
        """ Get mixer volume """
        try:
            return self.mixer.getvolume()[0]
        except alsa.ALSAAudioError, err:
            sys.stderr.write("%s.%s: %s\n" % (
                __name__, sys._getframe().f_code.co_name, str(err)))

    def set_mute(self, mute=0):
        """ Set mixer mute status """
        global OLD_VOLUME, MUTED
        try:
            self.mixer.setmute(mute, self.channel)
            self.mute_switch = True
        except alsa.ALSAAudioError:
            # element has no mute switch
            self.mute_switch = False
            if mute == 1:
                OLD_VOLUME = self.get_volume()
                self.set_volume(0)
                MUTED = True
            else:
                self.set_volume(OLD_VOLUME)
                MUTED = False

    def is_muted(self):
        """ Returns mixer mute status """
        global OLD_VOLUME, MUTED
        try:
            if self.mixer.getmute()[0] == 1:
                return True
        except alsa.ALSAAudioError:
            if MUTED:
                return True
        return False

    def get_card_name(self):
        """ Returns card name """
        try:
            return alsa.cards()[self.card_index]
        except IndexError, err:
            sys.stderr.write("%s.%s: %s\n" % (
                __name__, sys._getframe().f_code.co_name, str(err)))

    def get_mixer_name(self):
        """ Returns mixer name """
        try:
            return self.mixer.mixer()
        except alsa.ALSAAudioError, err:
            sys.stderr.write("%s.%s: %s\n" % (
                __name__, sys._getframe().f_code.co_name, str(err)))

    def get_cards(self):
        """ Returns cards list """
        cards = []
        acards = alsa.cards()
        for index in range(0, len(acards)):
            try:
                alsa.mixers(index)[0]
            except Exception, err:
                # card has no mixer control
                cards.append(None)
                sys.stderr.write("%s.%s: %s %s\n" % (
                    __name__, sys._getframe().f_code.co_name, type(err), str(err)))
            else:
                cards.append(acards[index])
        return cards

    def get_mixers(self):
        """ Returns mixers list """
        try:
            return alsa.mixers(self.card_index)
        except Exception, err:
            sys.stderr.write("%s.%s: %s\n" % (
                __name__, sys._getframe().f_code.co_name, str(err)))
