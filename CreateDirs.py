import os
import shutil
import random


def fill_dir(base_path, years, months, photos_path, clearDir=False):  # Sett cleardir til true om du vil tømme mappene
    photo_files = [f for f in os.listdir(photos_path) if os.path.isfile(os.path.join(photos_path, f))]

    for year in years:
        year_path = os.path.join(base_path, str(year))
        os.makedirs(year_path, exist_ok=True)

        for month in months:
            month_path = os.path.join(year_path, month)
            if clearDir:
                shutil.rmtree(month_path)
                continue
            os.makedirs(month_path, exist_ok=True)

            numPhotos = random.randint(1, len(photo_files))
            copyPhotos = random.sample(photo_files, numPhotos)

            for photo in copyPhotos:
                src = os.path.join(photos_path, photo)
                dest = os.path.join(month_path, photo)
                shutil.copy(src, dest)


years = [2025, 2024, 2023, 2022]
months = ['Jan', 'Feb', 'Mar', 'Apr']

test_photos_path = './TestPhotos'

google_base_path = './Google'
onedrive_base_path = './OneDrive'

fill_dir(google_base_path, years, months, test_photos_path)
fill_dir(onedrive_base_path, years, months, test_photos_path)
