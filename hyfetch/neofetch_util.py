from __future__ import annotations

import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from subprocess import check_output
from tempfile import TemporaryDirectory
from typing import Iterable

import pkg_resources

from .color_util import RGB, color, printc
from .constants import GLOBAL_CFG, MINGIT_URL, IS_WINDOWS
from .distros import distro_detector
from .types import BackendLiteral

from .flag_utils import get_flag

RE_NEOFETCH_COLOR = re.compile('\\${c[0-9]}')


def literal_input(prompt: str, options: Iterable[str], default: str, show_ops: bool = True) -> str:
    """
    Ask the user to provide an input among a list of options

    :param prompt: Input prompt
    :param options: Options
    :param default: Default option
    :param show_ops: Show options
    :return: Selection
    """
    options = list(options)
    lows = [o.lower() for o in options]

    if show_ops:
        op_text = '|'.join([f'&l&n{o}&L&N' if o == default else o for o in options])
        printc(f'{prompt} ({op_text})')
    else:
        printc(f'{prompt} (default: {default})')

    def find_selection(sel: str):
        if not sel:
            return None

        # Find exact match
        if sel in lows:
            return options[lows.index(sel)]

        # Find starting abbreviation
        for i, op in enumerate(lows):
            if op.startswith(sel):
                return options[i]

        return None

    selection = input('> ').lower() or default
    while not find_selection(selection):
        print(f'Invalid selection! {selection} is not one of {"|".join(options)}')
        selection = input('> ').lower() or default

    print()

    return find_selection(selection)


def ascii_size(asc: str) -> tuple[int, int]:
    """
    Get distro ascii width, height ignoring color code

    :param asc: Distro ascii
    :return: Width, Height
    """
    return max(len(line) for line in re.sub(RE_NEOFETCH_COLOR, '', asc).split('\n')), len(asc.split('\n'))


def normalize_ascii(asc: str) -> str:
    """
    Make sure every line is the same width
    """
    w = ascii_size(asc)[0]
    return '\n'.join(line.ljust(w) for line in asc.split('\n'))


def fill_starting(asc: str) -> str:
    """
    Fill the missing starting placeholders.

    E.g. "${c1}...\n..." -> "${c1}...\n${c1}..."
    """
    new = []
    last = ''
    for line in asc.split('\n'):
        new.append(last + line)

        # Line has color placeholders
        matches = RE_NEOFETCH_COLOR.findall(line)
        if len(matches) > 0:
            # Get the last placeholder for the next line
            last = matches[-1]

    return '\n'.join(new)


def recolor_ascii(asc: str, flag: str, lightness: float = 0.5, lightness_mode: str = "set_dl",
                  foreground: bool = True, rotation: int = 0,
                  term: str = 'dark') -> str:
    """
    Use the color alignment to recolor an ascii art
    """
    asc = fill_starting(asc)

    # Remove existing colors
    asc = re.sub(RE_NEOFETCH_COLOR, '', asc)

    # Get image array
    lines = asc.split('\n')
    x_len = max(len(line) for line in lines)
    y_len = len(lines)
    asc = normalize_ascii(asc)
    img = get_flag(flag, x_len, y_len, rotation=rotation)
    # Bold
    new_asc = color("&l\033[1m")
    current_color = ''
    x = 0
    y = 0
    # Color
    if lightness_mode == "set_dl":
        if term.lower() == 'dark':
            at_least, at_most = (True, None)
        else:
            at_least, at_most = (None, True)

    for char in asc:
        if char == '\n':
            # Clear
            new_asc += color('&~&*')
            new_asc += '\n'
            new_asc += color("&l\033[1m")
            current_color = ''
            continue
        if x == x_len:
            x = 0
            y += 1

        rgb_color = RGB(*img.getpixel((x, y)))
        if lightness_mode == "set_dl":
            rgb_color = rgb_color.set_light(lightness, at_least, at_most)
        elif lightness_mode == "set_raw":
            rgb_color = rgb_color.set_light(lightness, None, None)
        elif lightness_mode == "scale":
            rgb_color = rgb_color.lighten(lightness)
        elif lightness_mode is None:
            pass
        else:
            raise NotImplementedError(
                "lightness_mode must be either set_dl, set_raw, scale, or None")

        color_str = rgb_color.to_ansi(foreground=foreground)

        if color_str != current_color:
            new_asc += color_str
            current_color = color_str
        new_asc += char

        x += 1

    # Unbold + clear
    new_asc += color("&l\033[22m")
    new_asc += color('&~&*')
    return new_asc


def if_file(f: str | Path) -> Path | None:
    """
    Return the file if the file exists, or return none. Useful for chaining 'or's
    """
    f = Path(f)
    if f.is_file():
        return f
    return None


def get_command_path() -> str:
    """
    Get the absolute path of the neofetch command

    :return: Command path
    """
    cmd_path = pkg_resources.resource_filename(__name__, 'scripts/neowofetch')

    # Windows doesn't support symbolic links, but also I can't detect symbolic links... hard-code it here for now.
    if IS_WINDOWS:
        pkg = Path(__file__).parent
        pth = (shutil.which("neowofetch") or
               if_file(cmd_path) or
               if_file(pkg / 'scripts/neowofetch') or
               if_file(pkg.parent / 'neofetch') or
               if_file(Path(cmd_path).parent.parent.parent / 'neofetch'))

        if not pth:
            printc("&cError: Neofetch script cannot be found")
            sys.exit(127)

        return str(pth)

    return cmd_path


def ensure_git_bash() -> Path:
    """
    Ensure git bash installation for windows

    :returns git bash path
    """
    if IS_WINDOWS:
        # Find installation in default path
        def_path = Path(r'C:\Program Files\Git\bin\bash.exe')
        if def_path.is_file():
            return def_path

        # Detect third-party git.exe in path
        git_exe = shutil.which("bash") or shutil.which("git.exe") or shutil.which("git")
        if git_exe is not None:
            pth = Path(git_exe).parent
            if (pth / r'bash.exe').is_file():
                return pth / r'bash.exe'
            if (pth / r'bin\bash.exe').is_file():
                return pth / r'bin\bash.exe'

        # Find installation in PATH (C:\Program Files\Git\cmd should be in path)
        pth = (os.environ.get('PATH') or '').lower().split(';')
        pth = [p for p in pth if p.endswith(r'\git\cmd')]
        if pth:
            return Path(pth[0]).parent / r'bin\bash.exe'

        # Previously downloaded portable installation
        path = Path(__file__).parent / 'min_git'
        pkg_path = path / 'package.zip'
        if path.is_dir():
            return path / r'bin\bash.exe'

        # No installation found, download a portable installation
        print('Git installation not found. Git is required to use HyFetch/neofetch on Windows')
        if literal_input('Would you like to install a minimal package for Git? (if no is selected colors almost certainly won\'t work)', ['yes', 'no'], 'yes', False) == 'yes':
            print('Downloading a minimal portable package for Git...')
            from urllib.request import urlretrieve
            urlretrieve(MINGIT_URL, pkg_path)
            print('Download finished! Extracting...')
            with zipfile.ZipFile(pkg_path, 'r') as zip_ref:
                zip_ref.extractall(path)
            print('Done!')
            return path / r'bin\bash.exe'
        sys.exit()


def check_windows_cmd():
    """
    Check if this script is running under cmd.exe. If so, launch an external window with git bash
    since cmd doesn't support RGB colors.
    """
    if IS_WINDOWS:
        import psutil
        # TODO: This line does not correctly identify cmd prompts...
        if psutil.Process(os.getppid()).name().lower().strip() == 'cmd.exe':
            print("cmd.exe doesn't support RGB colors, restarting in MinTTY...")
            cmd = f'"{ensure_git_bash().parent.parent / "usr/bin/mintty.exe"}" -s 110,40 -e python -m hyfetch --ask-exit'
            os.system(cmd)
            sys.exit(0)


def run_neofetch_cmd(args: str, pipe: bool = False) -> str | None:
    """
    Run neofetch command
    """
    if platform.system() != 'Windows':
        full_cmd = ['/usr/bin/env', 'bash', get_command_path(), *shlex.split(args)]

    else:
        cmd = get_command_path().replace("\\", "/").replace("C:/", "/c/")
        args = args.replace('\\', '/').replace('C:/', '/c/')

        full_cmd = [ensure_git_bash(), '-c', f"'{cmd}' {args}"]
    # print(full_cmd)

    if pipe:
        return check_output(full_cmd).decode().strip()
    subprocess.run(full_cmd)


def get_distro_ascii(distro: str | None = None) -> str:
    """
    Get the distro ascii of the current distro. Or if distro is specified, get the specific distro's
    ascii art instead.

    :return: Distro ascii
    """
    if not distro and GLOBAL_CFG.override_distro:
        distro = GLOBAL_CFG.override_distro
    if GLOBAL_CFG.debug:
        print(distro)
        print(GLOBAL_CFG)

    # Try new pure-python detection method
    det = distro_detector.detect(distro or get_distro_name())
    if det is not None:
        return normalize_ascii(det.ascii)

    if GLOBAL_CFG.debug:
        printc(f"&cError: Cannot find distro {distro}")

    # Old detection method that calls neofetch
    cmd = 'print_ascii'
    if distro:
        cmd += f' --ascii_distro {distro}'

    asc = run_neofetch_cmd(cmd, True)

    # Unescape backslashes here because backslashes are escaped in neofetch for printf
    asc = asc.replace('\\\\', '\\')

    return normalize_ascii(asc)


def get_distro_name():
    return run_neofetch_cmd('ascii_distro_name', True)


def run(asc: str, backend: BackendLiteral, args: str = ''):
    if backend == "neofetch":
        return run_neofetch(asc, args)
    if backend == "fastfetch":
        return run_fastfetch(asc, args)
    if backend == "fastfetch-old":
        return run_fastfetch(asc, args, legacy=True)
    if backend == "qwqfetch":
        return run_qwqfetch(asc, args)


def run_qwqfetch(asc: str, args: str = ''):
    """
    Run neofetch with colors

    :param preset: Color palette
    :param alignment: Color alignment settings
    """
    asc = asc.replace('\\', '\\\\')

    # call qwqfetch to print string
    try:
        import qwqfetch
        # distro_detector only return a bash variable
        # so we use qwqfetch builtin distro detector
        print(qwqfetch.get_ascres(asc))  
    except ImportError as e:  # module not found etc
        print("qwqfetch is not installed. Install it by executing:")  # use print to output hint directly
        print("pip install git+https://github.com/nexplorer-3e/qwqfetch")  # TODO: public repo
        raise e

def run_neofetch(asc: str, args: str = ''):
    """
    Run neofetch with colors

    :param asc: Ascii art
    :param args: Additional arguments to pass to neofetch
    """
    # Escape backslashes here because backslashes are escaped in neofetch for printf
    asc = asc.replace('\\', '\\\\')

    # Write temp file
    with TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        path = tmp_dir / 'ascii.txt'
        path.write_text(asc)

        # Call neofetch with the temp file
        if args:
            args = ' ' + args
        run_neofetch_cmd(f'--ascii --source {path.absolute()} --ascii-colors' + args)


def run_fastfetch(asc: str, args: str = '', legacy: bool = False):
    """
    Run neofetch with colors

    :param asc: Ascii art
    :param args: Additional arguments to pass to fastfetch
    :param legacy: Set true when using fastfetch < 1.8.0
    """
    # Write temp file
    with TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        path = tmp_dir / 'ascii.txt'
        path.write_text(asc)

        # Call fastfetch with the temp file
        proc = subprocess.run(['fastfetch', '--raw' if legacy else '--file-raw', path.absolute(), *shlex.split(args)])
        if proc.returncode == 144:
            printc("&6Error code 144 detected: Please upgrade fastfetch to >=1.8.0 or use the 'fastfetch-old' backend")


def get_fore_back(distro: str | None = None) -> tuple[int, int] | None:
    """
    Get recommended foreground-background configuration for distro, or None if the distro ascii is
    not suitable for fore-back configuration.

    :return:
    """
    if not distro and GLOBAL_CFG.override_distro:
        distro = GLOBAL_CFG.override_distro
    if not distro:
        distro = get_distro_name().lower()
    distro = distro.lower().replace(' ', '-')
    for k, v in fore_back.items():
        if distro.startswith(k.lower()):
            return v
    return None


# Foreground-background recommendation
fore_back = {
    'fedora': (2, 1),
    'kubuntu': (2, 1),
    'lubuntu': (2, 1),
    'xubuntu': (2, 1),
    'ubuntu-cinnamon': (2, 1),
    'ubuntu-kylin': (2, 1),
    'ubuntu-mate': (2, 1),
    'ubuntu-studio': (2, 1),
    'ubuntu-sway': (2, 1),
}
