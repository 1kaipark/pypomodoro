import time
import pyfiglet
import curses
import argparse

from playsound import playsound

from pathlib import Path
import threading

from typing import Literal

FOCUS_TEXT: str = pyfiglet.figlet_format("focus...", "small")
REST_TEXT: str = pyfiglet.figlet_format("take a break...", "small")

DING_SFX: str = str(Path(__file__).parent / "assets/ding.wav")


def time_fmt(secs: int, display_hours: bool = False) -> str:
    """Returns base-60 time string in format 00:00.00"""
    h, rm = secs // 3600, secs % 3600
    m = rm // 60
    s = rm % 60
    disp = [str(v).zfill(2) for v in [h, m, s]]

    if display_hours:
        return "{}:{}:{}".format(*disp)
    else:
        return "{}:{}".format(*disp[1:])


class CursesPomo(object):
    def __init__(
        self,
        stdscr,
        focus_duration: int = 25 * 60,
        rest_duration: int = 5 * 60,
        num_sessions: int = 2,
        show_elapsed: bool = False
    ):
        self.stdscr = stdscr

        self.focus_duration = focus_duration
        self.rest_duration = rest_duration
        # session counter
        self.num_sessions = num_sessions
        self.show_elapsed = show_elapsed

        self.h, self.w = self.stdscr.getmaxyx()

        # initialize colors
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_RED, -1)
        curses.init_pair(2, curses.COLOR_GREEN, -1)
        curses.init_pair(3, curses.COLOR_MAGENTA, -1)

        self.run()

    def add_ascii_str(
        self,
        display_ascii: str,
        positioning: Literal["center", "topcenter", "topright", "topleft"] = "center",
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

        # write each line to stdscr
        for i, line in enumerate(display_ascii):
            self.stdscr.addstr(start_y + i, start_x, line, *args)

    def render_progress_bar(self, prop: float = 0.0, end_text: str = "", *args):
        self.h, self.w = self.stdscr.getmaxyx()  # refresh dims
        bar_len = self.w - 6 - len(end_text)
        prog: int = int(prop * bar_len)  # number of thingies

        bar: list[str] = ["_"] * bar_len
        bar[:prog] = ["█"] * prog
        bar_disp = "[" + "".join(bar) + "] " + end_text
        self.stdscr.addstr(self.h - 1, 2, bar_disp, *args)

    def play_ding(self):
        threading.Thread(target=playsound, args=(DING_SFX,), daemon=True).start()

    def timer_loop(
        self,
        duration: int,
        text: str,
        color_pair: int,
        show_elapsed: bool = False,
    ):
        start: float = time.time()  # initialize time
        elapsed: int = 0  # initialize seconds counter

        while elapsed < duration:  # go until duration is reached
            self.stdscr.clear()
            self.add_ascii_str(text, "topleft", color_pair)
            time.sleep(1)

            # update elapsed with current time
            current_time: float = time.time()
            elapsed = int(current_time - start)
            # convert elapsed time in seconds to ASCII display

            if show_elapsed:
                timestamp = time_fmt(elapsed)
            else:
                timestamp = time_fmt(duration - elapsed)

            display_ascii: list[str] = pyfiglet.figlet_format(timestamp, "slant")

            # render time
            self.add_ascii_str(display_ascii, "center", color_pair | curses.A_BOLD)

            # render progress bar
            self.render_progress_bar(
                (elapsed / duration), time_fmt(duration), color_pair
            )

            # refresh screen
            self.stdscr.refresh()

    def run(self) -> None:
        """Main timer loop"""
        curses.curs_set(0)  # hide cursor

        for _ in range(self.num_sessions):
            # Start focus session ----
            self.timer_loop(self.focus_duration, FOCUS_TEXT, curses.color_pair(1), self.show_elapsed)
            self.play_ding()
            # Start rest ...
            self.timer_loop(self.rest_duration, REST_TEXT, curses.color_pair(2), self.show_elapsed)


def main(stdscr, focus_duration, rest_duration, num_sessions, show_elapsed) -> None:
    pomo = CursesPomo(stdscr, focus_duration, rest_duration, num_sessions, show_elapsed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="simple curses pomodoro timer written in python"
    )
    parser.add_argument(
        "-focus",
        type=int,
        default=25,
        help="duration of pomodoro focus period in minutes",
    )
    parser.add_argument(
        "-rest", type=int, default=5, help="duration of pomodoro rest period in minutes"
    )
    parser.add_argument(
        "-sessions", type=int, default=4, help="number of focus/rest sessions"
    )
    parser.add_argument(
        "--show_elapsed",
        default=False,
        action="store_true",
        help="show elapsed time in main clock, rather than time remaining",
    )

    args = parser.parse_args()
    curses.wrapper(main, args.focus * 60, args.rest * 60, args.sessions, args.show_elapsed)
