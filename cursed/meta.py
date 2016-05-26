#!/usr/bin/env python
'''
cursed.meta

This contains the metaclass used to decorate all user classes that subclass
CursedWindow, crucial for the curses interface to work.
'''
from cursed.version import PY3

if PY3:
    from queue import Queue
else:
    from Queue import Queue


BASE_CURSED_CLASSES = ('CursedWindowClass', 'CursedWindow', 'CursedMenu')


class CursedWindowClass(type):

    WINDOWS = []

    def __new__(cls, name, parents, dct):
        new = super(CursedWindowClass, cls).__new__(cls, name, parents, dct)
        if name in BASE_CURSED_CLASSES:
            return new
        new.WIDTH = dct.get('WIDTH', 80)
        new.HEIGHT = dct.get('HEIGHT', 24)
        new.WINDOW = None
        new.APP = None
        new.X = dct.get('X', 0)
        new.Y = dct.get('Y', 0)
        new.BORDERED = dct.get('BORDERED', False)
        new.EVENTS = Queue()
        new.RESULTS = Queue()
        new.KEY_EVENTS = Queue()
        new.SCROLL = dct.get('SCROLL', False)
        new.WAIT = dct.get('WAIT', True)
        new.MENU = dct.get('MENU', None)
        new._KEYMAP = {}
        new._OPENED_MENU = None
        cls.WINDOWS += [new]
        return new