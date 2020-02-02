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
    def __init__(self, create_annotated, force_creation):
        self.create_annotated = create_annotated
        self.force_creation = force_creation

    def _tile_fname(self, pos):
        return Path(self.date_dir, '%d-%d.png' % pos)

    def _download_tile(self, tile, image_url, depth, date_str):
        x, y = tile
        file_name = self._tile_fname(tile)

        if file_name.exists():
            self._log(f'[{x},{y}] cached')
            return

        url = image_url % (depth, self.size, date_str, y, x)
        self._log(f'[{x},{y}] downloading from {url}')

        tmp_fname = file_name.with_suffix('.tmp')
        with urllib.request.urlopen(url) as response, open(tmp_fname, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

        tmp_fname.rename(file_name)

    def _make_strip(self, tiles, x, annotated=False):
        if annotated:
            strip_type = 'annotated '
        else:
            strip_type = ''

        strip_fname = Path(self.date_dir, 'strip_%s_%02d.jpg' % (strip_type, x))
        if strip_fname.exists():
            self._log(f'{strip_type}strip file exists (recreate? {self.force_creation})')
            if not self.force_creation:
                return strip_fname

        self._log(f'saving {strip_type}strip ({len(tiles)} tiles)')
        width = len(tiles) * self.size
        img = Image.new('RGB', (width, self.size))
        if annotated:
            draw = ImageDraw.Draw(img)
        for index, tile in enumerate(tiles):
            tile_img = Image.open(self._tile_fname(tile))
            img.paste(tile_img, (index * self.size, 0))
            if annotated:
                draw.rectangle(
                    ((index * self.size, 0), (index * self.size + self.size, self.size)),
                    width=2
                )
                offset = 50
                draw.text(
                    (tile[1] * self.size + offset, offset),
                    f'{tile[0]},{tile[1]}',
                    fill='white'
                )
        tmp_strip_fname = strip_fname.with_suffix('.tmp')
        img.save(tmp_strip_fname, format='jpeg')
        tmp_strip_fname.rename(strip_fname)

        return strip_fname

    def _make_target_image(self, strips_paths, width):
        dstr = self.cur_date.strftime('%Y%m%d%H%M%S')
        image_fname = Path(self.date_dir, 'target-%s.jpg' % dstr)
        if image_fname.exists():
            self._log(f'target image file exists (recreate? {self.force_creation})')
            if not self.force_creation:
                return

        self._log(f'saving target ({len(strips_paths)} strips)')

        img = Image.new('RGB', (width, len(strips_paths) * self.size))
        for index, strip_path in enumerate(strips_paths):
            strip_img = Image.open(strip_path)
            img.paste(strip_img, (0, index * self.size))

        tmp_target_fname = image_fname.with_suffix('.tmp')
        img.save(tmp_target_fname, format='jpeg')
        tmp_target_fname.rename(image_fname)

    def _log(self, what):
        when = self.cur_date.strftime('%Y-%m-%dT%H:%M')
        print(f'{when}: {what}')

    def run(self):
        # depth can be: 4, 8, 16, 20
        # (according to https://habr.com/ru/sandbox/99937/)
        depth = 20
        self.size = 550
        image_url = "http://himawari8.nict.go.jp/img/D531106/%dd/%d/%s_%d_%d.png"

        target = (
            (12, 5),
            (17, 13)
        )
        print(f'tiles target: {target}')

        step = timedelta(minutes=10)
        self.cur_date = datetime.fromisoformat('2020-01-29 00:00')
        end_date = self.cur_date + timedelta(days=1)

        base_dir = Path('~', 'cache-sat', 'himawari8', str(depth), self.cur_date.strftime('%Y-%m-%d'))
        base_dir = base_dir.expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)

        while self.cur_date < end_date:
            date_str = self.cur_date.strftime('%Y/%m/%d/%H%M%S')

            self.date_dir = Path(base_dir, self.cur_date.strftime('%H-%M'))
            self.date_dir.mkdir(parents=True, exist_ok=True)

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

                    self._download_tile(tile, image_url, depth, date_str)

                if len(tiles) > 0:
                    strip_fname = self._make_strip(tiles, x)
                    strips.append(strip_fname)
                    if self.create_annotated:
                        self._make_strip(tiles, x, annotated=True)

            if len(strips) > 0:
                strip_width = (target[1][1] - target[0][1]) * self.size
                self._make_target_image(strips, strip_width)

            self.cur_date += step


Downloader(create_annotated=False, force_creation=False).run()
