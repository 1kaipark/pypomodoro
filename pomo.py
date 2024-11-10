import time
import pyfiglet
import curses
import argparse
import random
import string

from playsound import playsound
from _curses import error as CursesError

from pathlib import Path
import threading

from typing import Literal

FOCUS_TEXT: str = pyfiglet.figlet_format("focus...", "small")
REST_TEXT: str = pyfiglet.figlet_format("take a break...", "small")
LB_TEXT: str = pyfiglet.figlet_format("relax...", "small")
DING_SFX: str = str(Path(__file__).parent / "assets/ding.wav")

DEVIOUS_LIST: list[str] = (
    [" "] * 1000 + ["*"] * 2 + ["@", "{", "}", "*", "."]*10 + [c for c in string.ascii_letters]
)

from logger import log

def time_fmt(secs: int, display_hours: bool = False) -> str:
    """Returns base-60 time string in format 00:00.00"""
    h, rm = secs // 3600, secs % 3600
    m = rm // 60
    s = rm % 60
    disp = [str(int(v)).zfill(2) for v in [h, m, s]]

    if display_hours:
        return "{}:{}:{}".format(*disp)
    else:
        return "{}:{}".format(*disp[1:])
    
def rand_string(character_set, length):
    """Returns a random string.
        character_set -- the characters to choose from.
        length        -- the length of the string.
    """
    return "".join(random.choice(character_set) for _ in range(length))

try:
    from playsound import playsound 
    def play_ding():
        threading.Thread(target=playsound, args=(DING_SFX,), daemon=True).start()
except Exception as e:
    play_ding = lambda : 1

BACKGROUND_CHARSETS: dict = {
    "matrix": string.printable + "｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ"*50 + " "*50000,
    "snow": ".*                         "
}

class CursesPomo(object):
    def __init__(
        self,
        stdscr,
        focus_duration: int = 25 * 60,
        rest_duration: int = 5 * 60,
        long_break_duration: int = 20 * 60,
        num_sessions: int = 2,
        bg_type: Literal["snow", "matrix", "none"] = "snow"
    ):
        self.stdscr = stdscr

        self.focus_duration = focus_duration
        self.rest_duration = rest_duration
        self.long_break_duration = long_break_duration
        self.bg_type = bg_type
        # session counter 
        self.num_sessions = num_sessions


        self.show_elapsed: bool = False

        self.h, self.w = self.stdscr.getmaxyx()

        # initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_CYAN, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_WHITE, -1)

        self.stdscr.nodelay(True)  # non-blocking input

        self.dynamic_bg_accumulator = []
        self.dynamic_bg_frame_counter = 0

        self.run()

    def render_background_random(self, *args) -> None:
        # if self.stdscr.getmaxyx()[1] < self.w:
        #     self.dynamic_bg_accumulator = [] # clear cached background if the window has become smaller, as this will fail to render

        self.h, self.w = self.stdscr.getmaxyx()  # refresh dims
        bg_h, bg_w = self.h - 1, self.w - 1


        match self.bg_type:
            case "matrix":
                color = curses.color_pair(3) 
                charset = "matrix"
            case "snow":
                color = curses.color_pair(4)
                charset = "snow"
            case "none":
                return
        row = random.choices(BACKGROUND_CHARSETS[self.bg_type], k=bg_w)
        if len(self.dynamic_bg_accumulator) > bg_h:
            self.dynamic_bg_accumulator = self.dynamic_bg_accumulator[:-1]

        self.dynamic_bg_accumulator = [row] + self.dynamic_bg_accumulator

        try:
            for i, line in enumerate(self.dynamic_bg_accumulator):
                self.stdscr.addstr(0 + i, 0, "".join(line), color)
        except CursesError as e:
            # self.dynamic_bg_accumulator = []
            return

    def render_ascii_str(
        self,
        display_ascii: str,
        positioning: Literal["center", "topcenter", "topright", "topleft"] = "center",
        color_pair: int = 0,
        y_offset: int = 0,
        x_offset: int = 0,
        *args,
    ) -> None:

        display_ascii = display_ascii.splitlines()
        self.h, self.w = self.stdscr.getmaxyx()  # refresh dims
        ascii_height = len(display_ascii)
        ascii_width = max([len(line) for line in display_ascii])

        match positioning:
            case "center":
                start_y = max((self.h - ascii_height) // 2, 0)
                start_x = max((self.w - ascii_width) // 2, 0)
            case "topcenter":
                start_y = 0
                start_x = max((self.w - ascii_width) // 2, 0)
            case "topright":
                start_y = 0
                start_x = max((self.w - ascii_width), 0)
            case "topleft":
                start_y = 0
                start_x = 0

        start_x, start_y = start_x + x_offset, start_y + y_offset

        # write each line to stdscr
        try:
            for i, line in enumerate(display_ascii):
                self.stdscr.addstr(start_y + i, start_x, line, color_pair)
        except CursesError as e:
            pass

    def render_progress_bar(self, prop: float = 0.0, end_text: str = "", *args):
        self.h, self.w = self.stdscr.getmaxyx()  # refresh dims
        bar_len = self.w - 6 - len(end_text)
        prog: int = int(prop * bar_len)  # number of thingies

        bar: list[str] = ["_"] * bar_len
        bar[:prog] = ["█"] * prog
        bar_disp = "[" + "".join(bar) + "] " + end_text
        try:
            self.stdscr.addstr(self.h - 1, 2, bar_disp, *args)
        except CursesError as e:
            pass

    def timer_loop(
        self,
        duration: int,
        color_pair: int = 0,
        show_elapsed: bool = False,
        title_text: str = " ",
        sub_text: str = " ",
        body_text: str = " ",

    ):
        """
        creates a loop for a timer screen according to set parameters.
        additionally listens for keys for pausing and skipping
        """
        start: float = time.time()  # initialize time
        elapsed: int = 0  # initialize seconds counter
        active: bool = True  # timer state is active or paused

        self.stdscr.clear()
        # render timer
        # idea from https://github.com/joechrisellis/pmatrix
        delta = 0
        lt = start

        force_render = False

        while elapsed < duration:  # go until duration is reached
            # handle keys 
            key = self.stdscr.getch()
            # `p` pause key
            if key == ord("p"):
                active = not active
                if active:
                    self.stdscr.clear()
                    force_render = True
                    start += time.time() - (
                        start + elapsed
                    )  # grab current time to account for pause time
                else:
                    self.stdscr.clear()
                    self.render_ascii_str(
                        pyfiglet.figlet_format("paused", "small"),
                        positioning="center",
                        color_pair=color_pair
                    )
                    self.stdscr.refresh()
            # `shift + S` skip timer 
            if key == ord("S"):
                self.stdscr.clear()
                self.render_ascii_str(
                    pyfiglet.figlet_format("skipped", "small"),
                    positioning="center",
                    color_pair=color_pair
                )
                self.stdscr.refresh()
                time.sleep(0.4)
                break  # skip this timer
            
            # `e` to switch elapsed/remaining 
            if key == ord("e"):
                show_elapsed = not show_elapsed
            
            # `q` to exit the entire program 
            if key == ord("q"):
                exit()
            
            # actual timer rendering 
            if active:
                now = time.time()
                elapsed = round(now - start, 2)  # update with current time
                delta += (now - lt) * 15 # delta accumulates time taken by the last loop cycle
                # multiply by 15, once delta reaches >= 1, render
                lt = now

                # convert elapsed time in seconds to ASCII display
                if show_elapsed:
                    timestamp = time_fmt(elapsed)[:10]
                else:
                    timestamp = time_fmt(round(duration - elapsed, 2) + 1)[:10]

                display_ascii: list[str] = pyfiglet.figlet_format(timestamp, "slant")

                if delta >= 1 or force_render:
                    # conditional rendering
                    self.render_background_random()

                    self.render_ascii_str(title_text, positioning="topleft", color_pair=color_pair)
                    self.render_ascii_str(sub_text, positioning="topright", color_pair=color_pair)
                    self.render_ascii_str(body_text, positioning="center", color_pair=color_pair, y_offset=6)
                    self.render_ascii_str(
                        display_ascii, positioning="center", color_pair=color_pair | curses.A_BOLD
                    )
                    # render progress bar
                    self.render_progress_bar(
                        (elapsed / duration), time_fmt(duration), color_pair
                    )
                    delta -= 1
                    
                    # refresh screen
                    self.stdscr.refresh()
                    force_render = False



    def run(self) -> None:
        """Main timer loop"""
        quote = "'hello' - anonymous"
        curses.curs_set(0)  # hide cursor

        for i in range(self.num_sessions):
            # three focus/rest sessions, then a long break
            ascii_session = pyfiglet.figlet_format(str(i+1)+" ", "small")
            for _ in range(3): 
                # Start focus session ----
                self.timer_loop(
                    self.focus_duration, curses.color_pair(1), self.show_elapsed, FOCUS_TEXT, ascii_session, quote
                )
                play_ding()
                # Start rest ...
                self.timer_loop(
                    self.rest_duration, curses.color_pair(2), self.show_elapsed, REST_TEXT, ascii_session
                )
                play_ding()
            self.timer_loop(
                self.focus_duration, curses.color_pair(1), self.show_elapsed, FOCUS_TEXT, ascii_session, quote
            )

            self.timer_loop(self.long_break_duration, curses.color_pair(3), self.show_elapsed, LB_TEXT, ascii_session)
            play_ding()
def main(stdscr, focus_duration, rest_duration, long_break_duration, num_sessions, bg_type) -> None:
    pomo = CursesPomo(stdscr, focus_duration, rest_duration, long_break_duration, num_sessions, bg_type)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="simple curses pomodoro timer written in python"
    )
    parser.add_argument(
        "-focus",
        type=float,
        default=25,
        help="duration of pomodoro focus period in minutes",
    )
    parser.add_argument(
        "-rest",
        type=float,
        default=5,
        help="duration of pomodoro rest period in minutes",
    )
    parser.add_argument(
        "-longbreak",
        type=float,
        default=20,
        help="duration of the final break in a session"
    )
    parser.add_argument(
        "-sessions", type=int, default=4, help="number of sessions, each consisting of 4 pomodoros"
    )
    parser.add_argument(
        "-bg",
        type=str,
        default="snow",
        help="background: can be 'snow', 'matrix', or 'none'."
    )

    args = parser.parse_args()
    try:
        curses.wrapper(
            main, int(args.focus * 60), int(args.rest * 60), int(args.longbreak * 60), args.sessions, args.bg 
        )
    except KeyboardInterrupt:
        exit()
