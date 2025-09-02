import os
from package import BASE_DIR
import requests
import zipfile
import tempfile
import shutil
from io import BytesIO


def create_folder_structure():
    os.makedirs(BASE_DIR / 'data', exist_ok=True)
    os.makedirs(BASE_DIR / 'data/clusters', exist_ok=True)
    os.makedirs(BASE_DIR / 'data/geometries', exist_ok=True)
    os.makedirs(BASE_DIR / 'data/temp', exist_ok=True)
    os.makedirs(BASE_DIR / 'outputs', exist_ok=True)


def download_and_unzip(url, extract_to, name):
    response = requests.get(url)
    response.raise_for_status()

    final_folder = extract_to / name
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(tmpdir)

        if os.path.exists(final_folder):
            shutil.rmtree(final_folder)

        extracted_items = os.listdir(tmpdir)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(tmpdir, extracted_items[0])):
            shutil.move(os.path.join(tmpdir, extracted_items[0]), final_folder)
        else:
            shutil.copytree(tmpdir, final_folder)


def download_datasets():
    maus_link = "https://download.pangaea.de/dataset/942325/files/global_mining_polygons_v2.gpkg"
    regions_link = "https://storage.googleapis.com/teow2016/Ecoregions2017.zip"
    countries_link = "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_0_countries.zip"

    response = requests.get(maus_link, stream=True)
    response.raise_for_status()
    with open(BASE_DIR / "data/geometries/maus/global_mining_polygons_v2.gpkg", 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    download_and_unzip(regions_link, BASE_DIR / 'data/geometries', ".")
    download_and_unzip(countries_link, BASE_DIR / 'data/geometries', ".")


def run(args):
    if args.verbose:
        print("Creating folder structure")
    create_folder_structure()
    if not args.minimal:
        download_datasets()
    elif args.verbose:
        print("Skipped downlading datasets")
