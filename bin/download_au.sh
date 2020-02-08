#!/bin/sh

dir=`dirname "$0"`
source "$dir"/common.sh

python "$dir"/../chimalacatl.py --depth $depth --target "12 5 17 13" --location "$lat $lng" --date $*
