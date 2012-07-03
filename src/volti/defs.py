# -*- coding: utf-8 -*-

import os
import gettext

APP_NAME = "volti"
APP_VERSION = "0.3.0-svn"
RES_DIR = None
LOCALE_DIR = None

CONFIG_DIR = os.path.expanduser(os.path.join("~", ".config", APP_NAME))
CONFIG_FILE = os.path.join(CONFIG_DIR, "config")

gettext.bindtextdomain(APP_NAME, LOCALE_DIR)
gettext.textdomain(APP_NAME)

import __builtin__
__builtin__._ = gettext.gettext

try:
    from gi.repository import Gtk
    HAS_GTK3 = True
    HAS_GTK2 = False
except ImportError:
    try:
        import gtk
        HAS_GTK3 = False
        HAS_GTK2 = True
    except ImportError:
        HAS_GTK3 = False
        HAS_GTK2 = False

try:
    import pyalsa
    HAS_PYALSA = True
    HAS_PYALSAAUDIO = False
except ImportError:
    try:
        import alsaaudio
        HAS_PYALSA = False
        HAS_PYALSAAUDIO = True
    except ImportError:
        HAS_PYALSA = False
        HAS_PYALSAAUDIO = False

try:
    from Xlib import X
    HAS_XLIB = True
except ImportError:
    HAS_XLIB = False

for base in ["/usr/local/share", "/usr/share"]:
    if os.path.isdir(os.path.join(base, APP_NAME)):
        RES_DIR = os.path.join(base, APP_NAME)
        LOCALE_DIR = os.path.join(base, "locale")
        break

if not RES_DIR:
    RES_DIR = os.path.realpath(os.path.join(".", "data"))

PREFS = {
"card_index": 0,
"control": "Master",
"mixer": "alsamixer",
"run_in_terminal": 1,
"mixer_internal": 1,
"mixer_show_values": 1,
"icon_theme": "Default",
"scale_increment": 1.0,
"scale_show_value": 0,
"show_tooltip": 1,
"toggle": "mute",
"keys": 0,
"show_notify": 0,
"notify_timeout": 2.0,
"notify_position": 0,
"notify_body": '{volume}\n{card}\n{mixer}'
}
