import zipfile
import os
import sys
import io

INNER_APK = 'InstallPack.apk'
INNER_FOLDER = 'assets/'

apk_to_read = os.path.expanduser(sys.argv[1])

files = {}
with zipfile.ZipFile(apk_to_read) as outer:
    inner = io.BytesIO(outer.read(INNER_APK))
    with zipfile.ZipFile(inner) as apk:
        for fileinfo in apk.infolist():
            if not fileinfo.filename.startswith(INNER_FOLDER):
                continue

            with apk.open(fileinfo) as fd:
                content = fd.read()
                files[fileinfo.filename] = content

extracted_name = os.path.basename(apk_to_read.rstrip('.apk'))
output_dir = os.path.join('./data/extracted', extracted_name)
print("Extracting to", os.path.abspath(output_dir))

os.makedirs(output_dir, exist_ok=True)
for name, content in files.items():
    path = os.path.join(output_dir, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(content)
