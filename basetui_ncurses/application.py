import curses
import _curses
import os
import pathlib
import datetime
from .enums import inputResponses
from .config import Config
import traceback


LH = lambda: f"[{datetime.datetime.now()}] "
MAX_LOGBUFFER_SIZE = 100
TRANSMITTABLE_KEYPRESSES = ["KEY_UP", "KEY_DOWN", "KEY_LEFT", "KEY_RIGHT"]
ESCAPE_SEQUENCE_KEYPRESSES = {
    "\x1b[A": "KEY_UP",
    "\x1b[B": "KEY_DOWN",
    "\x1b[C": "KEY_RIGHT",
    "\x1b[D": "KEY_LEFT",
}


class GenericObject:
    pass


class Application:
    def __init__(
        self,
        stdscr: _curses.window,
        logfile,
        metainfo,
        pobj,
        log_verbosity=1,
        dev=False,
    ):
        self.wininfo = (curses.LINES, curses.COLS)

        self.stdscr = stdscr
        self.wins = GenericObject()
        self.init_windows()

        self.pobj = pobj
        self.pobj.setWin(self.wins.center)
        self.pobj.setLogger(self.log)

        self.metainfo = metainfo
        curses.halfdelay(1)

        self.flags = GenericObject()

        self.log_verbosity = log_verbosity
        self.logbuffer = []
        self.logfile = logfile
        self.flush_logbuffer(trunc=True)

        try:
            self.config = Config(self.log)
            self.init_cpairs()
            self.pobj.setCPairs(self.cpairs)
        finally:
            self.flush_logbuffer()

    def flush_logbuffer(self, trunc=False):
        with open(self.logfile, "w" if trunc else "a") as f:
            if self.log_verbosity > 8:
                f.write(LH() + "Starting log write.\n")
            for l in self.logbuffer:
                f.write(l + "\n")
            if self.log_verbosity > 8:
                f.write(LH() + "Finished log write.\n")
        self.logbuffer = []

    def log(self, message, verbosity):
        if self.log_verbosity >= verbosity:
            self.logbuffer.append(LH() + str(message))
        if len(self.logbuffer) >= MAX_LOGBUFFER_SIZE:
            self.flush_logbuffer()

    def init_windows(self):
        self.wins.center = curses.newwin(curses.LINES - 2, curses.COLS, 1, 0)
        self.wins.header = curses.newwin(1, curses.COLS, 0, 0)
        self.wins.footer = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
        if hasattr(self, "pobj"):
            self.pobj.setWin(self.wins.center)

    def _initcolor(self, r, g, b):
        if not hasattr(self, "nccolori"):
            self.nccolori = 24
        self.nccolori += 1
        self.log(
            f"Initializing color {self.nccolori} as r {r}, g {g}, b {b}", 8
        )
        curses.init_color(self.nccolori, r, g, b)
        return self.nccolori

    def _initcpair(self, fg, bg):
        if not hasattr(self, "nccolori"):
            self.nccolori = 24
        self.nccolori += 1
        self.log(
            f"Initializing color pair {self.nccolori} as fg {fg}, bg {bg}", 8
        )
        curses.init_pair(self.nccolori, fg, bg)
        return curses.color_pair(self.nccolori)

    def init_cpairs(self):
        # Initialize colors
        colors = dict(self.config.colors)
        for c in colors:
            if (
                len(colors[c]) != 7
                or not colors[c].startswith("#")
                or not colors[c].lower().strip("1234567890abcdef") == "#"
            ):
                raise ValueError(
                    f"Invalid color value `{c}`: `{colors[c]}` passed"
                )
            r = min(max(int(int(colors[c][1:3], 16) * (1000 / 256)), 0), 1000)
            g = min(max(int(int(colors[c][3:5], 16) * (1000 / 256)), 0), 1000)
            b = min(max(int(int(colors[c][5:7], 16) * (1000 / 256)), 0), 1000)
            colors[c] = self._initcolor(r, g, b)

        self.log(colors, 1)

        # Initialize color pairs
        self.cpairs = GenericObject()
        cpairs = dict(self.config.color_pairs)
        for cpair in cpairs:
            fg = cpairs[cpair][0]
            fg = fg if isinstance(fg, int) else colors[fg]
            bg = cpairs[cpair][1]
            bg = bg if isinstance(bg, int) else colors[bg]
            if not isinstance(fg, int) or not isinstance(bg, int):
                raise TypeError(
                    f"Invalid pair {cpair}: ({type(fg)}: {fg}), ({type(bg)}: "
                    f"{bg})"
                )
            setattr(self.cpairs, cpair, self._initcpair(fg, bg))

    def handleinput(self, inp):
        self.log(f"Handling input `{inp}`.", 5)
        il = inp.lower()
        if il in ("quit", "exit"):
            return inputResponses.BREAK
        elif il.startswith(":"):
            if il == ":flushlog":
                self.flush_logbuffer()
                return inputResponses.NORMAL
        else:
            return self.pobj.handleInput(inp)

    def handleKeypress(self, keystr):
        return self.pobj.handleKeypress(keystr)

    def draw_header(self):
        self.wins.header.clear()
        header_text = f"{self.metainfo['pkgname']} v{self.metainfo['version']}"
        header_text = header_text[: curses.COLS - 1].center(curses.COLS - 1)
        if not hasattr(self.flags, "header"):
            self.flags.header = True
            self.log(f"Drawing header with color pair {self.cpairs.HEADER}", 8)
        self.wins.header.bkgd(self.cpairs.HEADER)
        self.wins.header.addstr(
            0,
            0,
            header_text,
            self.cpairs.HEADER,
        )
        self.wins.header.refresh()

    def draw_footer(self, buffer):
        self.wins.footer.clear()
        buf_text = buffer[: curses.COLS - 1]
        footer_text = buf_text.ljust(curses.COLS - 1)
        if not hasattr(self.flags, "footer"):
            self.flags.footer = True
            self.log(f"Drawing footer with color pair {self.cpairs.CMD}", 8)
        self.wins.footer.bkgd(self.cpairs.CMD)
        self.wins.footer.addstr(0, 0, footer_text, self.cpairs.CMD)
        self.wins.footer.addstr(
            0, len(buf_text), "_", self.cpairs.CMD | curses.A_BLINK
        )
        self.wins.footer.refresh()

    def run(self):
        curses.update_lines_cols()
        footer_buffer = ""
        multichar_escape_reader_chars_left = 0
        multichar_escape_reader_chars_buffer = ""
        while True:
            self.draw_header()
            self.draw_footer(footer_buffer)
            self.pobj.draw()
            self.wins.center.refresh()

            if (
                len(multichar_escape_reader_chars_buffer) > 0
                and multichar_escape_reader_chars_left == 0
            ):
                self.log(f"Seq was {multichar_escape_reader_chars_buffer}", 9)
                ret = self.handleKeypress(
                    ESCAPE_SEQUENCE_KEYPRESSES[
                        multichar_escape_reader_chars_buffer
                    ]
                )
                if ret == inputResponses.BREAK:
                    break
                multichar_escape_reader_chars_buffer = ""

            try:
                inp = self.wins.footer.getkey()
            except _curses.error:
                inp = None
            except KeyboardInterrupt:
                break

            if inp is not None:
                self.log(
                    f"INPUT `{inp.strip()}` of type {type(inp)}."
                    + (
                        str([(c, ord(c)) for c in inp])
                        if type(inp) == str
                        else ""
                    ),
                    9,
                )

            if inp is None:
                pass
            elif inp == "KEY_RESIZE":
                curses.update_lines_cols()
            elif inp in TRANSMITTABLE_KEYPRESSES:
                self.handleKeypress(inp)
            elif type(inp) == str and len(inp) == 1:
                if multichar_escape_reader_chars_left > 0:
                    multichar_escape_reader_chars_buffer += inp
                    multichar_escape_reader_chars_left -= 1
                # enter key
                elif ord(inp) == 10:
                    response = self.handleinput(footer_buffer)
                    if response == inputResponses.BREAK:
                        break
                    footer_buffer = ""
                elif ord(inp) == 27:
                    multichar_escape_reader_chars_left = 2
                    multichar_escape_reader_chars_buffer = inp
                elif ord(inp) in range(32, 127):
                    footer_buffer += inp
                # backspace
                elif ord(inp) == 127:
                    footer_buffer = footer_buffer[:-1]
                else:
                    self.log(
                        (
                            f"Unknown 1-char string input `{inp.strip()}` with "
                            f"ord {ord(inp)}"
                        ),
                        4,
                    )
            else:
                self.log(f"Unknown input {inp} of type {type(inp)}", 4)


def main(metainfo, extras, pobj):
    TWTUI_DIR = pathlib.Path(os.path.expanduser("~")) / ".twtui"
    if not os.path.exists(TWTUI_DIR):
        inp = input(
            f"TWTUI directory ({TWTUI_DIR}) does not exist. Would you like to "
            f"create it? (y/n) "
        ).lower()
        if inp == "y":
            os.mkdir(TWTUI_DIR)
        if inp == "n":
            print(f"Unable to continue without a program directory.")
            return
    LOG_LOC = TWTUI_DIR / "current.log"

    def submain(stdscr):
        curses.curs_set(0)
        try:
            extapp = extras["application"] if "application" in extras else {}
            app = Application(
                stdscr,
                logfile=LOG_LOC,
                metainfo=metainfo,
                pobj=pobj,
                **extapp,
            )
            try:
                app.run()
            except Exception as e:
                exc = f"ERROR:\n{type(e)}\n{e}\n" + traceback.format_exc()
                app.log(exc, 1)
                raise e
            finally:
                app.flush_logbuffer()
        finally:
            curses.curs_set(1)

    try:
        curses.wrapper(submain)
    except Exception as e:
        if extras["meta"]["dev"] is True:
            raise e
        else:
            print(
                f"Encountered an error. Look for details in {LOG_LOC}. If no "
                "traceback is present, pass the -d flag to get details."
            )
