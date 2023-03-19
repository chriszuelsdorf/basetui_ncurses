import curses
import os
from enum import Enum
from ..subprog_template import SubProgTemplate


# type `flag flag_name` to activate/deactivate the flag
FLAGS = []


class twModes(Enum):
    TEXT = 0
    PWD = 1


class FileViewer(SubProgTemplate):
    def __init__(self) -> None:
        super().__init__()
        self.text = ["No text loaded."]
        self.maxtlen = 0
        self.vpos = 0
        self.hpos = 0
        self.mode = twModes.TEXT
        for f in FLAGS:
            setattr(self.flags, f, False)

    def handleInput(self, inp):
        self.log(f"TW input handler: `{inp}`", 9)
        if inp == "unload":
            self.text = ["No text loaded."]
            self.vpos = 0
            self.hpos = 0
            self.maxtlen = max([len(x) for x in self.text])
        elif inp.startswith("load "):
            fn = os.path.expanduser(inp[5:])
            if not os.path.exists(fn):
                self.text = [f"Failed to load file {fn} - File not found."]
            else:
                with open(fn, "r") as f:
                    self.text = f.readlines()
            self.vpos = 0
            self.hpos = 0
            self.maxtlen = max([len(x) for x in self.text])
        elif inp.startswith("flag "):
            flag = inp[5:]
            setattr(self.flags, flag, not getattr(self.flags, flag))
        else:
            self.log(f"TW: Unrecognized input `{inp}`.", 5)

    def handleKeypress(self, keypress):
        if keypress == "KEY_UP":
            if self.vpos == 0:
                curses.beep()
                curses.flash()
            else:
                self.vpos -= 1
        elif keypress == "KEY_DOWN":
            if self.vpos >= len(self.text) - 1:
                curses.beep()
                curses.flash()
            else:
                self.vpos += 1
        elif keypress == "KEY_RIGHT":
            if self.hpos >= self.maxtlen - 2:
                curses.beep()
                curses.flash()
            else:
                self.hpos += 1
        elif keypress == "KEY_LEFT":
            if self.hpos == 0:
                curses.beep()
                curses.flash()
            else:
                self.hpos -= 1

    def draw(self):
        self.win.clear()
        self.win.bkgd(self.cpairs.BODY)
        rows, cols = self.win.getmaxyx()
        crow = 0
        shown_lines = self.text[self.vpos : self.vpos + rows - 1]
        for line in shown_lines:
            text = line[self.hpos : cols + self.hpos - 1]
            self.win.addstr(crow, 0, text, self.cpairs.BODY)
            crow += 1
