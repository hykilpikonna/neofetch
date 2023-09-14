from __future__ import annotations

import os
from PIL import Image


def get_flags() -> list:
    """
    Gets installed flags

    Returns
    -------
    list
        Alphabetical list of installed flags.

    """
    files = os.listdir('hyfetch/flags')
    files_no_ext = [f.split('.')[0] for f in files]
    files_no_ext.sort()
    return files_no_ext


def get_flag(flag: str, x_len: int, y_len: int, rotation: int = 0) -> Image.Image:
    """
    Opens a flag file, then rotates and resizes it

    Parameters
    ----------
    flag : str
        flag name.
    x_len : int
        width of flag.
    y_len : int
        height of flag.
    rotation : int, optional
        Counterclockwise rotation of the image in degrees. The default is 0.

    Raises
    ------
    error
        Flag is not installed.
    FileNotFoundError
        Flag is not installed.

    Returns
    -------
    img : Image.Image
        RGB image of flag.

    """
    # Get files in the flag directory
    files = os.listdir('hyfetch/flags')
    # Remove file extensions
    files_no_ext = [f.split('.')[0] for f in os.listdir('hyfetch/flags')]
    # Get index of file in list of files without extensions, raise error if it doesn't exist
    try:
        index = files_no_ext.index(flag.lower())
    except ValueError as ex:
        raise FileNotFoundError(f'{flag.lower()} flag does not exist') from ex

    filename = files[index]
    img = Image.open('hyfetch/flags/' + filename).convert('RGB')
    img = img.rotate(rotation, expand=True)
    img = img.resize((x_len, y_len), resample=Image.Resampling.NEAREST)
    return img
