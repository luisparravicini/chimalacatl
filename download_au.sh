#!/bin/sh

# Brisbane
lat=-27.470125
lng=153.021072

python download.py --depth 20 --target "12 5 17 13" --location "$lat $lng" --date $*
