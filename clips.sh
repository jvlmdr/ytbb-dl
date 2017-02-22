#!/bin/bash

if [[ $# -le 4 ]]; then
	echo "usage: $0 download/ boxes/ clips/ tmp/ [options]"
	echo
	echo 'Reads videos from download/ and writes to clips/'
	echo 'Calls clips.py in parallel.'
	echo
	echo 'INPUT:'
	echo 'download/ -- Directory produced by download.sh'
	echo '    List of videos in download/video.txt'
	echo '    Videos are found in download/complete/{video}/{video}.f*.*'
	echo 'boxes/ -- Directory produced by split_boxes.py'
	echo '    Boxes are found in boxes/{video}.csv'
	echo
	echo 'OUTPUT:'
	echo 'clips/ -- Directory to which clips are written.'
	echo '    Clips are saved to clips/{video}/'
	echo
	echo 'TEMPORARY:'
	echo 'tmp/ -- Must be on the same physical disk as clips/'
	echo '    This ensures that os.rename() can be used.'
	echo
	exit 1
fi

download=$1 ; shift # e.g. /datasets/youtube-bb/train/download
boxes=$1    ; shift # e.g. /datasets/youtube-bb/train/boxes
clips=$1    ; shift # e.g. /datasets/youtube-bb/train/clips
tmp=$1      ; shift # e.g. /datasets/youtube-bb/train/tmp/clips

cat $download/videos.txt | xargs -t -I{} -n 1 -P 1 python clips.py $@ $boxes/{}.csv $download/complete/ $clips $tmp
