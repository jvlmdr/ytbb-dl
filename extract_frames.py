'''
Extracts the labelled frames from YTBB.

Creates directory structure:
frames-tar/{video}.tar
where each tarball contains:
{video}/{time_sec:05d}.jpg
'''

import argparse
import csv
import os
import os.path
import subprocess
import tarfile
import tempfile
import time

import ytbb
import download


def main():
    parser = argparse.ArgumentParser(description='Extracts frames with boxes')
    parser.add_argument('boxes_file', metavar='boxes.csv')
    parser.add_argument('video_dir', metavar='videos/')
    parser.add_argument('frame_dir', metavar='frames-tar/')
    parser.add_argument('tmp_rename', metavar='tmp-frames-tar/')
    parser.add_argument('tmp_local', metavar='/tmp/')
    parser.add_argument('--max_size', type=int, help='Maximum size of small edge')
    parser.add_argument('--size_str', type=str,
                        help='String to pass to ffmpeg e.g. "200:200", "320:-1"')
    args = parser.parse_args()

    if not os.path.exists(args.tmp_rename):
        os.makedirs(args.tmp_rename, 0o755)

    print('read CSV file: {}'.format(args.boxes_file))
    with open(args.boxes_file, 'r') as f:
        times = extract_times(f)
    if not os.path.isdir(args.frame_dir):
        os.makedirs(args.frame_dir, 0o755)
    for video_id in times.keys():
        dst_file = os.path.join(args.frame_dir, video_id + '.tar')
        if os.path.exists(dst_file):
            print('%s: skip' % video_id)
            continue
        # Confirm that input file exists.
        in_dir = os.path.join(args.video_dir, video_id)
        if not os.path.isdir(in_dir):
            print('%s: video not found' % video_id)
            continue
        # Attempt to find video file.
        video_file = download.find_video_file(in_dir)
        if not video_file:
            raise ValueError('could not find video file: %s' % in_dir)
        video_file = os.path.join(in_dir, video_file)

        video_dst_dir = os.path.join(args.tmp_local, video_id)
        create_tmp_dir(video_dst_dir)
        im_files = decode_frames(video_dst_dir, video_file, times[video_id],
                                 size_str=args.size_str,
                                 max_size=args.max_size)

        tmp_dst_file = os.path.join(args.tmp_rename, video_id + '.tar')
        with tarfile.open(tmp_dst_file, 'w') as tar:
            for im_file in im_files:
                rel_name = os.path.join(video_id, im_file)
                tar.add(os.path.join(args.tmp_local, rel_name), arcname=rel_name)
        # Now rename tar file to final location.
        try:
            os.rename(tmp_dst_file, dst_file)
        except OSError, ex:
            print(ex)


def _try_mkdir(*args):
    try:
        os.mkdir(*args)
    except OSError:
        return False
    return True


def extract_times(r):
    track_times = {}
    reader = csv.DictReader(r, ytbb.DETECTION_FIELDS)
    for row in reader:
        # Ignore frames that are neither present nor absent?
        # if not row['object_present'] in ['present', 'absent']:
        #     continue
        time_ms = int(row['timestamp_ms'])
        if time_ms % 1000 != 0:
            raise RuntimeError('time is not divisible by 1000: {}'.format(time_ms))
        time_sec = time_ms / 1000
        track_id = (row['youtube_id'], row['class_id'], row['object_id'])
        track_times.setdefault(track_id, []).append(time_sec)

    video_times = {}
    for track_id in track_times:
        video_id, _, _ = track_id
        min_time = min(track_times[track_id])
        max_time = max(track_times[track_id])
        video_times.setdefault(video_id, []).extend(range(min_time, max_time + 1))
    # Sort and take unique list.
    return {video_id: list(sorted(set(video_times[video_id]))) for video_id in video_times}


def decode_frames(dst_dir, src_file, times_sec, size_str=None, max_size=0):
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

    dst_files = []
    for t in times_sec:
        # Should check if dst_dir contains '%'
        dst_file = '{:05d}.jpg'.format(t)
        command = (
            ['ffmpeg', '-nostdin', '-v', 'warning'] +
            input_args +
            ['-ss', str(t)] +
            ['-i', src_file] +
            output_args +
            [os.path.join(dst_dir, dst_file)])
        status = subprocess.call(command)
        if status != 0:
            raise ValueError('ffmpeg exit status non-zero: %s' % str(status))
        _wait_for_file_to_exist(os.path.join(dst_dir, dst_file))
        dst_files.append(dst_file)
    return dst_files

    # min_time = min(times_sec)
    # max_time = max(times_sec)

    # input_args = [
    #     '-accurate_seek',
    #     '-ss', str(min_time),
    # ]
    # output_args = [
    #     '-r', '1',
    #     '-vframes', str(max_time - min_time + 1),
    #     '-q:v', '2',
    #     '-start_number', str(min_time),
    # ]
    # if size_str:
    #     output_args += ['-vf', 'scale='+size_str]

    # # Should check if dst_dir contains '%'
    # command = (
    #     ['ffmpeg', '-nostdin', '-v', 'warning'] +
    #     input_args +
    #     ['-i', src_file] +
    #     output_args +
    #     [os.path.join(dst_dir, '%05d.jpg')])
    #     # [os.path.join(dst_dir, dst_file)])
    # status = subprocess.call(command)
    # if status != 0:
    #     raise RuntimeError('ffmpeg exit status non-zero: {}'.format(status))
    # dst_files = ['{:05d}.jpg'.format(t) for t in range(min_time, max_time+1)]
    # return dst_files


def _wait_for_file_to_exist(fname, init_pause=0.01, max_pause=1.0):
    pause = init_pause
    while True:
        if os.path.exists(fname):
            return
        if pause > max_pause:
            raise RuntimeError('file did not start to exist: \'{}\''.format(fname))
        time.sleep(pause)
        pause *= 2


def create_tmp_dir(d):
    if os.path.isdir(d):
        clear_dir(d)
        os.rmdir(d)
    os.makedirs(d, 0o755)


def clear_dir(d):
    # Deletes all files in a directory.
    fs = os.listdir(d)
    for f in fs:
        os.remove(os.path.join(d, f))


def dir_contains_image_files(frames_dir, times):
    video_dir = os.path.join(frames_dir, video)
    if not os.path.isdir(video_dir):
        files = []
    else:
        files = os.listdir(video_dir)
    got = set(fnmatch.filter(files, '*.jpg'))
    want = set('{:05d}.jpg'.format(t) for t in times[video])
    return got == want


if __name__ == '__main__':
    main()
