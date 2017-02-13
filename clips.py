import argparse
import csv
import os
import os.path
import re
import subprocess
import tempfile

# Creates directory structure:
# clips/VIDEO/CATEGORY-INDEX/%06d.jpg
# clips/VIDEO/CATEGORY-INDEX/boxes.csv

# https://research.google.com/youtube-bb/download.html
FIELD_NAMES = ['youtube_id', 'timestamp_ms', 'class_id', 'class_name', 'object_id', 'object_presence', 'xmin', 'xmax', 'ymin', 'ymax']

def main():
    parser = argparse.ArgumentParser(description='Identifies clips')
    parser.add_argument('boxes_file', metavar='boxes.csv')
    parser.add_argument('video_dir', metavar='videos/')
    parser.add_argument('clip_dir', metavar='clips/')
    parser.add_argument('tmp_dir', metavar='tmp/')
    args = parser.parse_args()

    print 'read CSV file'
    with open(args.boxes_file, 'r') as f:
        d = split_tracks(f)

    for video_id in d.keys():
        dst_video = os.path.join(args.clip_dir, video_id)
        if not os.path.isdir(dst_video):
            os.makedirs(dst_video, 0755)

        for track_id in d[video_id].keys():
            track_str = '%s-%d' % track_id
            # Skip if output directory already exists.
            dst_clip = os.path.join(dst_video, track_str)
            if os.path.isdir(dst_clip):
                print '%s: skip' % video_id
                continue
            # Confirm that input file exists.
            in_dir = os.path.join(args.video_dir, video_id)
            if not os.path.isdir(in_dir):
                print '%s: video not found' % video_id
                continue
            # Attempt to find video file.
            video_file = find_video_file(in_dir, video_id)
            if not video_file:
                raise ValueError('could not find video file: %s' % in_dir)

            times = [int(row['timestamp_ms']) for row in d[video_id][track_id]]
            start, end = (float(x)/1e3 for x in [min(times), max(times)])
            tmp_dir = os.path.join(args.tmp_dir, '%s-%s' % (video_id, track_str))
            create_tmp_dir(tmp_dir)
            extract_frames(tmp_dir, video_file, start, end)

            # Write CSV file
            boxes_file = os.path.join(tmp_dir, 'boxes.csv')
            with open(boxes_file, 'w') as f:
                w = csv.DictWriter(f, fieldnames=FIELD_NAMES)
                for row in d[video_id][track_id]:
                    w.writerow(row)

            os.rename(tmp_dir, dst_clip)

def split_tracks(r):
    d = {}
    reader = csv.DictReader(r, FIELD_NAMES)
    for row in reader:
        video_id = row['youtube_id']
        category = row['class_name']
        instance = int(row['object_id'])
        track_id = (category, instance)
        d.setdefault(video_id, {}).setdefault(track_id, []).append(row)
    return d

# https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/youtube.py
VIDEO_FORMATS = {
    5, 6, 13, 17, 18, 22, 34, 35, 36, 37, 38, 43, 44, 45, 46, 59, 78,
    91, 92, 93, 94, 95, 96, 132, 151,
    133, 134, 135, 136, 137, 138, 160, 212, 264, 298, 299, 266,
    167, 168, 169, 170, 218, 219, 278, 242, 243, 244, 245, 246, 247, 248, 271, 272, 302, 303, 308, 313, 315}

def find_video_file(d, video_id):
    # Find the video file for the given video in a directory.
    files = os.listdir(d)
    if not files:
        return None
    r = re.compile(r'^%s\.f(\d+)\..*$' % video_id)
    matches = [r.match(s) for s in files]
    matches = [m for m in matches if m]
    if not matches:
        return None
    matches = [m.group(0) for m in matches if int(m.group(1)) in VIDEO_FORMATS]
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError('multiple video formats: ' + str(matches))
    return os.path.join(d, matches[0])

def extract_frames(dst_dir, video_file, start, end):
    # Add 1 second to end.
    start_num = round(start * 30)
    num_frames = round(30 * (end - start + 1))
    # Should check if dst_dir contains '%'
    status = subprocess.call(['ffmpeg',
        '-v', 'warning',
        '-accurate_seek',
        '-ss', str(start),
        '-i', video_file,
        '-r', '30',
        '-vframes', str(num_frames),
        '-q:v', '2',
        '-start_number', str(start_num),
        os.path.join(dst_dir, '%08d.jpg')])
    if status != 0:
        raise ValueError('ffmpeg exit status non-zero: %s' % str(status))

def create_tmp_dir(d):
    if os.path.isdir(d):
        clear_dir(d)
        os.rmdir(d)
    os.makedirs(d, 0755)

def clear_dir(d):
    # Deletes all files in a directory.
    fs = os.listdir(d)
    for f in fs:
        os.remove(os.path.join(d, f))

if __name__ == '__main__':
    main()
