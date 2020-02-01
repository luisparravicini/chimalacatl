import urllib.request
import shutil
import datetime
from pathlib import Path


# url format from https://gist.github.com/FZambia/ca83c61beac90a15b4d6
# and https://github.com/bitpeach/EarthLiveForMatlab/blob/master/README.md

# json with latest image:
# http://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json

# depath is: 4, 8, 16, 20
# according to https://habr.com/ru/sandbox/99937/

depth = 20
size = 550
image_url = "http://himawari8.nict.go.jp/img/D531106/%dd/%d/%s_%d_%d.png"
date_format = "YYYY/DD/mm/HHMMSS"

# time is (supposedly) gmt+8
h = 6
date = '2020/01/01/%02d1000' % h

for x in range(depth):
    for y in range(depth):
        base_dir = Path('cache', 'himawari8', '2020-01-01', str(depth))
        base_dir.mkdir(parents=True, exist_ok=True)
        file_name = Path(base_dir, '%d-%d.png' % (x, y))

        url = image_url % (depth, size, date, y, x)
        print(f'downloading from {url}')
        with urllib.request.urlopen(url) as response, open(file_name, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
