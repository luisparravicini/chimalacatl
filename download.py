import requests
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageDraw
import argparse
from suntime import Sun, SunTimeException
import pytz
import os

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


class Downloader:
    def __init__(self, create_annotated, force_creation, location):
        self.create_annotated = create_annotated
        self.force_creation = force_creation
        self.location = location

    def _tile_fname(self, pos):
        return Path(self.date_dir, '%d-%d.png' % pos)

    def _download_tile(self, tile, image_url, depth, date_str):
        x, y = tile
        file_name = self._tile_fname(tile)

        if file_name.exists():
            self._log(f'[{x},{y}] cached')
            return True

        url = image_url % (depth, self.size, date_str, y, x)
        self._log(f'[{x},{y}] downloading from {url}')

        tmp_fname = file_name.with_suffix('.tmp')
        try:
            response = requests.get(url)
            response.raise_for_status()
        except (requests.exceptions.BaseHTTPError,
                requests.exceptions.ConnectionError) as e:
            self._log(f'error during download: "{e}"')
            return False

        with open(tmp_fname, 'wb') as out_file:
            out_file.write(response.content)
        tmp_fname.rename(file_name)

        return True

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
            tile_path = self._tile_fname(tile)
            tile_img = Image.open(tile_path)
            try:
                img.paste(tile_img, (index * self.size, 0))
            except IOError as e:
                if str(e) == 'image file is truncated':
                    self._log(f'removing truncated image (rerun script)')
                    os.remove(tile_path)
                    return None
                else:
                    raise e
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

    def run(self, start_date, depth, target):
        self.cur_date = pytz.utc.localize(start_date)

        self._log(f'using depth {depth}')

        sunrise = sunset = None
        if self.location is not None:
            sun = Sun(self.location[0], self.location[1])
            sunrise = sun.get_sunrise_time(self.cur_date)
            sunset = sun.get_sunset_time(self.cur_date)
            sunrise_s = sunrise.strftime('%H:%M')
            sunset_s = sunset.strftime('%H:%M')
            self._log(f'using location: {self.location}, sunrise: {sunrise_s}, sunset: {sunset_s}')
            # magic!
            suntime_offset = timedelta(hours=1)
            sunrise -= suntime_offset
            sunset += suntime_offset

        self.size = 550
        image_url = "http://himawari8.nict.go.jp/img/D531106/%dd/%d/%s_%d_%d.png"

        self._log(f'tiles target: {target}')

        step = timedelta(minutes=10)
        end_date = self.cur_date + timedelta(days=1)

        base_dir = Path('~', 'cache-sat', 'himawari8', str(depth), self.cur_date.strftime('%Y-%m-%d'))
        base_dir = base_dir.expanduser()
        base_dir.mkdir(parents=True, exist_ok=True)

        while self.cur_date < end_date:
            date_str = self.cur_date.strftime('%Y/%m/%d/%H%M%S')

            self.date_dir = Path(base_dir, self.cur_date.strftime('%H-%M'))

            if sunrise is not None:
                if sunrise > sunset:
                    if sunset <= self.cur_date <= sunrise:
                        self.cur_date += step
                        continue
                else:
                    if sunrise <= self.cur_date <= sunset:
                        self.cur_date += step
                        continue

            all_downloaded = True
            strips = []
            for x in range(depth):
                tiles = []
                for y in range(depth):
                    if len(target) > 0:
                        if x < target[0] or y < target[1]:
                            continue
                        if x > target[2] or y > target[3]:
                            continue

                    tile = (x, y)
                    tiles.append(tile)

                    self.date_dir.mkdir(parents=True, exist_ok=True)
                    success = self._download_tile(tile, image_url, depth, date_str)
                    if not success:
                        all_downloaded = False

                if all_downloaded and len(tiles) > 0:
                    strip_fname = self._make_strip(tiles, x)
                    if strip_fname is None:
                        all_downloaded = False
                    else:
                        strips.append(strip_fname)
                        if self.create_annotated:
                            self._make_strip(tiles, x, annotated=True)

            if all_downloaded and len(strips) > 0:
                strip_width = (target[3] - target[1] + 1) * self.size
                self._make_target_image(strips, strip_width)

            self.cur_date += step


parser = argparse.ArgumentParser(description='Donwloads Himawari8 images.')
parser.add_argument('--date',
                    required=True,
                    help='The day used to download images, as YYYY-MM-DD')
parser.add_argument('--depth', type=int, default=20,
                    help='Depth used (possible values: 4, 8, 16, 20). 20 is used if no value is specified')
parser.add_argument('--target',
                    help='Target region defined as "left top right bottom". ')
parser.add_argument('--annotated', default=False, action='store_true',
                    help='Create annotated strip images.')
parser.add_argument('--force', default=False, action='store_true',
                    help='Force creation of strip and target images.')
parser.add_argument('--location',
                    help='Location to use to get sunset/sunrise times. Specified as "latitude longitude"')
args = parser.parse_args()

date = datetime.strptime(args.date, '%Y-%m-%d')
target = []
if args.target is not None:
    target = [int(x) for x in args.target.split(' ')]
location = None
if args.location is not None:
    location = [float(x) for x in args.location.split(' ')]
downloader = Downloader(
                create_annotated=args.annotated,
                force_creation=args.force,
                location=location)

downloader.run(date, args.depth, target)
