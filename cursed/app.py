#!/usr/bin/env python
'''
cursed.app

Contains the base functionality to run an app and return a result.
'''

import sys
import traceback
import gevent
import six
import curses

from cursed.window import CursedWindowClass


class Result(object):
    '''
    Result represents the object returned by `app.run()`, which may contain
    exception information.
    '''

    def __init__(self):
        self.exc_type, self.exc, self.tb = None, None, None

    def _extract_exception(self):
        self.exc_type, self.exc, self.tb = sys.exc_info()

    def _extract_thread_exception(self, thread):
        self.exc_type, self.exc, self.tb = thread.exc_info

    def unwrap(self):
        '''
        Unwraps the `Result`, raising an exception if one exists.
        '''
        if self.exc:
            six.reraise(self.exc_type, self.exc, self.tb)

    def ok(self):
        '''
        Return True if no exception occurred.
        '''
        return not bool(self.exc)

    def err(self):
        '''
        Returns the exception or None.
        '''
        return self.exc if self.exc else None

    def interrupted(self):
        '''
        Returns True if the application was interrupted, like through Ctrl-C.
        '''
        return self.exc_type is KeyboardInterrupt

    def print_exc(self):
        '''
        Prints the exception traceback.
        '''
        if self.tb:
            traceback.print_tb(self.tb)

    def __repr__(self):
        if self.exc_type is None:
            return 'Result(OKAY)'
        if self.interrupted():
            return 'Result(KeyboardInterrupt)'
        return 'Result(%s, message=%s)' % (self.exc_type.__name__,
                                           str(self.exc))


class CursedApp(object):
    '''
    The CursedApp is the main class which is used to track windows that are
    created and finally run the application.

    The CursedApp is initialized then run in the main function to build the
    windows.

    Example:
    ::

        from cursed import CursedApp, CursedWindow

        app = CursedApp()

        class MainWindow(CursedWindow):
            X, Y = (0, 0)
            WIDTH, HEIGHT = ('max', 'max')

            ...

        result = app.run()
        result.unwrap()
    '''

    def __init__(self):
        '''
        Initializes the CursedApp. No parameters are required.
        '''
        self.scr = None
        self.menu = None
        self.threads = []
        self.windows = None
        self.running = True

    def _run_windows(self):
        CursedWindowClass.fix_windows(self.MAX_WIDTH, self.MAX_HEIGHT)
        self.windows = CursedWindowClass.WINDOWS
        self.active_window = None
        for i, cw in enumerate(self.windows):
            thread = gevent.spawn(cw._cw_run, self, self.window)
            cw.THREAD = thread
            self.threads += [thread]

    def _input_loop(self):
        while self.running:
            for cw in self.windows:
                if cw.THREAD.exception is not None:
                    for cw in self.windows:
                        cw.RUNNING = False
                    self.running = False
                    break
                if cw.RUNNING and cw.WAIT:
                    break
            else:
                self.running = False
                break
            gevent.sleep(0)
            c = self.window.getch()
            if c == -1:
                continue
            for cw in self.windows:
                cw.KEY_EVENTS.put(c)

    def run(self):
        '''
        Runs all the windows added to the application, and returns a `Result`
        object.

        '''
        result = Result()
        try:
            self.scr = curses.initscr()
            self.MAX_HEIGHT, self.MAX_WIDTH = self.scr.getmaxyx()
            curses.noecho()
            curses.cbreak()
            curses.start_color()
            curses.use_default_colors()
            self.window = self.scr.subwin(0, 0)
            self.window.keypad(1)
            self.window.nodelay(1)
            self._run_windows()
            self.threads += [gevent.spawn(self._input_loop)]
            gevent.joinall(self.threads)
            for thread in self.threads:
                if thread.exception:
                    result._extract_thread_exception(thread)
        except KeyboardInterrupt:
            result._extract_exception()
        except Exception:
            result._extract_exception()
        finally:
            if self.scr is not None:
                self.scr.keypad(0)
                curses.echo()
                curses.nocbreak()
                curses.endwin()
        return result
