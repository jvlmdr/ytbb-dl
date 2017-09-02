#!/bin/bash

# e.g. format="[fps=30][height<=360]"
format="[fps=30]"

if [[ $# -ne 2 ]]; then
	echo "usage: $0 dst/ video-id"
	exit 1
fi
dst=$1
video=$2

mkdir -p $dst/complete
prefix="video $video"

# Skip video if directory already exists in dst/
if [ -d "$dst/complete/$video" ]; then
	echo "$prefix: skip"
	exit 0
fi

mkdir -p $dst/partial/$video
(
	cd $dst/partial/$video
	set -o pipefail
	youtube-dl \
        -f "(bestvideo${format},bestaudio)/best${format}" \
        -o '%(id)s.f%(format_id)s.%(ext)s' \
        --newline \
        -- "https://www.youtube.com/watch?v=$video" \
		2>err.txt | tee out.txt
)
result=$?

# Move if successful.
if [ $result -eq 0 ]; then
	mv $dst/partial/$video $dst/complete/$video
	echo "$prefix: success"
	exit $result
fi
# Otherwise report error.
echo "$prefix: error"
