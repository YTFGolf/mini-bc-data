"""Combine the functions of extract and decrypt"""

import zipfile
import os
import sys
import io
import re
from download import CountryCode
from decrypt import decryptfile

INNER_APK = 'InstallPack.apk'
INNER_FOLDER = 'assets/'

ual = '--use-all-langs'
if len(sys.argv) < 2:
    print(f'Usage: python simpleapk.py <to_read> [<{ual}>?]')

apk_to_read = os.path.expanduser(sys.argv[1])

files = {}
with zipfile.ZipFile(apk_to_read) as outer:
    inner = io.BytesIO(outer.read(INNER_APK))
    with zipfile.ZipFile(inner) as apk:
        for fileinfo in apk.infolist():
            if not re.match(r'^assets/\w+\.(?:list|pack)$', fileinfo.filename):
                continue
            newname = os.path.basename(fileinfo.filename)

            with apk.open(fileinfo) as fd:
                content = fd.read()
                files[newname] = content

names = []
for fname in files:
    name, ext = os.path.splitext(fname)
    if ext == '.pack':
        names.append(name)
names.sort()

if ual not in sys.argv:
    names2 = list(filter(lambda x: '_' not in x, names))
    if names2 != names:
        print(f'Removing all variant languages because {ual} is not set')
        names = names2

extracted_name = os.path.basename(apk_to_read.rstrip('.apk'))
output_dir = os.path.join('./data/decrypted', extracted_name)
[lang, *_] = extracted_name.partition('-')
cc = CountryCode.from_cc(lang)

for name in names:
    list_data = bytes(files[f'{name}.list'])
    pack_data = bytes(files[f'{name}.pack'])

    targ_base_path = os.path.join('./data/decrypted', extracted_name, name)

    decryptfile(list_data, pack_data, name, cc, targ_base_path)
