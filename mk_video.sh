#!/bin/sh


find ~/cache-sat/ -iname '*target*.jpg' | sed -e "s/$/'/" -e "s/^/file '/" >targets.txt

# -vf scale=-1:640
ffmpeg -f concat -safe 0 -i targets.txt -y -r 10 -c:v libx264 -vf scale=-1:640 target.mp4
