"""
Type Utilities
"""

from typing_extensions import Literal

AnsiMode = Literal['default', 'ansi', '8bit', 'rgb']
LightDark = Literal['light', 'dark']
BackendLiteral = Literal["neofetch", "fastfetch"]
