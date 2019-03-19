#!/bin/bash

NUM_PARALLEL="${NUM_PARALLEL:-16}"

if [[ $# -ne 2 ]]; then
	echo "usage: $0 dst/ labels.csv"
	exit 1
fi
dst="$(readlink -m "$1")"
labels="$2"

# Directory dst will have structure:
# dst/videos.txt
# dst/partial/
# dst/complete/

mkdir -p "$dst"/{partial,complete}
if [ ! -f "$dst/videos.txt" ]; then
	cut -d, -f1 <"$labels" | uniq >"$dst/videos.txt"
fi

(
    cd "$dst"
    # Videos that are missing from YouTube.
    # Clear partial/ to try again.
    find partial/ -name err.txt -print0 | xargs -0 grep -l 'ERROR:.*YouTube said:' | \
        awk '-F/' '{print $2}' >missing.txt
    echo "number of unavailable videos: $(wc -l missing.txt)"
    # Get list of videos that are not missing and not complete.
    comm -23 <(cat videos.txt | sort) <(cat <(ls complete) missing.txt | sort) >remain.txt
    echo "number of available videos that remain: $(wc -l remain.txt)"
)
# Download!
cat "$dst/remain.txt" | shuf | xargs -n 1 -P "${NUM_PARALLEL}" ./download_one.sh "$dst"
