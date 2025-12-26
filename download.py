from __future__ import annotations

import enum
from typing import Literal, Any, TypedDict
import requests
import os
import sys

################################################################################
# Most code in this file is taken from tbcml, in particular src/tbcml/io/apk.py
################################################################################


# https://codeberg.org/fieryhenry/tbcml/src/branch/master/src/tbcml/io/file_handler.py
class FileSize:
    def __init__(self, file_size: int):
        self.file_size = file_size

    def __str__(self) -> str:
        return self.format()

    def __repr__(self) -> str:
        return self.format()

    def format(self) -> str:
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024**2:
            return f"{self.file_size / 1024:.2f} KB"
        elif self.file_size < 1024**3:
            return f"{self.file_size / 1024 ** 2:.2f} MB"
        elif self.file_size < 1024**4:
            return f"{self.file_size / 1024 ** 3:.2f} GB"
        else:
            return f"{self.file_size / 1024 ** 4:.2f} TB"


# https://codeberg.org/fieryhenry/tbcml/src/branch/master/src/tbcml/country_code.py
class CountryCode(enum.Enum):
    """Country code enum."""

    EN = "en"
    JP = "jp"
    KR = "kr"
    TW = "tw"

    @staticmethod
    def from_cc(cc: Literal["en"] | Literal["jp"] | Literal["kr"] | Literal["tw"] | CountryCode):
        if isinstance(cc, str):
            return CountryCode.from_code(cc)
        return cc

    @staticmethod
    def from_code(code: str) -> CountryCode:
        map = {
            "ja": "jp",
            "ko": "kr",
        }
        # alternative names for these codes
        codel = code.lower()
        if codel in map:
            codel = map[codel]
        for country_code in CountryCode:
            if country_code.value == codel:
                return country_code

        raise ValueError(f'{code!r} is not a valid country code!')

    def __str__(self):
        return self.value


class VersionURL(TypedDict):
    url: str
    extraURL: str
    versionID: int

class UptodownVersion(TypedDict):
    fileID: int
    version: str
    minSDK: str
    lastUpdate: str
    sdkVersion: str
    kindFile: str
    titleKindFile: str
    versionURL: VersionURL


def get_uptodown(url, **kwargs):
    return requests.get(url, headers={'user-agent': "WWR's auto APK getter"}, **kwargs)

def get_apkpure_version_url(cc: CountryCode) -> str:
    if cc == CountryCode.JP:
        url = "https://apkpure.com/%E3%81%AB%E3%82%83%E3%82%93%E3%81%93%E5%A4%A7%E6%88%A6%E4%BA%89/jp.co.ponos.battlecats/versions"
    elif cc == CountryCode.KR:
        url = "https://apkpure.com/%EB%83%A5%EC%BD%94-%EB%8C%80%EC%A0%84%EC%9F%81/jp.co.ponos.battlecatskr/versions"
    elif cc == CountryCode.TW:
        url = "https://apkpure.com/%E8%B2%93%E5%92%AA%E5%A4%A7%E6%88%B0%E7%88%AD/jp.co.ponos.battlecatstw/versions"
    elif cc == CountryCode.EN:
        url = "https://apkpure.com/the-battle-cats/jp.co.ponos.battlecatsen/versions"

    return url

def get_uptodown_pkg_name(country_code: CountryCode) -> str:
    if country_code == CountryCode.EN:
        return "the-battle-cats"
    elif country_code == CountryCode.JP:
        return "the-battle-cats-jp"
    elif country_code == CountryCode.KR:
        return "jp-co-ponos-battlecatskr"
    elif country_code == CountryCode.TW:
        return "jp-co-ponos-battlecatstw"

def get_uptodown_app_id(country_code: CountryCode) -> str | None:
    package_name = get_uptodown_pkg_name(country_code)
    url = f"https://{package_name}.en.uptodown.com/android/versions"
    res = get_uptodown(url).text

    data = res[res.find("detail-app-name"):]
    code = 'data-code="'
    data = data[data.find(code) + len(code):]
    data = data[:data.find('"')]

    return data

def get_uptodown_apk_json(country_code: CountryCode) -> list[UptodownVersion]:
    package_name = get_uptodown_pkg_name(country_code)
    app_id = get_uptodown_app_id(country_code)
    if app_id is None:
        return []
    counter = 0
    versions: list[dict[str, Any]] = []
    while True:
        url = f"https://{package_name}.en.uptodown.com/android/apps/{app_id}/versions/{counter}"
        versions_data = get_uptodown(url).json().get("data")
        if versions_data is None:
            break
        if len(versions_data) == 0:
            break
        for version_data in versions_data:
            versions.append(version_data)
        counter += 1
    return versions

def get_uptodown_download_url(version: str, country_code: CountryCode) -> str:
    js = get_uptodown_apk_json(country_code)
    n = []

    version_split = version.split('.')
    for version2 in js:
        for (n1, n2) in zip(version_split, version2['version'].split('.')):
            if n1 != n2:
                break
        else:
            v = version2['versionURL']
            base = '/'.join([v['url'], v['extraURL'], str(v['versionID'])])
            n.append(base + '-x')

    if len(n) == 0:
        raise ValueError(
            f'Version {country_code}/{version!r} could not be found on uptodown. ' \
            f'You may want to manually download from {get_apkpure_version_url(country_code)}.'
        )

    res = get_uptodown(n[0]).text
    data = res[res.find("detail-download-button"):]
    code = 'data-url="'
    data = data[data.find(code) + len(code):]
    data = data[:data.find('"')]

    return "https://dw.uptodown.com/dwn/" + data

def to_data(data: Any) -> bytes:
    if isinstance(data, str):
        return data.encode("utf-8")
    elif isinstance(data, bytes):
        return data
    elif isinstance(data, bool):
        value = 1 if data else 0
        return str(value).encode("utf-8")
    elif isinstance(data, int):
        return str(data).encode("utf-8")
    elif isinstance(data, Data):
        return data.data
    elif data is None:
        return b""
    else:
        raise TypeError(
            f"data must be bytes, str, int, bool, Data, or None, not {type(data)}"
        )

def progress(
    progress: float,
    current: int,
    total: int,
    is_file_size: bool = False,
):
    total_bar_length = 50
    if is_file_size:
        current_str = FileSize(current).format()
        total_str = FileSize(total).format()
    else:
        current_str = str(current)
        total_str = str(total)
    bar_length = int(total_bar_length * progress)
    bar = "#" * bar_length + "-" * (total_bar_length - bar_length)
    print(
        f"\r[{bar}] {int(progress * 100)}% ({current_str}/{total_str})    ",
        end="",
    )

def download_uptodown(version: str, country_code: CountryCode, containing_folder: str):
    url = get_uptodown_download_url(version, country_code)
    stream = get_uptodown(url, stream=True)
    if stream.status_code == 404:
        return tbcml.Result(False, error=f"Download url returned 404: {url}")

    _total_length = int(stream.headers.get("content-length"))  # type: ignore

    dl = 0
    chunk_size = 1024
    buffer: list[bytes] = []
    for d in stream.iter_content(chunk_size=chunk_size):
        dl += len(d)
        buffer.append(d)
        if progress is not None:
            res = progress(dl / _total_length, dl, _total_length, True)
            if res is not None and not res:
                return tbcml.Result(
                    False, error="Download stopped by download callback"
                )

    apk = to_data(b"".join(buffer))
    filename = f'{country_code}-{version}.apk'
    abs_path = os.path.join(containing_folder, filename)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    with open(abs_path, "wb") as f:
        f.write(apk)
        print()
        print(abs_path)

if __name__ == '__main__':

    # https://stackoverflow.com/a/14981125
    def eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)
    raw_print = print
    def print(*args, **kwargs):
        raw_print(*args, **kwargs)
        # if you want to disable printing comment out this line
        pass

    try:
        version = sys.argv[1]
        cc = sys.argv[2]
    except IndexError:
        quit("Usage: python download.py <version_num> <country_code>")

    try:
        containing_folder = sys.argv[3]
    except IndexError:
        containing_folder = os.getcwd() + '/data'
        print(f'Using default containing folder: {containing_folder!r}')

    cc = CountryCode.from_cc(cc)

    download_uptodown(version, cc, containing_folder)
