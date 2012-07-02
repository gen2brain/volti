# -*- coding: utf-8 -*-

import os
import gettext

APP_NAME = "volti"
APP_VERSION = "0.3.0-svn"
RES_DIR = None
LOCALE_DIR = None

CONFIG_DIR = os.path.expanduser(os.path.join("~", ".config", APP_NAME))
CONFIG_FILE = os.path.join(CONFIG_DIR, "config")

try:
    from Xlib import X
    HAS_XLIB = True
except ImportError:
    HAS_XLIB = False

gettext.bindtextdomain(APP_NAME, LOCALE_DIR)
gettext.textdomain(APP_NAME)

import __builtin__
__builtin__._ = gettext.gettext

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
