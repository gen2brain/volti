# -*- coding: utf-8 -*-

import sys
from pyalsa import alsamixer, alsacard

from volti.utils import log

OLD_VOLUME = 0
MUTED = False

class PyAlsaControl():
    """ Interface to ALSA mixer API. """

    def __init__(self, card_index, control, main_instance):
        """ Constructor """
        try:
            self.main = main_instance
            self.card_index = card_index
            self.control = control
            self.mixerlist=[]

            self.mixer = alsamixer.Mixer()
            self.mixer.attach("hw:%d" % self.card_index)
            self.mixer.load()
            
            self.open()
            self._has_capture()
            self._check_version()

        except Exception, err:
            log.warn("can't open %s control for card %s, \
                    trying to select first available mixer channel\n" % (
                self.control, self.get_card_name()))
            try:
                control = self.get_mixers(self.card_index)[0]
                self.main.control = control
                self.reopen(self.card_index, control)
                self._has_capture()
                self._check_version()
            except Exception, err:
                log.error("can't open first available control \
                        for card %s\nerror: %s" % (
                    self.get_card_name(), str(err)))
                sys.exit(1)

    def _has_capture(self):
        if self.has_capture_channel():
            self.capture = True
        else:
            self.capture = False

    def _check_version(self):
        try:
            assert hasattr(self.mixer, "poll_fds")
        except AssertionError:
            log.error("This program needs pyalsa 1.0.23 or higher")
            sys.exit(1)

    def open(self):
        """ Open mixer """
        self.get_mixer_list()
        if self.mixerlist:
            self.element = self.mixerlist[0]
        else:
            raise Exception

    def close(self):
        """ Close mixer """
        self.element = None
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
        for mixer in self.mixer.list():
            try:
                if mixer[0] not in mixerlist:
                    mixerlist.append(mixer[0])
                    seq = 0
                else:
                    seq += 1
                if self.control == mixer[0]:
                    m = alsamixer.Element(mixer=self.mixer,
                            name=mixer[0], index=seq)
                    self.mixerlist.append(m)
            except Exception:
                pass

    def get_descriptors(self):
        """ Returns file descriptors """
        try:
            if not hasattr(self, 'mixer'):
                return (None, None)
            return self.mixer.poll_fds[0]
        except Exception, err:
            log.exception(str(err))
            return (None, None)

    def set_volume(self, volume):
        """ Set mixer volume """
        try:
            min, max = self.element.get_volume_range(self.capture)
            range = max - min
            vol = int(round(range * (volume * .01) + min))
            for mixer in self.mixerlist:
                mixer.set_volume_all(vol, self.capture)
            return True
        except Exception, err:
            log.exception(str(err))
            return False

    def get_volume(self):
        """ Get mixer volume """
        try:
            min, max = self.element.get_volume_range(self.capture)
            range = max - min
            vol = self.element.get_volume(0, self.capture)
            vol -= min
            volume = int(round(vol * 100/float(range)))
            return volume
        except Exception, err:
            log.exception(str(err))

    def has_playback_channel(self):
        try:
            if self.element.has_channel(0):
                return True
        except Exception, err:
            log.exception(str(err))
        return False

    def has_capture_channel(self):
        try:
            if self.element.has_channel(0, True):
                return True
        except Exception, err:
            log.exception(str(err))
        return False

    def set_mute(self, mute=0):
        """ Set mixer mute status """
        global OLD_VOLUME, MUTED
        try:
            for mixer in self.mixerlist:
                if mixer.has_switch(self.capture):
                    if mixer.has_channel(0, self.capture):
                        mixer.set_switch_all(not mute, self.capture)
            else:
                # mixer doesn't have mute switch
                if mute:
                    OLD_VOLUME = self.get_volume()
                    self.set_volume(0)
                    MUTED = True
                else:
                    self.set_volume(OLD_VOLUME)
                    MUTED = False
        except Exception, err:
            log.exception(str(err))

    def is_muted(self):
        """ Returns mixer mute status """
        global OLD_VOLUME, MUTED
        try:
            if self.element.has_switch(self.capture):
                if self.element.has_channel(0, self.capture):
                    return not self.element.get_switch(0, self.capture)
            else:
                if MUTED:
                    return True
        except Exception, err:
            log.exception(str(err))
        return False

    def get_card_name(self):
        """ Returns card name """
        try:
            return alsacard.card_get_name(self.card_index)
        except Exception, err:
            log.exception(str(err))

    def get_mixer_name(self):
        """ Returns mixer name """
        try:
            if not self.mixerlist:
                return ''
            return self.mixerlist[0].name
        except Exception, err:
            log.exception(str(err))

    def get_cards(self):
        """ Returns cards list """
        cards = []
        try:
            acards = alsacard.card_list()
            for card in acards:
                try:
                    self.get_mixers(card)[0]
                except IndexError:
                    cards.append(None)
                else:
                    cards.append(alsacard.card_get_name(card))
        except Exception, err:
            log.exception(str(err))
        return cards

    def get_mixers(self, card_index=0):
        """ Returns mixers list """
        mixers = []
        try:
            mixer = alsamixer.Mixer()
            mixer.attach("hw:%d" % card_index)
            mixer.load()
            for mix in mixer.list():
                m = alsamixer.Element(mixer=mixer,
                        name=mix[0], index=0)
                if m.has_volume():
                    if mix[0] not in mixers:
                        mixers.append(mix[0])
        except Exception, err:
            log.exception(str(err))
        return mixers
