#!/usr/bin/env python3
"""
Create configuration file interactively
"""

from math import ceil
from .color_scale import Scale
from .color_util import clear_screen
from . import constants, termenv
from .models import Config
from .neofetch_util import get_distro_ascii, ascii_size, color, printc, literal_input, recolor_ascii
from .flag_utils import get_flags


class Configure:
    """
    Return a configuration file created interactively.
    Usage: config = Configure().create()
    """

    def __init__(self):
        self.det_bg = termenv.get_background_color()
        self.det_ansi = termenv.detect_ansi_mode()
        asc = get_distro_ascii()
        asc_width = ascii_size(asc)[0]
        if self.det_bg is None or self.det_bg.is_light():
            self.logo = color("&l&bhyfetch&~&L")
        else:
            self.logo = color("&l&bhy&ffetch&~&L")

        self.term_len_min = 2 * asc_width + 4
        self.term_lines_min = 30

        self.title = f'Welcome to {self.logo}! Let\'s set up some colors first.'
        self.option_counter = 1

    def update_title(self, k: str, v: str):
        if not k.endswith(":"):
            k += ':'
        self.title += f"\n&e{self.option_counter}. {k.ljust(30)} &~{v}"
        self.option_counter += 1

    def print_title_prompt(self, prompt: str):
        printc(f'&a{self.option_counter}. {prompt}')

    def select_color_system(self):
        if self.det_ansi == 'rgb':
            return 'rgb', 'Detected color mode'

        clear_screen(self.title)

        scale2 = Scale(['#12c2e9', '#c471ed', '#f7797d'])
        _8bit = [scale2(i / constants.TERM_WIDTH).to_ansi_8bit(False)
                 for i in range(constants.TERM_WIDTH)]
        _rgb = [scale2(i / constants.TERM_WIDTH).to_ansi_rgb(False)
                for i in range(constants.TERM_WIDTH)]

        printc('&f' + ''.join(c + t for c, t in zip(_8bit,
               '8bit Color Testing'.center(constants.TERM_WIDTH))))
        printc('&f' + ''.join(c + t for c, t in zip(_rgb,
               'RGB Color Testing'.center(constants.TERM_WIDTH))))

        print()
        self.print_title_prompt(
            'Which &bcolor system &ado you want to use?')
        printc('(If you can\'t see colors under "RGB Color Testing", please choose 8bit)')
        print()

        return literal_input('Your choice?', ['8bit', 'rgb'], 'rgb'), 'Selected color mode'

    def select_light_dark(self):
        if self.det_bg is not None:
            return self.det_bg.is_light(), 'Detected background color'

        clear_screen(self.title)
        inp = literal_input('2. Is your terminal in &blight mode&~ or &4dark mode&~?',
                            ['light', 'dark'], 'dark')
        return inp == 'light', 'Selected background color'

    def print_flag_row(self, current: list[list[str]]):
        for line in zip(*current):
            printc('  '.join(line))
        print()

    def print_flag_page(self, page: list[list[list[str]]], num_pages: int, page_num: int):
        clear_screen(self.title)
        self.print_title_prompt("Let's choose a flag!")
        printc('Installed flags:')
        print(f'Page: {page_num + 1} of {num_pages}')
        print()
        for i in page:
            self.print_flag_row(i)
        print()

    def select_lightness(self, light_dark, preset):
        clear_screen(self.title)
        self.print_title_prompt("Let's adjust the color brightness!")
        adj = "bright" if constants.GLOBAL_CFG.is_light else "dark"
        printc(
            f'The colors might be a little bit too {adj} for {light_dark} mode.')
        print()

        # Print cats
        num_cols = (constants.TERM_WIDTH //
                    (constants.TEST_ASCII_WIDTH + 2)) or 1
        min_l, max_l = 0.15, 0.85
        ratios = [col / num_cols for col in range(num_cols)]
        ratios = [(r * (max_l - min_l) / 2 + min_l) if constants.GLOBAL_CFG.is_light else (
            (r * (max_l - min_l) + (max_l + min_l)) / 2) for r in ratios]
        lines = [recolor_ascii(constants.TEST_ASCII.replace(
            '{txt}', f'{r * 100:.0f}%'.center(5)), preset, r).split('\n') for r in ratios]

        for line in zip(*lines):
            printc('  '.join(line))

        def_lightness = constants.GLOBAL_CFG.default_lightness(light_dark)

        while True:
            print()
            def_val = int(100 * def_lightness)
            printc(
                f'Which brightness level looks the best? (Default: {def_val}% for {light_dark} mode)')
            lightness = input('> ').strip().lower() or None

            # Parse lightness
            if not lightness or lightness in ['unset', 'none']:
                return def_lightness

            light_val_msg = """&cUnable to parse lightness value, please input it as a decimal or percentage (e.g. 0.5 or 50%)"""

            try:
                lightness = int(
                    lightness[:-1]) / 100 if lightness.endswith('%') else float(lightness)
                assert 0 <= lightness <= 1
                return lightness

            except ValueError:
                printc(light_val_msg)

            except AssertionError:
                printc(light_val_msg)

    def choose_flag(self):
        flags = []
        spacing = max([len(k) for k in get_flags()] +
                      [constants.CONFIGURE_FLAG_WIDTH])
        for name in get_flags():
            flag_lines = '\n'.join(
                constants.CONFIGURE_FLAG_HEIGHT * [' ' * spacing])
            flag_lines = recolor_ascii(
                flag_lines, name, rotation=270, lightness_mode=None, foreground=False).split('\n')
            flags.append([name.center(spacing)] + flag_lines)

        # Calculate flags per row
        flags_per_row = constants.TERM_WIDTH // (spacing + 2)
        row_per_page = max(
            1, (constants.TERM_HEIGHT - 13) // (constants.CONFIGURE_FLAG_HEIGHT + 2))
        num_pages = ceil(len(flags) / (flags_per_row * row_per_page))

        pages = []
        for _ in range(num_pages):
            page = []
            for _ in range(row_per_page):
                page.append(flags[:flags_per_row])
                flags = flags[flags_per_row:]
                if not flags:
                    break
            pages.append(page)
        page = 0
        while True:
            self.print_flag_page(
                pages[page], num_pages, page)

            tmp = recolor_ascii('preset', 'rainbow', rotation=90)
            opts = get_flags()
            if page < num_pages - 1:
                opts.append('next')
            if page > 0:
                opts.append('prev')
            print(
                "Enter 'next' to go to the next page and 'prev' to go to the previous page.")
            preset = literal_input(
                f'Which {tmp} do you want to use? ', opts, 'rainbow', show_ops=False)
            if preset == 'next':
                page += 1
            elif preset == 'prev':
                page -= 1
            else:
                self.update_title(
                    'Selected flag', recolor_ascii(preset, preset, rotation=270))
                return preset

    def run(self) -> Config:
        """
        Create config interactively

        Returns
        -------
        Config
            Config object (automatically stored).

        """
        clear_screen(self.title)

        ##############################
        # 0. Check term size

        if constants.TERM_WIDTH < self.term_len_min or constants.TERM_HEIGHT < self.term_lines_min:
            printc(f'&cWarning: Your terminal is too small ({constants.TERM_WIDTH} * {constants.TERM_HEIGHT}). \n'
                   f'Please resize it to at least ({self.term_len_min} * {self.term_lines_min}) for a better experience.')
            input('Press enter to ignore...')

        ##############################
        # 1. Select color system

        # Override global color mode
        color_mode, ttl = self.select_color_system()
        constants.GLOBAL_CFG.color_mode = color_mode
        self.update_title(ttl, color_mode)

        ##############################
        # 2. Select light/dark mode

        constants.GLOBAL_CFG.is_light, ttl = self.select_light_dark()
        light_dark = 'light' if constants.GLOBAL_CFG.is_light else 'dark'
        self.update_title(ttl, light_dark)

        ##############################
        # 3. Choose preset
        # Create flags = [[lines]]

        preset = self.choose_flag()

        #############################
        # 4. Dim/lighten colors

        lightness = self.select_lightness(light_dark, preset)
        self.update_title('Selected Brightness', f"{lightness:.2f}")

        # Create config
        clear_screen(self.title)
        config = Config(preset, constants.GLOBAL_CFG.color_mode,
                        light_dark, lightness)

        # Save config
        print()
        save = literal_input('Save config?', ['y', 'n'], 'y')
        if save == 'y':
            config_path = config.save()
            print('Configuration file saved at ' + str(config_path)+'\n')

        return config
