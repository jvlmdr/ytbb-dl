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
    parser = argparse.ArgumentParser(description='Extracts clips from larger video')
    parser.add_argument('boxes_file', metavar='boxes.csv')
    parser.add_argument('video_dir', metavar='videos/')
    parser.add_argument('clip_dir', metavar='clips/')
    parser.add_argument('tmp_dir', metavar='tmp/')
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--video_codec', type=str)
    parser.add_argument('--video_ext', type=str)
    parser.add_argument('--max_size', type=int,
        help='Maximum size of small edge of video')
    args = parser.parse_args()

    print 'read CSV file'
    with open(args.boxes_file, 'r') as f:
        d = split_tracks(f)

    for video_id in d.keys():
        # Confirm that input file exists.
        in_dir = os.path.join(args.video_dir, video_id)
        if not os.path.isdir(in_dir):
            print '%s: video not found' % video_id
            continue
        # Attempt to find video file.
        video_file = download.find_video_file(in_dir)
        if not video_file:
            raise ValueError('could not find video file: %s' % in_dir)
        video_path = os.path.join(in_dir, video_file)

        # Video directory.
        dst_video = os.path.join(args.clip_dir, video_id)

        for track_id in d[video_id].keys():
            category, instance = track_id
            track_str = '%s-%d' % (category.replace(' ', '-'), instance)
            prefix = '%s %s' % (video_id, track_str)
            # Skip if output directory already exists.
            dst_clip = os.path.join(dst_video, track_str)
            if os.path.isdir(dst_clip):
                print '%s: skip' % prefix
                continue

            print '%s: process' % prefix
            times = [int(row['timestamp_ms']) for row in d[video_id][track_id]]
            start, end = (float(x)/1e3 for x in [min(times), max(times)])
            # Add one second to allow frames to be processed with a lag.
            end += 1
            tmp_dir = os.path.join(args.tmp_dir, '%s-%s' % (video_id, track_str))
            create_tmp_dir(tmp_dir)

            out_path = None
            if args.video:
                # Use user-specified extension if given.
                if args.video_ext:
                    ext = ensure_starts_with_dot(args.video_ext)
                else:
                    _, ext = os.path.splitext(video_file)
                out_path = os.path.join(tmp_dir, track_str+ext)
            else:
                out_path = os.path.join(tmp_dir, '%08d.jpg')

            cut_video_interval(out_path, video_path, start, end,
                               video=args.video,
                               max_size=args.max_size,
                               codec=args.video_codec)

            # Write CSV file
            boxes_file = os.path.join(tmp_dir, 'boxes.csv')
            with open(boxes_file, 'w') as f:
                w = csv.DictWriter(f, fieldnames=ytbb.DETECTION_FIELDS)
                for row in d[video_id][track_id]:
                    w.writerow(row)

            # Ensure that parent directory exists.
            if not os.path.isdir(dst_video):
                os.makedirs(dst_video, 0755)
            # Move from temporary location.
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

def cut_video_interval(dst_file, src_file, start, end, video=False, max_size=0, codec=None):
    start_num = round(start * 30)
    num_frames = round(30 * (end-start)) + 1
    # Unless otherwise specified, use same codec as input.
    if not codec:
        codec = 'copy'

    size_args = []
    if max_size:
        w_str = 'min(iw\,max({0}\,iw*{0}/ih))'.format(max_size)
        h_str = 'min(ih\,max(ih*{0}/iw\,{0}))'.format(max_size)
        if video:
            # Round to nearest multiple of 2.
            w_str = '2*trunc((1+({}))/2)'.format(w_str)
            h_str = '2*trunc((1+({}))/2)'.format(h_str)
        size_args = ['-vf', 'scale=w={}:h={}'.format(w_str, h_str)]

    if video:
        input_args = [
            '-accurate_seek',
            '-ss', str(start),
            '-t', str(end - start),
        ]
        output_args = [
            '-vcodec', codec,
            '-an',
        ]
        output_args += size_args
    else:
        input_args = [
            '-accurate_seek',
            '-ss', str(start),
        ]
        output_args = [
            '-r', '30',
            '-vframes', str(num_frames),
            '-q:v', '2',
            '-start_number', str(start_num),
        ]
        output_args += size_args

    command = ['ffmpeg', '-nostdin'] + input_args + ['-i', src_file] + output_args + [dst_file]
    status = subprocess.call(command)
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

def ensure_starts_with_dot(ext):
    if ext[0] == '.':
        return ext
    return '.' + ext

if __name__ == '__main__':
    main()
