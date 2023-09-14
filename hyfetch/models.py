from dataclasses import dataclass, field
from pathlib import Path
from .constants import CONFIG_PATH
from .serializer import json_stringify, from_dict
from .types import AnsiMode, LightDark, BackendLiteral


@dataclass
class Config:
    """
    Configuration object
    """
    preset: str
    mode: AnsiMode
    light_dark: LightDark = 'dark'
    lightness: float | None = None
    backend: BackendLiteral = "neofetch"
    args: str | None = None
    distro: str | None = None

    # This is deprecated, see issue #136
    pride_month_shown: list[int] = field(default_factory=list)
    pride_month_disable: bool = False

    @classmethod
    def from_dict(cls, _dict: dict):
        return from_dict(cls, _dict)

    def save(self) -> Path:
        """
        Save to path

        Returns
        -------
        Path
            Path of config file.

        """
        CONFIG_PATH.parent.mkdir(exist_ok=True, parents=True)
        CONFIG_PATH.write_text(json_stringify(self, indent=4), 'utf-8')
        return CONFIG_PATH
