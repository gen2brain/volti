#!/usr/bin/env python

import os
import sys
import glob
import subprocess
from distutils.core import setup
from distutils.command.install_data import install_data
from distutils.command.build import build
from distutils.dep_util import newer
from distutils.log import info

from src.config import Config
config = Config()

PO_DIR = 'po'
MO_DIR = os.path.join('build', 'mo')

class BuildLocales(build):
  def run(self):
    build.run(self)

    for po in glob.glob(os.path.join(PO_DIR, '*.po')):
      lang = os.path.basename(po[:-3])
      mo = os.path.join(MO_DIR, lang, config.APP_NAME + '.mo')

      directory = os.path.dirname(mo)
      if not os.path.exists(directory):
        os.makedirs(directory)

      if newer(po, mo):
        info('compiling %s -> %s' % (po, mo))
        try:
          rc = subprocess.call(['msgfmt', po, '-o', mo])
          if rc != 0:
            raise Warning, "msgfmt returned %d" % rc
        except Exception, e:
          print "Building gettext files failed."
          print "%s: %s" % (type(e), str(e))
          sys.exit(1)

class InstallLocales(install_data):
  def run(self):
    self.data_files.extend(self._find_mo_files())
    install_data.run (self)

  def _find_mo_files(self):
    data_files = []
    for mo in glob.glob(os.path.join(MO_DIR, '*', config.APP_NAME + '.mo')):
        lang = os.path.basename(os.path.dirname(mo))
        dest = os.path.join('share', 'locale', lang, 'LC_MESSAGES')
        data_files.append((dest, [mo]))
    return data_files

setup(name = config.APP_NAME,
        version = config.APP_VERSION,
        description = "GTK+ application for controlling audio volume from system tray/notification area",
        author = "Milan Nikolic",
        author_email = "gen2brain@gmail.com",
        license = "GNU GPLv3",
        url = "http://code.google.com/p/volti/",
        download_url = "http://volti.googlecode.com/files/%s-%s.tar.gz " % (config.APP_NAME, config.APP_VERSION),
        packages = ["volti"],
        package_dir = {"volti": "src"},
        scripts = ["volti"],
        requires = ["gtk", "gobject", "cairo", "alsaaudio", "dbus", "Xlib"],
        platforms = ["Linux"],
        cmdclass = {'build': BuildLocales, 'install_data': InstallLocales},
        data_files = [("share/volti", ["data/preferences.glade"]),
                    ("share/applications", ["data/volti.desktop"]),
                    ("share/man/man1", ["doc/volti.1"])]
        )
