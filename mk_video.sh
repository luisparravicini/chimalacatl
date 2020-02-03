#!/bin/sh


find ~/cache-sat/ -iname '*target*.jpg' | sed -e "s/$/'/" -e "s/^/file '/" >targets.txt

ffmpeg -f concat -safe 0 -i targets.txt -y -r 10 -c:v libx264 target.mp4
