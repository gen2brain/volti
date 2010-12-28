# -*- coding: utf-8 -*-

# Author: Milan Nikolic <gen2brain@gmail.com>
# Based on code from http://code.google.com/p/rox-volume
# by Kenneth Hayber <ken@hayber.us>
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
import gettext
from ConfigParser import ConfigParser

import gtk
import gobject
import alsaaudio as alsa

from config import Config
CONFIG = Config()

gettext.bindtextdomain(CONFIG.app_name, CONFIG.locale_dir)
gettext.textdomain(CONFIG.app_name)

import __builtin__
__builtin__._ = gettext.gettext

CHANNEL_LEFT  = 0
CHANNEL_RIGHT = 1
CHANNEL_MONO  = 2

_STEREO	= 1
_LOCK   = 2
_REC    = 4
_MUTE   = 8

class Mixer(gtk.Window):
    """ Volti Mixer Application"""
    def __init__(self):
        gtk.Window.__init__(self)

        self.cp = ConfigParser()
        self.cp.read(CONFIG.config_file)

        self.lock_mask = {}
        self.control_mask = {}
        self.card_hbox = {}
        self.alsa_channels = {}

        self.set_title("Volti Mixer")
        self.set_resizable(True)
        self.set_border_width(5)
        self.set_position(gtk.WIN_POS_CENTER)
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.connect('delete_event', self.quit)

        icon_theme = gtk.icon_theme_get_default()
        if icon_theme.has_icon("multimedia-volume-control"):
            self.set_icon_name("multimedia-volume-control")
        else:
            file = os.path.join(
                    CONFIG.res_dir, "icons", "multimedia-volume-control.svg")
            self.set_icon_from_file(file)

        self.acards = alsa.cards()
        self.set_layout()
        self.init_controls()
        self.show()

        card_index = int(self.cp.get("global", "card_index"))
        self.notebook.set_current_page(card_index)

    def set_layout(self):
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        self.notebook.show()

        vbox = gtk.VBox()
        vbox.add(self.notebook)
        self.add(vbox)

        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_EDGE)
        button1 = gtk.Button(label=_('_Select Controls...'))
        button1.connect("clicked", self.on_select_controls)
        bbox.add(button1)
        button2 = gtk.Button(stock=gtk.STOCK_QUIT)
        button2.connect("clicked", self.quit)
        bbox.add(button2)

        align = gtk.Alignment(xscale=1, yscale=1)
        align.set_padding(5, 0, 0, 0)

        align.add(bbox)
        vbox.pack_start(align, False, False)
        vbox.show_all()

    def init_controls(self):
        try:
            show_values = bool(int(
                self.cp.get("global", "mixer_show_values")))
        except:
            show_values = False

        for card_index, card_name in enumerate(self.acards):
            vbox = gtk.VBox()
            frame = gtk.Frame()
            hbox = gtk.HBox(True, 10)

            align = gtk.Alignment(xscale=1, yscale=1)
            align.set_padding(10, 10, 10, 10)

            align.add(hbox)
            vbox.add(align)
            frame.add(vbox)

            self.card_hbox[card_index] = hbox
            self.notebook.insert_page(frame, gtk.Label(card_name), card_index)

            try:
                self.lock_mask[card_index] = int(
                        self.cp.get("card-%d" % card_index, "mask_lock"))
            except:
                self.lock_mask[card_index] = 0

            try:
                self.control_mask[card_index] = int(
                        self.cp.get("card-%d" % card_index, "mask_control"))
            except:
                self.control_mask[card_index] = 0
                for count, mixer in enumerate(alsa.mixers(card_index)):
                    self.control_mask[card_index] |= (1 << count)

            n = 0
            self.get_channels(card_index)
            for channel, id in self.alsa_channels[card_index]:
                option_mask = option_value = _LOCK
                mixer = alsa.Mixer(channel, id, card_index)

                if not len(mixer.volumecap()):
                    continue

                if len(mixer.getvolume()) > 1:
                    option_mask |= _STEREO
                    option_mask |= _LOCK

                if self.lock_mask[card_index] & (1 << n):
                    option_value |= _LOCK

                try:
                    if mixer.getrec():
                        option_mask |= _REC
                    if mixer.getrec()[0]:
                        option_value |= _REC
                    if mixer.getmute():
                        option_mask |= _MUTE
                    if mixer.getmute()[0]:
                        option_value |= _MUTE
                except:
                    pass

                for el in hbox, align, vbox, frame:
                    el.show()

                volume = MixerControl(n, option_mask, option_value,
                        show_values, card_index, channel)
                volume.set_level(self.get_volume(n, card_index))
                volume.connect("volume_changed", self.adjust_volume)
                volume.connect("volume_setting_toggled", self.setting_toggled)
                hbox.pack_start(volume, True, True)
                n += 1

            self.show_hide_controls(card_index)

    def get_channels(self, card_index):
        try:
            self.alsa_channels[card_index] = []
            for channel in alsa.mixers(card_index):
                id = 0
                while (channel, id) in self.alsa_channels[card_index]:
                    id += 1
                mixer = alsa.Mixer(channel, id, card_index)
                if len(mixer.volumecap()):
                    self.alsa_channels[card_index].append((channel, id))
        except:
            pass

    def setting_toggled(self, vol, channel, button, val, card_index):
        """ Handle checkbox toggles """
        ch, id = self.alsa_channels[card_index][channel]
        mixer = alsa.Mixer(ch, id, card_index)

        if button == _MUTE:
            mixer.setmute(val)

        if button == _LOCK:
            if val:
                self.lock_mask[card_index] |= (1<<channel)
            else:
                self.lock_mask[card_index] &= ~(1<<channel)

        if button == _REC:
            mixer.setrec(val)

    def adjust_volume(self, vol, channel, volume1, volume2, card_index):
        """ Track changes to the volume controls """
        self.set_volume((volume1, volume2), channel, card_index)

    def set_volume(self, volume, channel, card_index):
        """ Set the playback volume """
        ch, id = self.alsa_channels[card_index][channel]
        mixer = alsa.Mixer(ch, id, card_index)
        try:
            mixer.setvolume(volume[0], 0)
            mixer.setvolume(volume[1], 1)
        except:
            pass

    def get_volume(self, channel, card_index):
        """ Get the current sound card setting for specified channel """
        ch, id = self.alsa_channels[card_index][channel]
        mixer = alsa.Mixer(ch, id, card_index)
        vol = mixer.getvolume()
        if len(vol) == 1:
            return (vol[0], vol[0])
        return (vol[0], vol[1])

    def on_select_controls(self, widget=None):
        card_index = self.notebook.get_current_page()
        dialog = SelectControls(self, self.cp, card_index)

    def show_hide_controls(self, card_index):
        controls = self.card_hbox[card_index].get_children()
        for control in controls:
            if self.control_mask[card_index] & (1 << control.channel):
                control.show()
            else:
                control.hide()

    def write_config(self):
        for card_index, card_name in enumerate(self.acards):
            section = "card-%d" % card_index
            if not self.cp.has_section(section):
                self.cp.add_section(section)
            self.cp.set(section, "mask_lock", self.lock_mask[card_index])
        self.cp.write(open(CONFIG.config_file, "w"))

    def quit(self, element=None, event=None):
        """ Exit main loop """
        self.write_config()
        gtk.main_quit()

class SelectControls(gtk.Window):
    """ Select controls dialog """
    def __init__(self, parent=None, cp=None, card_index=0):
        gtk.Window.__init__(self)
        self.connect('destroy', self.close)
        self.set_title('Select Controls')
        self.set_transient_for(parent)
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        self.set_border_width(10)
        self.set_default_size(200, 300)

        icon_theme = gtk.icon_theme_get_default()
        self.set_icon_name("preferences-desktop")

        self.cp = cp
        self.main = parent
        self.card_index = card_index
        self.mixers = alsa.mixers(self.card_index)

        try:
            self.main.control_mask[self.card_index] = int(
                    self.cp.get("card-%d" % self.card_index, "mask_control"))
        except:
            self.main.control_mask[self.card_index] = 0
            for count, mixer in enumerate(self.mixers):
                self.main.control_mask[self.card_index] |= (1 << count)

        self.set_layout()

    def set_layout(self):
        vbox = gtk.VBox(False, 8)
        self.add(vbox)

        hbox = gtk.HBox(False, 5)
        label = gtk.Label()
        label.set_markup('<b>%s</b>' % _('Select which controls should be visible'))
        image = gtk.image_new_from_icon_name('preferences-desktop', gtk.ICON_SIZE_DIALOG)
        hbox.pack_start(image, False, False)
        hbox.pack_start(label, False, False)
        vbox.pack_start(hbox, False, False)

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(sw)

        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.BUTTONBOX_END)
        button = gtk.Button(stock=gtk.STOCK_CLOSE)
        button.connect('clicked', self.close)
        bbox.add(button)
        vbox.pack_start(bbox, False, False)

        model = self._create_model()
        treeview = gtk.TreeView(model)
        treeview.set_headers_visible(False)

        sw.add(treeview)
        self._add_columns(treeview)
        self.show_all()

    def _create_model(self):
        lstore = gtk.ListStore(
            gobject.TYPE_BOOLEAN,
            gobject.TYPE_STRING)

        for count, mixer in enumerate(self.mixers):
            if (self.main.control_mask[self.card_index] & (1 << count)):
                show = True
            else:
                show = False
            iter = lstore.append()
            lstore.set(iter,
                0, show,
                1, mixer)
        return lstore

    def _add_columns(self, treeview):
        model = treeview.get_model()

        renderer = gtk.CellRendererToggle()
        renderer.connect('toggled', self.on_control_toggled, model)

        column = gtk.TreeViewColumn('Checkbox', renderer, active=0)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        column.set_fixed_width(30)
        treeview.append_column(column)

        column = gtk.TreeViewColumn('Mixer', gtk.CellRendererText(), text=1)
        treeview.append_column(column)

    def _calc_mask(self, model, path, iter):
        active = model.get(iter, 0)
        if active[0]:
            self.main.control_mask[self.card_index] |= (1 << path[0])

    def on_control_toggled(self, cell, path, model):
        iter = model.get_iter((int(path),))
        control = model.get_value(iter, 0)
        control = not control
        model.set(iter, 0, control)

        self.main.control_mask[self.card_index] = 0
        model.foreach(self._calc_mask)

    def write_config(self):
        section = "card-%d" % self.card_index
        if not self.cp.has_section(section):
            self.cp.add_section(section)
        self.cp.set(section, "mask_control", str(self.main.control_mask[self.card_index]))
        self.cp.write(open(CONFIG.config_file, "w"))

    def close(self, widget=None):
        self.write_config()
        self.main.show_hide_controls(self.card_index)
        self.destroy()

class MixerControl(gtk.Frame):
    """
    A Class that implements a volume control (stereo or mono) for a sound card
    mixer. Each instance represents one mixer channel on the sound card.
    """

    __gsignals__ = {
            'volume_changed': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN,
                (gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_INT)),
            'volume_setting_toggled': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_BOOLEAN,
                (gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_INT, gobject.TYPE_INT))
        }

    def __init__(self, channel, option_mask, option_value, show_value, card_index, label=None):
        """
        Create a volume control widget
        'channel' specifies the audio device mixer channel.
        'option_mask' configures the widget while 'option_value' sets the actual
        value of the corresponding mask (e.g. 'option_mask |= _MUTE' shows the mute
        checkbox while 'option_value |= _MUTE' causes it to be checked by default)
        'show_value' controls whether the volume text is displayed or not.
        'card_index' is the index of the sound card
        'label' is the name of the channel (e.g. 'PCM).

        The widget supports two signals 'volume_changed' and 'volume_setting_toggled'.
        'volume_changed' always sends left and right volume settings regardless of
        whether the control is locked or mono.

        'volume_setting_toggled' notifies the parent of changes in the optional checkboxes.
        """
        gtk.Frame.__init__(self, label)

        self.card_index = card_index
        self.rec = self.lock = self.stereo = self.mute = False
        if option_mask & _LOCK:
            self.lock = True
            self.channel_locked = option_value & _LOCK

        if option_mask & _REC:
            self.rec = True
            self.channel_rec = option_value & _REC

        if option_mask & _MUTE:
            self.mute = True
            self.channel_muted = option_value & _MUTE

        if option_mask & _STEREO:
            self.stereo = True

        self.channel = channel
        self.vol_left = self.vol_right = 0

        vbox = gtk.VBox()
        control_box = gtk.HBox(True, 0)
        option_box = gtk.HBox(True, 0)

        align = gtk.Alignment(xscale=1, yscale=1)
        align.set_padding(5, 5, 5, 5)
        self.set_label_align(0.5, 0.8)

        align.add(vbox)
        self.add(align)

        self.volume1 = gtk.Adjustment(0.0, 0.0, 100.0, 1.0, 10.0, 0.0)
        if self.stereo:
            self.volume1_handler_id = self.volume1.connect('value_changed', self.value_changed,
                    channel, CHANNEL_LEFT, card_index)
        else:
            self.volume1_handler_id = self.volume1.connect('value_changed', self.value_changed,
                    channel, CHANNEL_MONO, card_index)

        volume1_control = gtk.VScale(self.volume1)
        volume1_control.set_inverted(True)
        volume1_control.set_draw_value(show_value)
        volume1_control.set_digits(0)
        volume1_control.set_size_request(-1, 250)
        volume1_control.set_value_pos(gtk.POS_TOP)
        control_box.pack_start(volume1_control, True, True)

        if self.stereo:
            self.volume2 = gtk.Adjustment(0.0, 0.0, 100.0, 1.0, 10.0, 0.0)
            self.volume2_handler_id = self.volume2.connect('value_changed', self.value_changed,
                    channel, CHANNEL_RIGHT, card_index)

            volume2_control = gtk.VScale(self.volume2)
            volume2_control.set_inverted(True)
            volume2_control.set_draw_value(show_value)
            volume2_control.set_digits(0)
            volume2_control.set_size_request(-1, 300)
            volume2_control.set_value_pos(gtk.POS_TOP)
            control_box.pack_start(volume2_control, True, True)

        if self.rec:
            self.rec_element = self.toggle_element(
                    self.channel_rec, channel, _REC)
            option_box.pack_start(self.rec_element, False, False)

        if self.mute:
            mute_element = self.toggle_element(
                    self.channel_muted, channel, _MUTE)
            option_box.pack_start(mute_element, False, False)

        if self.stereo and self.lock:
            lock_element = self.toggle_element(
                    self.channel_locked, channel, _LOCK)
            option_box.pack_start(lock_element, False, False)

        self.control1 = volume1_control
        if self.stereo:
            self.control2 = volume2_control

        vbox.pack_start(control_box, True, True)
        vbox.pack_start(option_box, False, False, 5)

        self.show_all()

    def set_level(self, level):
        """
        Allow the volume settings to be passed in from the parent.
        'level' is a tuple of integers from 0-100 as (left, right).
        """
        self.volume1.handler_block(self.volume1_handler_id)
        self.volume1.set_value(level[0])
        self.volume1.handler_unblock(self.volume1_handler_id)
        if self.stereo:
            self.volume2.handler_block(self.volume2_handler_id)
            self.volume2.set_value(level[1])
            self.volume2.handler_unblock(self.volume2_handler_id)

    def get_level(self):
        """
        Return the current widget's volume settings as a tuple of
        integers from 0-100 as (left, right)
        """
        return (self.vol_left, self.vol_right)

    def value_changed(self, vol, channel, channel_lr, card_index):
        """
        Track changes in the volume controls and pass them back to the parent
        via the 'volume_changed' signal.
        """
        if channel_lr == CHANNEL_LEFT:
            self.vol_left = int(vol.get_value())
            if self.lock and self.channel_locked:
                self.vol_right = self.vol_left
                self.volume2.handler_block(self.volume2_handler_id)
                self.volume2.set_value(vol.get_value())
                self.volume2.handler_unblock(self.volume2_handler_id)

        elif channel_lr == CHANNEL_RIGHT:
            self.vol_right = int(vol.get_value())
            if self.lock and self.channel_locked:
                self.vol_left = self.vol_right
                self.volume1.handler_block(self.volume1_handler_id)
                self.volume1.set_value(vol.get_value())
                self.volume1.handler_unblock(self.volume1_handler_id)
        else:
            self.vol_left = self.vol_right = int(vol.get_value())
        self.emit("volume_changed", channel, self.vol_left, self.vol_right, card_index)

    def check(self, button, channel, id):
        """
        Process the various checkboxes/buttons and signal the parent when they change
        via the 'volume_setting_toggled' signal.
        """
        active = button.get_active()
        if id == _LOCK:
            self.channel_locked = not self.channel_locked
            if self.channel_locked:
                avg_vol = (self.vol_left+self.vol_right)/2
                self.volume1.set_value(avg_vol)
                self.volume2.set_value(avg_vol)
        elif id == _MUTE:
            self.channel_muted = not self.channel_muted
        elif id == _REC:
            self.channel_rec = not self.channel_rec
        button.set_property("image", self.button_image(id, active))
        self.emit('volume_setting_toggled', channel, id, button.get_active(), self.card_index)

    def toggle_element(self, active, channel, id):
        button = gtk.ToggleButton()
        image = self.button_image(id, active)
        button.set_property("image", image)
        button.set_active(active)
        button.connect('toggled', self.check, channel, id)
        return button

    def button_image(self, id, active):
        if id == _LOCK:
            icon = "mixer-lock.png" if active else "mixer-no-lock.png"
        elif id == _MUTE:
            icon = "mixer-muted.png" if active else "mixer-no-muted.png"
        elif id == _REC:
            icon = "mixer-record.png" if active else "mixer-no-record.png"
        image = gtk.Image()
        image.set_from_file(os.path.join(CONFIG.res_dir, "icons", icon))
        image.show()
        return image

    def show_values(self, show_value):
        self.control1.set_draw_value(show_value)
        if self.stereo:
            self.control2.set_draw_value(show_value)
