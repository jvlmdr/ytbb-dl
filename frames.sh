#!/bin/bash

if [[ $# -ne 4 ]]; then
	echo "usage: $0 download/ boxes/ frames/ tmp/"
	echo
	echo 'Reads videos from download/ and writes images to frames/'
	echo 'Calls frames.py in parallel.'
	echo
	echo 'INPUT:'
	echo 'download/ -- Directory produced by download.sh'
	echo '    List of videos in download/video.txt'
	echo '    Videos are found in download/{video}/{video}.f*.*'
	echo 'boxes/ -- Directory produced by split_boxes.py'
	echo '    Boxes are found in boxes/{video}.csv'
	echo
	echo 'OUTPUT:'
	echo 'frames/ -- Directory to which frames are written.'
	echo '    Images are saved to frames/{video}/{time_ms}.jpg'
	echo
	echo 'TEMPORARY:'
	echo 'tmp/ -- Must be on the same physical disk as frames/'
	echo '    This ensures that os.rename() can be used.'
	echo
	exit 1
fi

download=$1 # e.g. /datasets/youtube-bb/train/download
boxes=$2    # e.g. /datasets/youtube-bb/train/boxes
frames=$3   # e.g. /datasets/youtube-bb/train/frames
tmp=$4      # e.g. /datasets/youtube-bb/train/tmp-frames

cat $download/videos.txt | xargs -I{} -n 1 -P 8 python frames.py $boxes/{}.csv $download/complete/ $frames $tmp
