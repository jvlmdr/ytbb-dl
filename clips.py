import argparse
import csv
import os
import os.path
import re
import subprocess

def main():
    parser = argparse.ArgumentParser(description='Identifies clips')
    parser.add_argument('labels_file', metavar='labels.csv')
    parser.add_argument('video_dir', metavar='videos/')
    parser.add_argument('image_dir', metavar='images/')
    args = parser.parse_args()

    print 'read CSV file'
    with open(args.labels_file, 'r') as r:
        d = split_tracks(r)

    for video_id in d.keys():
        for track_id in d[video_id].keys():
            times = d[video_id][track_id]
            start_time = float(min(times)) / 1e3
            end_time = float(max(times)) / 1e3
            # Add 1 second to end_time.
            num_frames = round(30 * (end_time - start_time + 1))
            in_dir = os.path.join(args.video_dir, video_id)
            video_file = find_video_file(in_dir, video_id)
            if not video_file:
                print 'could not find video file:', video_id
                continue

            track_str = '%s-%d' % track_id
            out_dir = os.path.join(args.image_dir, video_id, track_str)
            if not os.path.isdir(out_dir):
                os.makedirs(out_dir, 0755)
            # Should check if out_dir contains %
            status = subprocess.call(['ffmpeg',
                '-v', 'warning',
                '-accurate_seek',
                '-ss', str(start_time),
                '-i', os.path.join(in_dir, video_file),
                '-r', '30',
                '-vframes', str(num_frames),
                '-qscale:v', '2',
                os.path.join(out_dir, '%06d.jpeg')])
            print "status:", status

def split_tracks(r):
    d = {}
    reader = csv.reader(r)
    for row in reader:
        video_id = row[0]
        time = int(row[1])
        category = row[3]
        instance = int(row[4])
        track_id = (category, instance)
        d.setdefault(video_id, {}).setdefault(track_id, []).append(time)
    return d

# https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/youtube.py
VIDEO_FORMATS = {
    5, 6, 13, 17, 18, 22, 34, 35, 36, 37, 38, 43, 44, 45, 46, 59, 78,
    91, 92, 93, 94, 95, 96, 132, 151,
    133, 134, 135, 136, 137, 138, 160, 212, 264, 298, 299, 266,
    167, 168, 169, 170, 218, 219, 278, 242, 243, 244, 245, 246, 247, 248, 271, 272, 302, 303, 308, 313, 315}

def find_video_file(p, video_id):
    # Find the video file for the given video in a directory.
    if not os.path.isdir(p):
        return None
    files = os.listdir(p)
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
    return matches[0]

if __name__ == '__main__':
    main()
