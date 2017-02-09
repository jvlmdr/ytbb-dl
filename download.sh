#!/bin/bash

if [[ $# -ne 2 ]]; then
	echo "usage: $0 dst/ labels.csv"
	exit 1
fi
dst=$1
labels=$2

mkdir -p $dst
if [ ! -f "$dst/videos.txt" ]; then
	cut -d, -f1 <$labels | uniq | shuf >$dst/videos.txt
fi

# Download every video.
xargs -n 1 -P 16 ./download-one.sh $dst <$dst/videos.txt
