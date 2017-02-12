#!/bin/bash

if [[ $# -ne 2 ]]; then
	echo "usage: $0 dst/ labels.csv"
	exit 1
fi
dst=$1
labels=$2

# Directory dst will have structure:
# dst/videos.txt
# dst/partial/
# dst/complete/

mkdir -p $dst
if [ ! -f "$dst/videos.txt" ]; then
	cut -d, -f1 <$labels | uniq | shuf >$dst/videos.txt
fi

# Download every video.
xargs -n 1 -P 16 ./download-one.sh $dst <$dst/videos.txt

# Find videos which are just not available.
(
	cd $dst
	grep -l 'ERROR:.*YouTube said:' $(find partial/ -name err.txt) | \
		awk '-F/' '{print $2}' >$dst/missing.txt
)
