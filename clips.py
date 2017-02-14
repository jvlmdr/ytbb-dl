import argparse
import csv
import os
import os.path
import subprocess

import ytbb
import download

# Creates directory structure:
# clips/{video}/{category}-{index}/{frame}.jpg
# clips/{video}/{category}-{index}/boxes.csv

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
            video_file = download.find_video_file(in_dir)
            if not video_file:
                raise ValueError('could not find video file: %s' % in_dir)
            video_file = os.path.join(in_dir, video_file)

            times = [int(row['timestamp_ms']) for row in d[video_id][track_id]]
            start, end = (float(x)/1e3 for x in [min(times), max(times)])
            tmp_dir = os.path.join(args.tmp_dir, '%s-%s' % (video_id, track_str))
            create_tmp_dir(tmp_dir)
            # Add one second to the end to allow a lag.
            decode_frames_interval(tmp_dir, video_file, start, end+1)

            # Write CSV file
            boxes_file = os.path.join(tmp_dir, 'boxes.csv')
            with open(boxes_file, 'w') as f:
                w = csv.DictWriter(f, fieldnames=ytbb.DETECTION_FIELDS)
                for row in d[video_id][track_id]:
                    w.writerow(row)

            os.rename(tmp_dir, dst_clip)

def split_tracks(r):
    d = {}
    reader = csv.DictReader(r, ytbb.DETECTION_FIELDS)
    for row in reader:
        video_id = row['youtube_id']
        category = row['class_name']
        instance = int(row['object_id'])
        track_id = (category, instance)
        d.setdefault(video_id, {}).setdefault(track_id, []).append(row)
    return d

def decode_frames_interval(dst_dir, video_file, start, end):
    start_num = round(start * 30)
    num_frames = round(30 * (end-start)) + 1
    # Should check if dst_dir contains '%'
    status = subprocess.call(['ffmpeg',
        '-v', 'warning',
        '-accurate_seek',
        '-ss', str(start),
        '-i', video_file,
        '-r', '30',
        '-vframes', str(num_frames),
        '-q:v', '2',
        '-vf', 'scale=-1:min(360,ih)',
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
