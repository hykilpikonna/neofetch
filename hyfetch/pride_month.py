import sys
import math
import select
import importlib
from time import sleep

from hyfetch.color_util import RGB, color, printc
from . import constants
from .flag_utils import get_flag

if constants.IS_WINDOWS:
    msvcrt = importlib.import_module("msvcrt")

text = r"""
.======================================================.
| .  .              .__       .     .  .       , .   | |
| |__| _.._ ._   .  [__)._.* _| _   |\/| _ ._ -+-|_  | |
| |  |(_][_)[_)\_|  |   [  |(_](/,  |  |(_)[ ) | [ ) * |
|        |  |  ._|                                     |
'======================================================'""".strip("\n")
notice = "Press enter to continue"
text_lines = text.split("\n")
text_height = len(text_lines)
text_width = len(text_lines[0])
frame_delay = 0.1
text_start_y = constants.TERM_HEIGHT // 2 - text_height // 2
text_end_y = text_start_y + text_height
text_start_x = constants.TERM_WIDTH // 2 - text_width // 2
text_end_x = text_start_x + text_width
notice_start_x = constants.TERM_WIDTH - len(notice) - 1
notice_end_x = constants.TERM_WIDTH - 1
notice_y = constants.TERM_HEIGHT - 1
flag_im = get_flag('rainbow', constants.TERM_WIDTH, constants.TERM_HEIGHT)


def key_pressed():
    if constants.IS_WINDOWS:
        return msvcrt.kbhit()  # Non-blocking check for key press
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])


def play_animation():
    frame = 0

    def draw_frame(frame):
        buf = ""
        overlay = False
        # Loop over the height
        for y_pos in range(constants.TERM_HEIGHT):
            current_color = ''
            # Loop over the width
            y_text = text_start_y <= y_pos < text_end_y
            border = int(not y_pos in (text_start_y, text_end_y - 1)) + 1
            x_switch_pts = (text_start_x - border, text_end_x +
                            border, notice_start_x - 1, notice_end_x + 1)
            for x_pos in range(constants.TERM_WIDTH):
                # If it's a switching point
                if x_pos in x_switch_pts:
                    # Print the color at the current frame
                    overlay = (y_text and text_start_x - border <= x_pos < text_end_x + border) or (
                        y_pos == notice_y and notice_start_x - 1 <= x_pos < notice_end_x + 1)

                # Add flag
                diff = int(4*math.sin(-2 * math.tau *
                           (x_pos / constants.TERM_WIDTH) + frame))

                rgb_color = RGB(
                    *flag_im.getpixel((x_pos, (y_pos + diff) % constants.TERM_HEIGHT)))

                if overlay:
                    rgb_color = rgb_color.overlay(RGB(0, 0, 0), 0.5)

                if rgb_color != current_color:
                    buf += rgb_color.to_ansi(foreground=False)
                    current_color = rgb_color

                # If text should be printed, print text
                if y_text and text_start_x <= x_pos < text_end_x:
                    # Add white background
                    buf += text_lines[y_pos -
                                      text_start_y][x_pos - text_start_x]
                elif y_pos == notice_y and notice_start_x <= x_pos < notice_end_x:
                    buf += notice[x_pos - notice_start_x]
                else:
                    buf += ' '

                x_pos += 1
            # New line if it isn't the last line
            if y_pos != constants.TERM_HEIGHT - 1:
                buf += color('&r\n')

        print(buf, end='', flush=True)

    try:
        while True:
            # Clear the screen
            print("\033[2J\033[H", end="")
            draw_frame(frame)
            frame += 1
            sleep(frame_delay)

            if key_pressed():
                break
    except KeyboardInterrupt:
        pass

    # Clear the screen
    printc("&r")
    print("\033[2J\033[H", end="", flush=True)


if __name__ == '__main__':
    play_animation()
