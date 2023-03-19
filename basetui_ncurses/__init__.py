import pathlib

install_directory = pathlib.Path(__file__).parent.absolute()

from .application import main as mainLoop
from .subprog_template import SubProgTemplate
