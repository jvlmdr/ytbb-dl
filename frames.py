import argparse
import csv
import os
import os.path
import subprocess
import tempfile

import ytbb
import download

# Creates directory structure:
# frames/{video}/{time_ms}.jpg

def main():
    parser = argparse.ArgumentParser(description='Extracts frames with boxes')
    parser.add_argument('boxes_file', metavar='boxes.csv')
    parser.add_argument('video_dir', metavar='videos/')
    parser.add_argument('frame_dir', metavar='frames/')
    parser.add_argument('tmp_dir', metavar='tmp/')
    parser.add_argument('--max_size', type=int, help='Maximum size of small edge')
    parser.add_argument('--size_str', type=str, help='String to pass to ffmpeg e.g. "200:200", "320:-1"')
    args = parser.parse_args()

    print 'read CSV file'
    with open(args.boxes_file, 'r') as f:
        d = extract_frames(f)
    if not os.path.isdir(args.frame_dir):
        os.makedirs(args.frame_dir, 0755)
    for video_id in d.keys():
        dst_dir = os.path.join(args.frame_dir, video_id)
        if os.path.isdir(dst_dir):
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

        times = [float(x)/1e3 for x in d[video_id]]
        tmp_dir = os.path.join(args.tmp_dir, video_id)
        create_tmp_dir(tmp_dir)
        decode_frames(tmp_dir, video_file, times,
                      size_str=args.size_str,
                      max_size=args.max_size)

        os.rename(tmp_dir, dst_dir)

def extract_frames(r):
    d = {}
    reader = csv.DictReader(r, ytbb.DETECTION_FIELDS)
    for row in reader:
        video_id = row['youtube_id']
        d.setdefault(video_id, set()).add(int(row['timestamp_ms']))
    return d

def decode_frames(dst_dir, src_file, times, size_str=None, max_size=0):
    if not size_str:
        if max_size:
            w_str = 'min(iw\,max({0}\,iw*{0}/ih))'.format(max_size)
            h_str = 'min(ih\,max(ih*{0}/iw\,{0}))'.format(max_size)
            size_str = 'w={}:h={}'.format(w_str, h_str)

    input_args = [
        '-accurate_seek',
    ]
    output_args = [
        '-vframes', '1',
        '-q:v', '2',
    ]
    if size_str:
        output_args += ['-vf', 'scale='+size_str]

    for t in times:
        # Should check if dst_dir contains '%'
        dst_file = os.path.join(dst_dir, '%d.jpg' % int(round(1000*t)))
        command = (
            ['ffmpeg', '-nostdin', '-v', 'warning'] +
            input_args +
            ['-ss', str(t)] +
            ['-i', src_file] +
            output_args +
            [dst_file])
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

if __name__ == '__main__':
    main()
