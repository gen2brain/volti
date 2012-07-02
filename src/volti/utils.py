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

class Logger():
    def __init__(self):
        log_format = '%(levelname)s: %(message)s'
        logging.basicConfig(level=logging.DEBUG, format=log_format)
        self.logger = logging.getLogger('frontend')

log = Logger().logger
