#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import json
import argparse
import datetime
import traceback
import importlib
from pathlib import Path
from .__version__ import VERSION
from . import neofetch_util, pride_month, constants
from .models import Config
from .neofetch_util import get_distro_ascii, color, recolor_ascii, ensure_git_bash, check_windows_cmd
from .flag_utils import get_flags
from .create_config import Configure


def check_config(path) -> Config:
    """
    Check if the configuration exists. Return the config object if it exists. If not, call the
    config creator

    :return: Config object
    """
    if path.is_file():
        try:
            return Config.from_dict(json.loads(path.read_text('utf-8')))
        except KeyError:
            return Configure().run()

    return Configure().run()


def create_parser() -> argparse.ArgumentParser:
    # Create CLI
    hyfetch = color('&l&bhyfetch&~&L')
    parser = argparse.ArgumentParser(description=color(
        f'{hyfetch} - neofetch with flags <3'), prog="hyfetch")

    parser.add_argument('-c', '--config', action='store_true',
                        help=color('Configure hyfetch'))
    parser.add_argument('-C', '--config-file', dest='config_file',
                        default=constants.CONFIG_PATH, help='Use another config file')
    parser.add_argument('-p', '--preset', help='Use preset',
                        choices=get_flags())
    parser.add_argument('-m', '--mode', help='Color mode',
                        choices=['8bit', 'rgb'])
    parser.add_argument('-b', '--backend', help='Choose a *fetch backend',
                        choices=['qwqfetch', 'neofetch', 'fastfetch', 'fastfetch-old'])
    parser.add_argument(
        '--args', help='Additional arguments pass-through to backend')
    parser.add_argument('--c-scale', dest='scale',
                        help='Lighten colors by a multiplier', type=float)
    parser.add_argument('--c-set-l', dest='light',
                        help='Set lightness value of the colors', type=float)
    parser.add_argument('--c-overlay', action='store_true', dest='overlay',
                        help='Use experimental overlay color adjusting instead of HSL lightness')
    parser.add_argument('-V', '--version', dest='version',
                        action='store_true', help='Check version')
    parser.add_argument('--june', action='store_true',
                        help='Show pride month easter egg')
    parser.add_argument('--debug', action='store_true', help='Debug mode')

    parser.add_argument('-d', '--distro', '--test-distro',
                        dest='distro', help='Test for a specific distro')
    parser.add_argument(
        '--ascii-file', help='Use a specific file for the ascii art')

    # Hidden debug arguments
    # --test-print: Print the ascii distro and exit
    parser.add_argument('--test-print', action='store_true',
                        help=argparse.SUPPRESS)
    # --ask-exit: Ask for input before exiting
    parser.add_argument('--ask-exit', action='store_true',
                        help=argparse.SUPPRESS)

    return parser


def run():
    # Optional: Import readline
    try:
        readline = importlib.import_module("readline")
    except ModuleNotFoundError:
        pass

    # On Windows: Try to fix color rendering if not in git bash
    if constants.IS_WINDOWS:
        import colorama
        colorama.just_fix_windows_console()

    parser = create_parser()
    args = parser.parse_args()

    # Use a custom distro
    constants.GLOBAL_CFG.override_distro = args.distro
    constants.GLOBAL_CFG.use_overlay = args.overlay

    if args.version:
        print(f'Version is {VERSION}')
        return

    # Ensure git bash for windows
    ensure_git_bash()
    check_windows_cmd()

    if args.debug:
        constants.GLOBAL_CFG.debug = True

    if args.test_print:
        print(get_distro_ascii())
        return

    # Check if user provided alternative config path
    if not args.config_file == constants.CONFIG_PATH:
        args.config_file = Path(os.path.abspath(args.config_file))

        # If provided file does not exist use default config
        if not args.config_file.is_file():
            args.config_file = constants.CONFIG_PATH

    # Load config or create config
    config = Configure().run() if args.config else check_config(args.config_file)

    # Check if it's June (pride month)
    now = datetime.datetime.now()
    june_path = constants.CACHE_PATH / f'animation-displayed-{now.year}'
    if now.month == 6 and now.year not in config.pride_month_shown and not june_path.is_file() and os.isatty(sys.stdout.fileno()):
        args.june = True

    if args.june and not config.pride_month_disable:
        pride_month.play_animation()
        print()
        print("Happy pride month!")
        print("(You can always view the animation again with `hyfetch --june`)")
        print()

        if not june_path.is_file():
            june_path.parent.mkdir(parents=True, exist_ok=True)
            june_path.touch()

    # Use a custom distro
    constants.GLOBAL_CFG.override_distro = args.distro or config.distro

    # Param overwrite config
    if args.preset:
        config.preset = args.preset
    if args.mode:
        config.mode = args.mode
    if args.backend:
        config.backend = args.backend
    if args.args:
        config.args = args.args

    # Override global color mode
    constants.GLOBAL_CFG.color_mode = config.mode
    constants.GLOBAL_CFG.is_light = config.light_dark == 'light'

    # Get preset
    flag = config.preset

    # Run
    try:
        asc = get_distro_ascii() if not args.ascii_file else Path(
            args.ascii_file).read_text("utf-8")

        if args.scale:
            if args.scale > 0:
                mode = ("scale", args.scale)
            else:
                raise ValueError("Color scale must be larger than 0")
        elif args.light:
            mode = ("set_raw", args.light)
        else:
            mode = (
                "set_dl", config.lightness or constants.GLOBAL_CFG.default_lightness())

        asc = recolor_ascii(
            asc, flag, lightness=mode[1], lightness_mode=mode[0])
        neofetch_util.run(asc, config.backend, config.args or '')
    except Exception as ex:
        print(f'Error: {ex}')
        traceback.print_exc()

    if args.ask_exit:
        input('Press any key to exit...')
