from __future__ import annotations

from . import main
from .color_util import printc

if __name__ == '__main__':
    try:
        main.run()
    except KeyboardInterrupt:
        printc('&cThe program is interrupted by ^C, exiting...')
        exit(0)
