import os
import logging
from subprocess import Popen, PIPE

def which(prog):
    """ Equivalent of unix which command """
    def is_exe(fpath):
        return os.path.exists(fpath) and os.access(fpath, os.X_OK)

    paths = os.environ["PATH"].split(os.pathsep)
    paths.append(".")

    fpath, fname = os.path.split(prog)
    if fpath:
        if is_exe(prog):
            return prog
    else:
        for path in paths:
            filename = os.path.join(path, prog)
            if is_exe(filename):
                return filename
    return None

def find_term():
    """ Find terminal application """
    term = os.getenv("TERM")
    if term == "linux" or term is None:
        if which("gconftool-2"):
            term = Popen(["gconftool-2", "-g",
                "/desktop/gnome/applications/terminal/exec"],
                    stdout=PIPE).communicate()[0].strip()
        else:
            term = 'xterm'
    if term == "rxvt" and not which(term):
        term = "urxvt"
    return term

def get_pid_app():
    """ Returns application that can find pid by name """
    if which("pidof"):
        return "pidof -x"
    elif which("pgrep"):
        return "pgrep"
    return None

def get_icon_name(volume):
    """ Returns icon name for current volume """
    if volume == 0 or volume == _("Muted"):
        icon = "audio-volume-muted"
    elif volume <= 33:
        icon = "audio-volume-low"
    elif volume <= 66:
        icon = "audio-volume-medium"
    elif volume > 66:
        icon = "audio-volume-high"
    return icon

def get_icon_themes(res_dir):
    """ Returns list of icon themes """
    themes = ["Default"]
    icons_dir = os.path.join(res_dir, "icons")
    try:
        for file in os.listdir(icons_dir):
            if os.path.isdir(os.path.join(icons_dir, file)):
                if not file.startswith("."):
                    themes.append(file)
    except OSError:
        pass
    return themes

class Logger():
    def __init__(self):
        log_format = '%(levelname)s: %(message)s'
        logging.basicConfig(level=logging.DEBUG, format=log_format)
        self.logger = logging.getLogger('frontend')

log = Logger().logger
