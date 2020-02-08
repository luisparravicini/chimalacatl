#!/bin/sh

dir=`dirname "$0"`
source "$dir"/common.sh

# for depth 20:
# --target "12 5 17 13"
#
# for depth 8:
# --target "5 2 6 5"

python "$dir"/../chimalacatl.py --depth $depth --target "5 2 6 5" --location "$lat $lng" --date $*
