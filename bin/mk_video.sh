#!/bin/sh

dir=`dirname "$0"`
source "$dir"/common.sh

python "$dir"/../chimalacatl.py --depth $depth --location "$lat $lng" --targets
[ $? -eq 0 ] || exit 1

# -vf scale=-1:640
ffmpeg -f concat -safe 0 -i targets.txt -y -r 10 -c:v libx264 -vf scale=-1:640 target.mp4
