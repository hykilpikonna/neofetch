from PIL import Image
import numpy as np
import os


def get_flags() -> list:
    files = os.listdir('hyfetch/flags')
    files_no_ext = [f.split('.')[0] for f in os.listdir('hyfetch/flags')]
    return files_no_ext


def get_array(flag: str, x_len: int, y_len: int, rotation: int = 0) -> np.array:
    """
    Open the flag file, resize it, and return it as an array of size y * x * 3
    """

    # Get files in the flag directory
    files = os.listdir('hyfetch/flags')
    # Remove file extensions
    files_no_ext = [f.split('.')[0] for f in os.listdir('hyfetch/flags')]

    # Get index of file in list of files without extensions, raise error if it doesn't exist
    try:
        index = files_no_ext.index(flag)
    except ValueError:
        raise FileNotFoundError(f'{flag} flag does not exist')

    filename = files[index]
    im = Image.open('hyfetch/flags/' + filename).convert('RGB')
    im = im.rotate(rotation, expand=True)
    # +1 to account for newlines
    im = im.resize((x_len + 1, y_len), resample=Image.Resampling.NEAREST)
    arr = np.array(im)
    return arr
