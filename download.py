import urllib.request
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw

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
#
# timezone used in date strings is (supposedly) gmt+8
#


def tile_fname(dir, pos):
    return Path(dir, '%d-%d.png' % pos)


def download_tile(date_dir, tile, image_url, depth, size, date_str):
    x, y = tile
    file_name = tile_fname(date_dir, tile)

    if file_name.exists():
        print(f'\t[{x},{y}] found cache')
        return

    url = image_url % (depth, size, date_str, y, x)
    print(f'\t[{x},{y}] downloading from {url}')

    tmp_fname = file_name.with_suffix('.tmp')
    with urllib.request.urlopen(url) as response, open(tmp_fname, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    tmp_fname.rename(file_name)


def make_strip(date_dir, tiles, size, x, annotated=False):
    if annotated:
        strip_type = 'annotated'
    else:
        strip_type = ''

    strip_fname = Path(date_dir, 'strip_%s_%02d.jpg' % (strip_type, x))
    if strip_fname.exists():
        print(f'\t{strip_type} strip file exists')
        return

    print(f'\tsaving {strip_type} strip ({len(tiles)} tiles)')
    img = Image.new('RGB', (len(tiles) * size, size))
    if annotated:
        draw = ImageDraw.Draw(img)
    for index, tile in enumerate(tiles):
        tile_img = Image.open(tile_fname(date_dir, tile))
        img.paste(tile_img, (index * size, 0))
        if annotated:
            draw.rectangle(
                ((index * size, 0), (index * size + size, size)),
                width=2
            )
            offset = 50
            draw.text(
                (tile[1] * size + offset, offset),
                f'{tile[0]},{tile[1]}',
                fill='white'
            )
    tmp_strip_fname = strip_fname.with_suffix('.tmp')
    img.save(tmp_strip_fname, format='jpeg')
    tmp_strip_fname.rename(strip_fname)


def main():
    # depth can be: 4, 8, 16, 20
    # (according to https://habr.com/ru/sandbox/99937/)
    depth = 20
    size = 550
    image_url = "http://himawari8.nict.go.jp/img/D531106/%dd/%d/%s_%d_%d.png"
    create_annotated = True

    target = (
        (12, 5),
        (17, 12)
    )
    print(f'tiles target: {target}')

    step = timedelta(minutes=10)
    cur_date = datetime.fromisoformat('2020-01-29 00:00')
    end_date = cur_date + timedelta(days=1)

    base_dir = Path('cache', 'himawari8', str(depth), cur_date.strftime('%Y-%m-%d'))
    base_dir.mkdir(parents=True, exist_ok=True)

    while cur_date < end_date:
        # for testing
        if cur_date.hour != 6:
            cur_date += step
            continue

        print(cur_date.strftime('time: %H:%M'))

        date_str = cur_date.strftime('%Y/%m/%d/%H%M%S')

        date_dir = Path(base_dir, cur_date.strftime('%H-%M'))
        date_dir.mkdir(parents=True, exist_ok=True)

        for x in range(depth):
            tiles = []
            for y in range(depth):
                if len(target) > 0:
                    if x < target[0][0] or y < target[0][1]:
                        continue
                    if x > target[1][0] or y > target[1][1]:
                        continue

                tile = (x, y)
                tiles.append(tile)

                download_tile(date_dir, tile, image_url, depth, size, date_str)

            if len(tiles) > 0:
                make_strip(date_dir, tiles, size, x)
                if create_annotated:
                    make_strip(date_dir, tiles, size, x, annotated=True)

        cur_date += step


main()
