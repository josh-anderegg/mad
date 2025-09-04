from package import BASE_DIR
import glob
from datetime import datetime
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
DATABASE_PATH = None
WORKERS = None
YEAR = None


def parse_args(args):
    global DATABASE_PATH, WORKERS, YEAR
    DATABASE_PATH = args.path
    WORKERS = args.workers
    YEAR = args.year


def get_all_metadata():
    global DATABASE_PATH, WORKERS, YEAR
    with open(f"{DATABASE_PATH}/tiles.txt") as f:
        all_tiles = f.read().splitlines()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(get_metadata, tile, YEAR) for tile in all_tiles]
        for _ in tqdm(as_completed(futures), total=len(futures), desc="Downloading metadata"):
            pass


def get_metadata(name, year):
    global DATABASE_PATH
    subprocess.run(
        [f"{BASE_DIR}/package/s3_get_metadata.sh", name, str(DATABASE_PATH), str(year)],
    )


def collect_logs():
    global DATABASE_PATH
    now = datetime.now()
    timestamp = now.strftime("%Y_%m_%d_%H_%M_%S")
    log_files = sorted(glob.glob(f"{DATABASE_PATH}/*_indexing.tlog"))
    with open(os.path.join(DATABASE_PATH, f"{timestamp}_indexing.log"), "w") as outfile:
        for fname in log_files:
            with open(fname) as infile:
                outfile.write(infile.read())

    for fname in log_files:
        os.remove(fname)


def run(args):
    parse_args(args)
    get_all_metadata()
    collect_logs()
