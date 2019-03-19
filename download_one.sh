#!/bin/bash

# youtube_dl_flags="-r 1M"
YOUTUBE_DL_FORMAT="${YOUTUBE_DL_FORMAT:-"bestvideo/best"}"
YOUTUBE_DL_FLAGS="${YOUTUBE_DL_FLAGS}" # Default is empty string.

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
    # set -x
	set -o pipefail
	youtube-dl \
        -f "${YOUTUBE_DL_FORMAT}" \
        -o '%(id)s.f%(format_id)s.%(ext)s' \
        --newline \
        ${YOUTUBE_DL_FLAGS} \
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
