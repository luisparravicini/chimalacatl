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


class Downloader:
    def tile_fname(self, dir, pos):
        return Path(dir, '%d-%d.png' % pos)

    def download_tile(self, date_dir, tile, image_url, depth, size, date_str):
        x, y = tile
        file_name = self.tile_fname(date_dir, tile)

        if file_name.exists():
            print(f'\t[{x},{y}] found cache')
            return

        url = image_url % (depth, size, date_str, y, x)
        print(f'\t[{x},{y}] downloading from {url}')

        tmp_fname = file_name.with_suffix('.tmp')
        with urllib.request.urlopen(url) as response, open(tmp_fname, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        tmp_fname.rename(file_name)

    def make_strip(self, date_dir, tiles, size, x, force_creation=False, annotated=False):
        if annotated:
            strip_type = 'annotated'
        else:
            strip_type = ''

        strip_fname = Path(date_dir, 'strip_%s_%02d.jpg' % (strip_type, x))
        if strip_fname.exists():
            print(f'\t{strip_type} strip file exists')
            if force_creation:
                print('\trecreating strip')
            else:
                return strip_fname

        print(f'\tsaving {strip_type} strip ({len(tiles)} tiles)')
        width = len(tiles) * size
        img = Image.new('RGB', (width, size))
        if annotated:
            draw = ImageDraw.Draw(img)
        for index, tile in enumerate(tiles):
            tile_img = Image.open(self.tile_fname(date_dir, tile))
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

        return strip_fname

    def make_target_image(self, date_dir, cur_date, strips_paths, width, size, force_creation=False):
        dstr = cur_date.strftime('%Y%m%d%H%M%S')
        image_fname = Path(date_dir, 'target-%s.jpg' % dstr)
        if image_fname.exists():
            print('\ttarget image file exists')
            if force_creation:
                print('\trecreating image')
            else:
                return

        print(f'\tsaving target ({len(strips_paths)} strips)')

        img = Image.new('RGB', (width, len(strips_paths) * size))
        for index, strip_path in enumerate(strips_paths):
            strip_img = Image.open(strip_path)
            img.paste(strip_img, (0, index * size))

        tmp_target_fname = image_fname.with_suffix('.tmp')
        img.save(tmp_target_fname, format='jpeg')
        tmp_target_fname.rename(image_fname)

    def main(self, create_annotated=True, force_creation=False):
        # depth can be: 4, 8, 16, 20
        # (according to https://habr.com/ru/sandbox/99937/)
        depth = 20
        size = 550
        image_url = "http://himawari8.nict.go.jp/img/D531106/%dd/%d/%s_%d_%d.png"

        target = (
            (12, 5),
            (17, 13)
        )
        print(f'tiles target: {target}')

        step = timedelta(minutes=10)
        cur_date = datetime.fromisoformat('2020-01-29 00:00')
        end_date = cur_date + timedelta(days=1)

        base_dir = Path('~', 'cache-sat', 'himawari8', str(depth), cur_date.strftime('%Y-%m-%d'))
        base_dir = base_dir.expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)

        while cur_date < end_date:
            print(cur_date.strftime('time: %H:%M'))

            date_str = cur_date.strftime('%Y/%m/%d/%H%M%S')

            date_dir = Path(base_dir, cur_date.strftime('%H-%M'))
            date_dir.mkdir(parents=True, exist_ok=True)

            strips = []
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

                    self.download_tile(date_dir, tile, image_url, depth, size, date_str)

                if len(tiles) > 0:
                    strip_fname = self.make_strip(date_dir, tiles, size, x, force_creation=force_creation)
                    strips.append(strip_fname)
                    if create_annotated:
                        self.make_strip(date_dir, tiles, size, x, annotated=True)

            if len(strips) > 0:
                strip_width = (target[1][1] - target[0][1]) * size
                self.make_target_image(date_dir, cur_date, strips, strip_width, size, force_creation=force_creation)

            cur_date += step


Downloader().main(create_annotated=True, force_creation=True)
