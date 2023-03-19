import curses
from typing import final
from .application import GenericObject


NON_OVERRIDABLE_METHODS = ["setWin", "setCPairs", "setLogger"]


class SubProgTemplate:
    def __init__(self) -> None:
        for m in NON_OVERRIDABLE_METHODS:
            if getattr(SubProgTemplate, m) != getattr(type(self), m):
                raise RuntimeError(
                    f"The method {m} is overloaded but not permitted to be so."
                )
        self.flags = GenericObject()

    def handleInput(self, inp):
        raise NotImplementedError()

    def handleKeypress(self, keypress):
        raise NotImplementedError()

    def draw(self):
        raise NotImplementedError()

    @final
    def setWin(self, win):
        self.win = win

    @final
    def setLogger(self, logger):
        self.log = logger

    @final
    def setCPairs(self, cpairs):
        self.cpairs = cpairs
