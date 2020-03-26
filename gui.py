#!/usr/bin/env python3
import curses
from datetime import datetime
from time import sleep
from threading import Thread, Lock
from pathlib import Path

# Configuration
SLEEP_TIME = 0.01

# Directions
LEFT        = 0
UP_LEFT     = 1
UP          = 2
UP_RIGHT    = 3
RIGHT       = 4
DOWN_RIGHT  = 5
DOWN        = 6
DOWN_LEFT   = 7

# Origins
TOP_LEFT        = 8
TOP_CENTER      = 9
TOP_RIGHT       = 10
CENTER_LEFT     = 11
CENTER          = 12
CENTER_RIGHT    = 13
BOTTOM_LEFT     = 14
BOTTOM_CENTER   = 15
BOTTOM_RIGHT    = 16

# Singletons
BLANK_PIXEL = (' ', curses.A_NORMAL)


class GUI:
    def __init__(self):
        """
        GUI constructor. Does not take any parameters.
        """
        self.running = True
        self.input_thread = Thread(target=input_thread, args=(self,))
        self.render_thread = Thread(target=render_thread, args=(self,))
        self.lock = Lock()
        self.screen = None
        self.pixels = {}

    def __bool__(self):
        """
        GUI is considered 'True' until someone calls GUI.stop()
        """
        return bool(self.running)

    # Abstract methods
    def setup(self):
        """
        Abstract method.

        This method is called at the beginning of the start method
        before the input and render threads run.
        """
        pass

    def pre_render(self):
        """
        Abstract method.

        This method is called on each frame (30 times per second) before
        the render and post_render methods.
        """
        pass

    def render(self):
        """
        Abstract method.

        This method is called on each frame (30 times per second) after
        pre_render and before post_render.
        """
        pass

    def post_render(self):
        """
        Abstract method.

        This method is called on each frame (30 times per second) after
        pre_render and render.
        """
        pass

    def keypress(self, key):
        """
        Abstract method.

        This method is called each time the user presses a key.
        """
        pass

    # Public Methods
    def log(self, *args, sep=' ', end='\n'):
        timestamp = str(datetime.now())
        with open(Path.home() / ".gui_log", "a") as log_file:
            log_file.write(timestamp)
            log_file.write(" ")
            log_file.write(sep.join(args))
            log_file.write(end)

    def start(self):
        """
        Start the gui's main loops.
        GUI.start should only be called once.
        """
        open(Path.home() / '.gui_log', 'w').close()
        self.log("GUI start")
        with Screen() as screen:
            self.screen = screen
            self.setup()
            self.input_thread.start()
            self.render_thread.start()
            while True:
                try:
                    self.input_thread.join()
                    self.render_thread.join()
                    break
                except (KeyboardInterrupt, EOFError):
                    self.stop()
                    self.log("GUI ended by keyboard interrupt")
        self.log("GUI end")

    def stop(self):
        """
        Tell the threads to end and the start method to return.
        """
        self.running = False

    def draw_string(self, coord, string, *,
            attr=curses.A_NORMAL,
            direction=RIGHT,
            origin=BOTTOM_LEFT):
        """
        Updates a string of pixels, ignoring those that go out
        of the bounds of the screen.
        """
        x, y = coord
        origin_x, origin_y = self.get_origin_reference(origin)
        directional_x, directional_y = self.get_directional_reference(direction)
        for i, character in enumerate(string):
            self.draw(
                (
                    origin_x + (x + directional_x * i),
                    origin_y + (y + directional_y * i)
                ),
                character,
                attr=attr
            )

    def draw(self, coord, character, *, attr=curses.A_NORMAL):
        """
        Updates a single pixel, translating from regular
        x and y coord pair to upside down y, x pair for curses
        relative to the center coord.
        """
        x, y = coord
        if 0 <= x < self.screen_width and 0 <= y < self.screen_height:
            curses_y = self.screen_height - (y + 1)
            curses_coord = (curses_y, x)
            self.pixels[curses_coord] = (character, attr)

    def get_directional_reference(self, direction):
        if direction == LEFT:
            return (-1,  0)
        elif direction == UP_LEFT:
            return (-1,  1)
        elif direction == UP:
            return ( 0,  1)
        elif direction == UP_RIGHT:
            return ( 1,  1)
        elif direction == RIGHT:
            return ( 1,  0)
        elif direction == DOWN_RIGHT:
            return ( 1, -1)
        elif direction == DOWN:
            return ( 0, -1)
        elif direction == DOWN_LEFT:
            return (-1, -1)
        else:
            raise ValueError("Unknown direction '{}'".format(direction))

    def get_origin_reference(self, origin):
        if origin == TOP_LEFT:
            return (0                       , self.screen_height - 1)
        elif origin == TOP_CENTER:
            return (self.screen_width >> 1  , self.screen_height - 1)
        elif origin == TOP_RIGHT:
            return (self.screen_width - 1   , self.screen_height - 1)
        elif origin == CENTER_LEFT:
            return (0                       , self.screen_height >> 1)
        elif origin == CENTER:
            return (self.screen_width >> 1  , self.screen_height >> 1)
        elif origin == CENTER_RIGHT:
            return (self.screen_width - 1   , self.screen_height >> 1)
        elif origin == BOTTOM_LEFT:
            return (0                       , 0)
        elif origin == BOTTOM_CENTER:
            return (self.screen_width >> 1  , 0)
        elif origin == BOTTOM_RIGHT:
            return (self.screen_width - 1   , 0)
        else:
            raise ValueError("Unknown origin '{}'".format(origin))


def input_thread(gui):
    """
    This thread runs the gui.io function in a loop to
    get input from the user.
    """
    while gui:
        try:
            key = gui.screen.getch()
            if key == -1:
                continue
            gui.keypress(key)
        except (KeyboardInterrupt, EOFError):
            gui.stop()
            gui.log("Input thread received Keyboard Interrupt / EOF")
        except BaseException as e:
            gui.stop()
            gui.log("Input thread exception, {}: {}".format(type(e), e))


def render_thread(gui):
    """
    This thread runs the gui.render function thirty times per
    second and stops the gui if any errors occur.
    """
    while gui:
        sleep(SLEEP_TIME)
        try:
            # Update the window size
            gui.screen_size = gui.screen.getmaxyx()
            gui.screen_height = gui.screen_size[0]
            gui.screen_width = gui.screen_size[1]

            # Run the render functions to populate pixels
            gui.pre_render()
            gui.render()
            gui.post_render()

            # Output the pixels to the screen.
            for y in range(gui.screen_height):
                for x in range(gui.screen_width):
                    pixel = gui.pixels.get((y, x), BLANK_PIXEL)
                    try:
                        gui.screen.addstr(y, x, *pixel)
                    except Exception as e:
                        pass

            # Zero the pixels
            gui.pixels = {}

        except BaseException as e:
            gui.stop()
            gui.log("Render thread exception, {}: {}".format(type(e), e))


class Screen:
    def __enter__(self):
        # Initialize screen
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(1)

        # Setup colors
        curses.start_color()
        curses.use_default_colors()
        for i in range(curses.COLORS):
            curses.init_pair(i + 1, i, -1)

        # Set cursor invisible and timeout on read
        curses.curs_set(0)
        self.screen.timeout(50)

        # Return the curses screen
        return self.screen

    def __exit__(self, *args, **kwargs):
        # Return terminal to normal
        curses.curs_set(1)
        self.screen.keypad(0)
        curses.echo()
        curses.nocbreak()
        curses.endwin()
