from __future__ import annotations

import enum
from typing import Literal, Any, TypedDict
import requests
import os
import sys
import re

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
            return f"{self.file_size / 1024:.2f} KiB"
        elif self.file_size < 1024**3:
            return f"{self.file_size / 1024 ** 2:.2f} MiB"
        elif self.file_size < 1024**4:
            return f"{self.file_size / 1024 ** 3:.2f} GiB"
        else:
            return f"{self.file_size / 1024 ** 4:.2f} TiB"


# https://codeberg.org/fieryhenry/tbcml/src/branch/master/src/tbcml/country_code.py
class CountryCode(enum.Enum):
    """Country code enum."""

    EN = "en"
    JP = "jp"
    KR = "kr"
    TW = "tw"

    @staticmethod
    def from_cc(cc: str | Literal["en"] | Literal["jp"] | Literal["kr"] | Literal["tw"] | CountryCode):
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

    def get_patch_code(self) -> str:
        """For apkpure"""
        if self == CountryCode.JP:
            return ""
        else:
            return self.value

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


def get_uptodown(url: str, **kwargs: Any):
    return requests.get(url, headers={'user-agent': "WWR's auto APK getter"}, **kwargs)

def get_apkpure_versions_page(cc: CountryCode) -> str:
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
    versions: list[UptodownVersion] = []
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

    n: list[str] = []
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
            f'You may want to manually download from {get_apkpure_versions_page(country_code)}.'
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

def download_stream(stream: requests.Response, abs_path: str):
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
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    with open(abs_path, "wb") as f:
        f.write(apk)
        print()
        print(abs_path)

def download_uptodown(version: str, country_code: CountryCode, containing_folder: str):
    url = get_uptodown_download_url(version, country_code)
    stream = get_uptodown(url, stream=True)
    if stream.status_code == 404:
        return tbcml.Result(False, error=f"Download url returned 404: {url}")
    filename = f'{country_code}-{version}.apk'
    abs_path = os.path.join(containing_folder, filename)

    download_stream(stream, abs_path)

def get_apkpure_versions(country_code: CountryCode) -> list[str]:
    import cloudscraper
    url = get_apkpure_versions_page(country_code)

    # https://github.com/VeNoMouS/cloudscraper?tab=readme-ov-file#v3-with-different-javascript-interpreters
    scraper = cloudscraper.create_scraper(
        delay=5,
        # interpreter='nodejs',
    )
    # scraper.headers.update({
    #     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    # })
    # should realistically do some looping thing between different scrapers

    res = scraper.get(url)
    html = res.text

    if "<title>Just a moment...</title>" in html:
        raise ValueError('apkpure request blocked by cloudflare')
        # quit(html)

    lists = re.findall(r'<ul[^>]*ver-wrap[^>]*>(?:.|\n)*?</ul>', html)
    # ver-wrap class

    versions: list[str] = []
    for ls in lists:
        items = re.findall(r'<li[^>]*>(?:.|\n)*?</li>', ls)
        for item in items:
            link_s = re.search(r'<a(?:[^>]|\n)*>', item)
            if not link_s:
                continue
            link = link_s.group(0)
            ver = re.search(r'data-dt-version="([^"]*)"', link)
            if not ver:
                raise ValueError('interface changed; code needs to be updated')
            versions.append(ver.group(1))

    return sorted(dict.fromkeys(versions), reverse=True)

def get_gv_int(game_version: str) -> int:
    split_gv = game_version.split(".")
    if len(split_gv) == 2:
        split_gv.append("0")
    final = ""
    for split in split_gv:
        final += split.zfill(2)

    return int(final)

def get_apkpure_dl_link(version: str, country_code: CountryCode) -> str:
    versions = get_apkpure_versions(country_code)

    version_split = version.split('.')
    to_download: list[str] = []
    for version2 in versions:
        for (n1, n2) in zip(version_split, version2.split('.')):
            if n1 != n2:
                break
        else:
            to_download.append(version2)

    if len(to_download) == 0:
        raise ValueError(
            f'Version {country_code}/{version!r} could not be found on apkpure.'
        )

    ver = str(get_gv_int(to_download[0])) + '0'
    vendor = 'jp.co.ponos.battlecats' + country_code.get_patch_code()
    return f"https://d.apkpure.com/b/XAPK/{vendor}?versionCode={ver}"

def download_apkpure(version: str, country_code: CountryCode, containing_folder: str):
    print(f'Version {country_code}/{version!r} could not be found on uptodown. Trying apkpure.')
    try:
        import cloudscraper
    except ModuleNotFoundError:
        raise ValueError('Could not import cloudscraper. Run `pip install cloudscraper` or consult the appropriate documentation.')

    url = get_apkpure_dl_link(version, country_code)

    from time import sleep
    sleep(0.5)
    scraper = cloudscraper.create_scraper()
    scraper.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36"
    })

    stream = scraper.get(url, stream=True, timeout=10)
    if stream.status_code == 404:
        return tbcml.Result(False, error=f"Download url returned 404: {url}")
    filename = f'{country_code}-{version}.apk'
    abs_path = os.path.join(containing_folder, filename)

    download_stream(stream, abs_path)


if __name__ == '__main__':
    try:
        version = sys.argv[1]
        cc = sys.argv[2]
    except IndexError:
        quit("Usage: python download.py <version_num> <country_code>")

    try:
        containing_folder = sys.argv[3]
    except IndexError:
        containing_folder = os.getcwd() + '/data/apk'
        print(f'Using default containing folder: {containing_folder!r}')

    cc = CountryCode.from_cc(cc)

    try:
        download_uptodown(version, cc, containing_folder)
    except ValueError as e:
        print(e)
        try:
            download_apkpure(version, cc, containing_folder)
        except (ValueError, TypeError) as e:
            print(f'Error when trying to download from apkpure: {e.__traceback__}')
            print(f'Try manually downloading the apk (e.g. see {get_apkpure_versions_page(cc)})')
