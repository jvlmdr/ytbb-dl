import os
import os.path
import re

# https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/youtube.py
VIDEO_FORMATS = {
    5, 6, 13, 17, 18, 22, 34, 35, 36, 37, 38, 43, 44, 45, 46, 59, 78,
    91, 92, 93, 94, 95, 96, 132, 151,
    133, 134, 135, 136, 137, 138, 160, 212, 264, 298, 299, 266,
    167, 168, 169, 170, 218, 219, 278, 242, 243, 244, 245, 246, 247, 248, 271, 272, 302, 303, 308, 313, 315,
    213}

# def find_video_file(d, video_id):
#     # Find the video file for the given video in a directory.
#     files = os.listdir(d)
#     if not files:
#         return None
#     r = re.compile(r'^%s\.f(\d+)\..*$' % video_id)
#     matches = [r.match(s) for s in files]
#     matches = [m for m in matches if m]
#     if not matches:
#         return None
#     matches = [m.group(0) for m in matches if int(m.group(1)) in VIDEO_FORMATS]
#     if not matches:
#         return None
#     if len(matches) > 1:
#         raise ValueError('multiple video formats: ' + str(matches))
#     return matches[0]

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
    matches = [m.group(0) for m in matches if int(m.group(1)) in VIDEO_FORMATS]
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError('multiple video formats: ' + str(matches))
    return matches[0]
