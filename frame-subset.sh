#!/bin/bash

if [[ $# -ne 2 ]]; then
	echo "usage: $0 labels.csv frames/"
	exit 1
fi
label_file=$1
frame_dir=$2

# (cd $frame_dir && find . -type f -name '*.jpg') | tee files.txt | nl
cat files.txt | sed -e 's/\.jpg$//' | awk -F/ '{print $2,$3}' | sort | uniq >image-frames.txt

cat $label_file | awk -F, '{print $1,$2}' | sort | uniq >label-frames.txt

comm -23 label-frames.txt image-frames.txt | tee missing-frames.txt | nl
cat missing-frames.txt | sed -e 's/^/^/g' | sed -e 's/$/,/g' | tr ' ' , >patterns.txt

grep -v -f patterns.txt $label_file >subset.csv
