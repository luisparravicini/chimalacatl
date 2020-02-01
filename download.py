import urllib.request
import shutil
from datetime import datetime, timedelta
from pathlib import Path

#
# Downloads a whole day of Himawari 8 images at the specified depth.
# Each tile is cached locally to avoid downloading it again between runs.
#
# The himawari 8 url format was obtained from
# https://gist.github.com/FZambia/ca83c61beac90a15b4d6
# and https://github.com/bitpeach/EarthLiveForMatlab/blob/master/README.md
#
# There's a json with the date of the latest image taken at:
# http://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json

# depth can be: 4, 8, 16, 20
# (according to https://habr.com/ru/sandbox/99937/)
depth = 20
size = 550
image_url = "http://himawari8.nict.go.jp/img/D531106/%dd/%d/%s_%d_%d.png"

# time is (supposedly) gmt+8

whitelist = (
    # (1, 1),
)
print(f'tiles whitelist: {whitelist}')

step = timedelta(minutes=10)
cur_date = datetime.fromisoformat('2020-01-29 00:00')
end_date = cur_date + timedelta(days=1)

base_dir = Path('cache', 'himawari8', cur_date.strftime('%Y-%m-%d'), str(depth))
base_dir.mkdir(parents=True, exist_ok=True)

while cur_date < end_date:
    # for testing
    if cur_date.hour != 6:
        cur_date += step
        continue

    date_str = cur_date.strftime('%Y/%m/%d/%H%M%S')

    for x in range(depth):
        for y in range(depth):
            if len(whitelist) > 0 and (x, y) not in whitelist:
                continue

            file_name = Path(base_dir, '%d-%d.png' % (x, y))

            if file_name.exists():
                print(f'tile ({x},{y}) cached, skipping download')
                continue

            url = image_url % (depth, size, date_str, y, x)
            print(f'downloading from {url}')

            tmp_fname = file_name.with_suffix('.tmp')
            with urllib.request.urlopen(url) as response, open(tmp_fname, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

            tmp_fname.rename(file_name)

    cur_date += step
