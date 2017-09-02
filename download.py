import os
import os.path
import re

import youtube_dl

VIDEO_FORMATS = {
    k for k, v in youtube_dl.extractor.youtube.YoutubeIE._formats.items()
    if 'vcodec' in v
}

pattern = re.compile(r'^.*\.f(\d+)\..*$')

def find_video_file(d):
    # Find the video file for the given video in a directory.
    files = os.listdir(d)
    if not files:
        return None
    matches = [pattern.match(s) for s in files]
    matches = [m for m in matches if m]
    if not matches:
        return None
    matches = [m.group(0) for m in matches if m.group(1) in VIDEO_FORMATS]
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError('multiple video formats: ' + str(matches))
    return matches[0]
