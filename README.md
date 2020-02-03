This script is used to download a whole day of tiles from the Himawari 8 satellite.

Himawari 8 is [japanese geostationary weather satellite](https://en.wikipedia.org/wiki/Himawari_8). The captured image is divided into tiles and there's new images every 10 minutes. All the tiles are 550px x 550px.
There's a "depth" variable which determines the definition of the whole image, possible values could be 4, 8, 16 or 20. For a depth of 4 the whole image is 4x4 tiles, thus having 2200px x 2200px (550px * 4), A depth of 20 gives a 20 x 20 tiles image of 11000px (550px * 20).


What does this script do:

* It tries to download all the images in a specified date.
* All files are saved in a local cache directory.
* A target region can be specified to donwload only the tiles inside it. If the target is empty, all the tiles are downloaded.
* With each downloaded row of images an image strip is generated.
* After the target region (or whole image) is downloaded, a target image is created.
* If the script is stopped or crashes, running it again will resume from where it left off.


After downloading the images, `mk_video.sh` will find all the target images and create a video `target.mp4` with those files.

For example:

`./download.py --date 2020-01-01`

will download all the images from 2020-01-01.


All the variables can be specified as parameters to the script:

```
usage: download.py [-h] --date DATE [--depth DEPTH] [--target TARGET]

Donwloads Himawari8 images.

optional arguments:
  -h, --help       show this help message and exit
  --date DATE      The day used to download images, as YYYY-MM-DD
  --depth DEPTH    Depth used (possible values: 4, 8, 16, 20). 20 is used if no value is specified
  --target TARGET  Target region defined as left,top,right,bottom.
```
