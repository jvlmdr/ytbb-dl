#!/bin/bash

if [[ $# -lt 5 ]]; then
	echo "usage: $0 videos.txt boxes/ frames/ crops/ tmp/ [options]"
	echo
	echo 'Reads images from frames/ and writes images to crops/'
	echo 'Calls crops.py in parallel.'
	echo
	echo 'INPUT:'
	echo 'videos.txt -- List of videos'
	echo 'boxes/ -- Directory produced by split_boxes.py'
	echo '    Boxes are found in boxes/{video}.csv'
	echo 'frames/ -- Directory produced by frames.py'
	echo '    Images are found in frames/{video}/{time_ms}.jpg'
	echo
	echo 'OUTPUT:'
	echo 'crops/ -- Directory to which crops are written.'
	echo '    Images are saved to crops/{video}/{class}-{index}/{time_ms}.jpg'
	echo
	echo 'TEMPORARY:'
	echo 'tmp/ -- Must be on the same physical disk as crops/'
	echo '    This ensures that os.rename() can be used.'
	echo
	exit 1
fi

videos=$1 ; shift # e.g. /datasets/youtube-bb/download/videos.txt
boxes=$1  ; shift # e.g. /datasets/youtube-bb/train/boxes
frames=$1 ; shift # e.g. /datasets/youtube-bb/train/frames
crops=$1  ; shift # e.g. /datasets/youtube-bb/train/crops
tmp=$1    ; shift # e.g. /datasets/youtube-bb/train/tmp-crops

cat $videos | xargs -I{} -n 1 -P 16 python crops.py $@ $boxes/{}.csv $frames $crops $tmp
