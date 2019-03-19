#!/bin/bash

if [[ $# -ne 2 ]]; then
	echo "usage: $0 labels.csv frames/"
    echo
    echo "Takes subset of labels.csv for videos in frames/"
    echo
	exit 1
fi
src_file="$1"
frame_dir="$2"

# (cd $frame_dir && find . -type f -name '*.jpg') | tee files.txt | nl
# cat files.txt | sed -e 's/\.jpg$//' | awk -F/ '{print $2,$3}' | sort | uniq >image-frames.txt

# cat $src_file | awk -F, '{print $1,$2}' | sort | uniq >label-frames.txt

# comm -23 label-frames.txt image-frames.txt | tee missing-frames.txt | nl
# cat missing-frames.txt | sed -e 's/^/^/g' | sed -e 's/$/,/g' | tr ' ' , >patterns.txt

# grep -v -f patterns.txt $src_file >subset.csv

awk -F, 'NR==FNR{v[$1]; next} $1 in v{print $0}' <(ls "$frame_dir") "$src_file"
