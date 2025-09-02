from pathlib import Path
import string
import random
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
OUTPUT_DIR = BASE_DIR / 'outputs'
RANDOM_SYMBOLS = string.ascii_letters + string.digits


def random_seed():
    return ''.join(random.choices(RANDOM_SYMBOLS, k=32))
