#!/bin/bash

if [[ $# -lt 5 ]]; then
	echo "usage: $0 download/ boxes/ frames-tar/ tmp-rename/ tmp-local/ [options]"
	echo
	echo 'Reads videos from download/ and writes images to frames-tar/'
	echo 'Calls extract_frames.py in parallel.'
	echo
	echo 'INPUT:'
	echo 'download/ -- Directory produced by download.sh'
	echo '    List of videos in download/video.txt'
	echo '    Videos are found in download/{video}/{video}.f*.*'
	echo 'boxes/ -- Directory produced by split_boxes.py'
	echo '    Boxes are found in boxes/{video}.csv'
	echo
	echo 'OUTPUT:'
	echo 'frames-tar/ -- Directory to which frames are written.'
	echo '    Images are saved to {video}/{time_ms}.jpg within frames/{video}.tar'
	echo
	echo 'TEMPORARY:'
	echo 'tmp/ -- Must be on the same physical disk as frames/'
	echo '    This ensures that os.rename() can be used.'
	echo
	exit 1
fi

download="$(readlink -f "$1")"   ; shift # e.g. ytbb/train/download
boxes="$(readlink -f "$1")"      ; shift # e.g. ytbb/train/boxes
frames="$(readlink -f "$1")"     ; shift # e.g. ytbb/train/frames-tar
tmp_rename="$(readlink -f "$1")" ; shift # e.g. ytbb/train/tmp-frames-tar-{unique-id}
tmp_local="$(readlink -f "$1")"  ; shift # e.g. /tmp/

NUM_PARALLEL=${NUM_PARALLEL:-8}

mkdir -p "$tmp_rename"

# cat $download/videos.txt 
comm -23 <(ls "$download/complete") <(ls "$frames" | sed -e 's/\..*//') | shuf | \
    xargs -I{} -n 1 -P "$NUM_PARALLEL" \
    python extract_frames.py "$boxes/{}.csv" "$download/complete/" "$frames" "$tmp_rename" "$tmp_local" $@
