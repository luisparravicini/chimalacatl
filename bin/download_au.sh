#!/bin/sh

dir=`dirname "$0"`
source "$dir"/common.sh

# whole australia:
#
# for depth 20:
# --target "12 5 17 13"
#
# for depth 8:
# --target "5 2 6 5"

# southern east coast (depth 16)
# --target "12 8 13 10"

python "$dir"/../chimalacatl.py --depth $depth --target "12 8 13 10" --location "$lat $lng" --show-dates --date $*
