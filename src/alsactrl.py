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

import alsaaudio as alsa

from debug import log

OLD_VOLUME = 0
MUTED = False

class AlsaControl():
    """ Interface to ALSA mixer API. """

    def __init__(self, card_index, control, main_instance):
        """ Constructor """
        try:
            self.main = main_instance
            self.card_index = card_index
            self.control = control
            self.channel = alsa.MIXER_CHANNEL_ALL
            self.mixerlist=[]
            self.open()
            self._check_version()
        except Exception, err:
            log.Warn("can't open %s control for card %s, trying to select first available mixer channel\n" % (
                self.control, self.get_card_name()))
            try:
                control = self.get_mixers(self.card_index)[0]
                self.main.control = control
                self.reopen(self.card_index, control)
                self._check_version()
            except Exception, err:
                log.Error("can't open first available control for card %s\nerror: %s" % (
                    self.get_card_name(), str(err)))

    def __del__(self):
        """ Destructor """
        self.close()

    def _check_version(self):
        """ Check pyalsaaudio version """
        try:
            assert hasattr(self.mixer, "polldescriptors")
        except AssertionError:
            log.Error("This program needs pyalsaaudio 0.6 or higher")

    def open(self):
        """ Open mixer """
        self.get_mixer_list()
        if self.mixerlist:
            self.mixer = self.mixerlist[0]
        else:
            raise Exception

    def close(self):
        """ Close mixer """
        for mixer in self.mixerlist:
            if hasattr(mixer, 'close'):
                mixer.close()
        self.mixer = None
        self.mixerlist = []

    def reopen(self, card_index, control):
        """ Reopen mixer """
        self.close()
        self.card_index = card_index
        self.control = control
        self.open()

    def get_mixer_list(self):
        """ Append to mixer list, mixers with equal names
        are grouped and controlled together. """
        mixerlist = []
        for mixer in alsa.mixers(self.card_index):
            try:
                if mixer not in mixerlist:
                    mixerlist.append(mixer)
                    seq = 0
                else:
                    seq += 1
                if self.control == mixer:
                    m = alsa.Mixer(control=mixer, cardindex=self.card_index, id=seq)
                    self.mixerlist.append(m)
            except alsa.ALSAAudioError, err:
                pass

    def get_descriptors(self):
        """ Returns file descriptors """
        try:
            if not hasattr(self, 'mixer'):
                return (None, None)
            return self.mixer.polldescriptors()[0]
        except Exception, err:
            log.Warn(str(err))
            return (None, None)

    def set_volume(self, volume):
        """ Set mixer volume """
        try:
            for mixer in self.mixerlist:
                mixer.setvolume(volume, self.channel)
            return True
        except alsa.ALSAAudioError, err:
            log.Warn(str(err))
            return False

    def get_volume(self):
        """ Get mixer volume """
        try:
            if not self.mixerlist:
                return 0
            return self.mixerlist[0].getvolume()[0]
        except alsa.ALSAAudioError, err:
            log.Warn(str(err))

    def set_mute(self, mute=0):
        """ Set mixer mute status """
        global OLD_VOLUME, MUTED
        try:
            for mixer in self.mixerlist:
                mixer.setmute(mute, self.channel)
        except alsa.ALSAAudioError:
            # mixer doesn't have mute switch
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
            if not hasattr(self, "mixer"):
                return True
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
            log.Warn(str(err))

    def get_mixer_name(self):
        """ Returns mixer name """
        try:
            if not self.mixerlist:
                return ''
            return self.mixerlist[0].mixer()
        except alsa.ALSAAudioError, err:
            log.Warn(str(err))

    def get_cards(self):
        """ Returns cards list """
        cards = []
        acards = alsa.cards()
        for index, card in enumerate(acards):
            try:
                self.get_mixers(index)[0]
            except IndexError:
                cards.append(None)
            else:
                cards.append(acards[index])
        return cards

    def get_mixers(self, card_index=0):
        """ Returns mixers list """
        mixers = []
        amixers = []
        try:
            amixers = alsa.mixers(card_index)
        except alsa.ALSAAudioError:
            pass
        for mixer in amixers:
            try:
                m = alsa.Mixer(control=mixer, cardindex=card_index)
                cap = m.volumecap()
                if 'Playback Volume' in cap or 'Joined Volume' in cap:
                    if mixer not in mixers:
                        mixers.append(mixer)
            except alsa.ALSAAudioError:
                pass
        return mixers
