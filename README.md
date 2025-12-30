Provides a few helpful scripts to make downloading and extracting The Battle Cats game files.

## Previous extraction process

- Download the apks from APKPure or Uptodown.
- Extract the main bit.
- Run the decrypter contained in <https://codeberg.org/fieryhenry/BCGM-Python/>.

This project aims to provide a few scripts that partially automate this process. Or maybe the point is to generate a minimal bit of code that can do these?

## New extraction process

Where it says 14.7, you can replace that with 14.7.1 or 14.7.0 to get specific sub-versions. Technically putting "14" as the number will also get you the same as "14.7" but that's more a bug I can't be bothered to fix.

- Run the download script for the appropriate version e.g. `python download.py 14.7 en`. This might take a bit. If it fails it will probably tell you to download it yourself.
- Run the simpleapk script. The script assumes the apk file will be of the form `en-14.7.apk` so make sure it's like this. The script will tell you where it's extracting and decrypting data.

Instead of running simpleapk, you could:

- Run the extract script. The script assumes the apk file will be of the form `en-14.7.apk` so make sure it's like this. The script will tell you where it's extracting data.
- Run the decrypt script. The previous step will tell you where it's extracted data to. If you extracted it manually then the script will assume all data is in the assets folder, e.g. `mini-bc-data/data/extracted/en-14.7/assets/DataLocal.pack` will be one file it will try to extract if you did everything using this script.

## Goals

Main goal is just to do the install process with as little code as possible.

- [x] Download APKs.
  - [x] Uptodown: done although a bit brittle
  - [x] APKPure: sort of, requires the cloudscraper library to circumvent anti-abuse measures. Unreliable, see [#1](https://github.com/YTFGolf/mini-bc-data/issues/1).
- [x] Extract APKS
- [x] Decrypt data

## Requirements

- Python (tested on 3.9 and 3.12)
- download: [requests](https://docs.python-requests.org/en/latest/index.html) library
  - To enable downloading from apkpure, you will also need the [cloudscraper](https://pypi.org/project/cloudscraper/) library. This feature is not essential, see [#1](https://github.com/YTFGolf/mini-bc-data/issues/1) for more details.
- decrypt/simpleapk: [pycryptodome](https://pypi.org/project/pycryptodome/) package

## Licensing

This project uses code from <https://codeberg.org/fieryhenry/tbcml> and as such is licensed under the same terms, GPLv3.
