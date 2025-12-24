Provides a few helpful scripts to make downloading and extracting The Battle Cats game files.

## Current extraction process

- Download the apks from APKPure or Uptodown.
- Extract the main bit.
- Run the decrypter contained in <https://codeberg.org/fieryhenry/BCGM-Python/>.

This project aims to provide a few scritps that partially automate this process.

## Goals

- [ ] Download APKs.
  - [x] Uptodown: done although a bit brittle
  - [ ] APKPure: not done, requires the cloudscraper library to circumvent anti-abuse measures
- [ ] Extract APKS: not done yet but File Roller seems to support it so shouldn't be that difficult I hope (and even then it's not that difficult to do manually)
- [ ] Decrypt data: right now needs BCGM

## Requirements

- Python (developed with 3.12)
- [requests](https://docs.python-requests.org/en/latest/index.html) library

## Licensing

This project uses code from <https://codeberg.org/fieryhenry/tbcml> and as such is licensed under the same terms, GPLv3.
