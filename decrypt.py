#!/usr/bin/env python
import hashlib
import sys
import os
from Crypto.Cipher import AES
from download import progress, CountryCode

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

def open_file_b(path):
    with open(path, "rb") as f:
        return f.read()

def remove_pkcs7_padding(data):
    if not data:
        return data
    padding = data[-1]
    return data[:-padding]


def md5_str(string, length=8):
    return (
        bytearray(hashlib.md5(string.encode("utf-8")).digest()[:length])
        .hex()
        .encode("utf-8")
    )

def unpack_list(ls_file):
    data = open_file_b(ls_file)
    key = md5_str("pack")
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_data = cipher.decrypt(data)
    decrypted_data = remove_pkcs7_padding(data=decrypted_data)
    return decrypted_data

def parse_csv_file(path, lines=None, min_length=0, black_list=None):
    if not lines:
        lines = open(path, "r", encoding="utf-8").readlines()
    data = []
    for line in lines:
        line_data = line.split(",")
        if len(line_data) < min_length:
            continue
        if black_list:
            line_data = filter_list(line_data, black_list)

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

def decrypt_pack(chunk_data, cc, pk_name):
    aes_mode = AES.MODE_CBC

    skey, siv = get_key_iv_from_cc(cc)
    key, iv = bytes.fromhex(skey), bytes.fromhex(siv)

    if "server" in pk_name.lower():
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

def unpack_pack(pk_file_path, ls_data, cc, base_path):
    list_data = ls_data.decode("utf-8")
    split_data = parse_csv_file(None, list_data.split("\n"), 3)

    pack_data = open_file_b(pk_file_path)

    for i in range(len(split_data)):
        file = split_data[i]

        name = file[0]
        start_offset = int(file[1])
        length = int(file[2])

        pk_chunk = pack_data[start_offset : start_offset + length]
        base_name = os.path.basename(pk_file_path)
        if "imagedatalocal" in base_name.lower():
            pk_chunk_decrypted = pk_chunk
        else:
            pk_chunk_decrypted = decrypt_pack(pk_chunk, cc, base_name)

        open(os.path.join(base_path, name), "wb").write(pk_chunk_decrypted)

        j = i + 1
        progress(j / len(split_data), j, len(split_data), False)

    print()

def decryptfile(source_base_path, file):
    list_file = os.path.join(source_base_path, 'assets', f'{file}.list')
    pack_file = os.path.join(source_base_path, 'assets', f'{file}.pack')

    list_data = unpack_list(list_file)
    if list_data == b'0\n':
        print(f'skipping {file}')
        return

    extracted_name = os.path.basename(source_base_path)
    targ_base_path = os.path.join('./data/decrypted', extracted_name, file)
    print("extracting to", targ_base_path)
    os.makedirs(targ_base_path, exist_ok=True)

    [lang, *_] = extracted_name.partition('-')
    cc = CountryCode.from_cc(lang)

    unpack_pack(pack_file, list_data, cc, targ_base_path)

container = sys.argv[1].rstrip('/\\')
names = []
for fname in os.listdir(os.path.join(container, 'assets')):
    name, ext = os.path.splitext(fname)
    if ext == '.pack':
        names.append(name)
names.sort()

for name in names:
    decryptfile(container, name)
