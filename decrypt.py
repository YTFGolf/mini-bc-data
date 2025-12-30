#!/usr/bin/env python
import hashlib
import sys
import os
from Crypto.Cipher import AES
from download import progress, CountryCode
from typing import Optional

# this file is adapted from
# https://codeberg.org/fieryhenry/BCGM-Python/src/branch/master/src/BCGM_Python/encrypt_decrypt/decrypt_pack.py
# which is actually under a different license which reads as

"""
MIT License

Copyright (c) [2022] [fieryhenry]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# The license thing is a little confusing to me, but it seems like all that
# needs to be done is to license them both _simultaneously_ (not dual
# licensing), i.e. this project as a whole is already GPLv3 so those conditions
# are cleared, and this license text means the MIT license conditions are
# cleared as well.

def open_file_b(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()

def remove_pkcs7_padding(data: bytes) -> bytes:
    if not data:
        return data
    padding = data[-1]
    return data[:-padding]


def md5_str(string: str, length=8) -> bytes:
    return (
        bytearray(hashlib.md5(string.encode("utf-8")).digest()[:length])
        .hex()
        .encode("utf-8")
    )

def unpack_list(list_file_raw: bytes):
    key = md5_str("pack")
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_data = cipher.decrypt(list_file_raw)
    decrypted_data = remove_pkcs7_padding(data=decrypted_data)
    return decrypted_data

def parse_csv_file(path: str, lines: Optional[list[str]] = None, min_length = 0, blacklist = None) -> list[list[str]]:
    if not lines:
        lines = open(path, "r", encoding="utf-8").readlines()

    data = []
    for line in lines:
        line_data = line.split(",")
        if len(line_data) < min_length:
            continue

        if blacklist:
            # line_data = filter_list(line_data, blacklist)
            raise NotImplementedError

        data.append(line_data)
    return data

# https://codeberg.org/fieryhenry/tbcml/src/branch/master/src/tbcml/crypto.py
# https://codeberg.org/fieryhenry/tbcml/src/commit/4eede7d7af9b770dceb08ef6313f62aabe2fc45d/src/tbcml/crypto.py#L139

def get_key_iv_from_cc(cc: CountryCode) -> tuple[str, str]:
    if cc == CountryCode.JP:
        key = "d754868de89d717fa9e7b06da45ae9e3"
        iv = "40b2131a9f388ad4e5002a98118f6128"
    elif cc == CountryCode.EN:
        key = "0ad39e4aeaf55aa717feb1825edef521"
        iv = "d1d7e708091941d90cdf8aa5f30bb0c2"
    elif cc == CountryCode.KR:
        key = "bea585eb993216ef4dcb88b625c3df98"
        iv = "9b13c2121d39f1353a125fed98696649"
    elif cc == CountryCode.TW:
        key = "313d9858a7fb939def1d7d859629087d"
        iv = "0e3743eb53bf5944d1ae7e10c2e54bdf"
    else:
        raise ValueError("Unknown country code")
    return key, iv

def decrypt_pack(chunk_data: bytes, cc: CountryCode, pack_name: str) -> bytes:
    aes_mode = AES.MODE_CBC

    skey, siv = get_key_iv_from_cc(cc)
    key, iv = bytes.fromhex(skey), bytes.fromhex(siv)

    if "server" in pack_name.lower():
        key = md5_str("battlecats")
        iv = None
        aes_mode = AES.MODE_ECB
    if iv:
        cipher = AES.new(key, aes_mode, iv)
    else:
        cipher = AES.new(key, aes_mode)
    decrypted_data = cipher.decrypt(chunk_data)
    decrypted_data = remove_pkcs7_padding(data=decrypted_data)
    return decrypted_data

def unpack_pack(pk_file, pk_base_name, list_data, cc, save_to_base):
    files_info = parse_csv_file(None, list_data.split("\n"), 3)

    for i, file_info in enumerate(files_info):
        name = file_info[0]
        start_offset = int(file_info[1])
        length = int(file_info[2])

        pk_chunk = pk_file[start_offset : start_offset + length]
        if "imagedatalocal" in pk_base_name.lower():
            pk_chunk_decrypted = pk_chunk
        else:
            pk_chunk_decrypted = decrypt_pack(pk_chunk, cc, pk_base_name)

        open(os.path.join(save_to_base, name), "wb").write(pk_chunk_decrypted)

        j = i + 1
        progress(j / len(files_info), j, len(files_info), False)

    print()

def decryptfile(source_base_path, file):
    list_file = os.path.join(source_base_path, 'assets', f'{file}.list')
    pack_file = os.path.join(source_base_path, 'assets', f'{file}.pack')

    list_data = unpack_list(open_file_b(list_file))
    if list_data == b'0\n':
        print(f'skipping {file}')
        return

    extracted_name = os.path.basename(source_base_path)
    targ_base_path = os.path.join('./data/decrypted', extracted_name, file)
    print("extracting to", targ_base_path)
    os.makedirs(targ_base_path, exist_ok=True)

    [lang, *_] = extracted_name.partition('-')
    cc = CountryCode.from_cc(lang)

    pk_file = open_file_b(pack_file)
    base_name = os.path.basename(pack_file)
    list_data = list_data.decode("utf-8")
    unpack_pack(pk_file, base_name, list_data, cc, targ_base_path)

if __name__ == '__main__':
    container = sys.argv[1].rstrip('/\\')
    names = []
    for fname in os.listdir(os.path.join(container, 'assets')):
        name, ext = os.path.splitext(fname)
        if ext == '.pack':
            names.append(name)
    names.sort()

    for name in names:
        decryptfile(container, name)
