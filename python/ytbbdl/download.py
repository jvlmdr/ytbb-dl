import os
import re

import youtube_dl


FORMATS = youtube_dl.extractor.youtube.YoutubeIE._formats

_PATTERN = re.compile(r'^.*\.f(\d+)\..*$')


def find_video_file(d):
    # Find the video file for the given video in a directory.
    files = os.listdir(d)
    video_files = filter(_is_video_file, files)
    if len(video_files) == 0:
        return None
    elif len(video_files) == 1:
        return video_files[0]
    else:
        raise RuntimeError('multiple video formats: ' + str(video_files))


def _is_video_file(fname):
    match = _PATTERN.match(fname)
    if not match:
        return False
    format_id = match.group(1)
    if not format_id in FORMATS:
        raise RuntimeError('unknown format: {}'.format(format_id))
    return _is_video_format(FORMATS[format_id])


def _is_video_format(fmt):
    return 'vcodec' in fmt
