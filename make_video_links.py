import argparse
import os
import progressbar

import download

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('download_dir', metavar='download/')
    parser.add_argument('video_dir', metavar='video/')
    args = parser.parse_args()

    with open(os.path.join(args.download_dir, 'videos.txt'), 'r') as f:
        videos = [line.strip() for line in f if line]

    bar = progressbar.ProgressBar()
    for video in bar(videos):
        original_dir = os.path.join(args.download_dir, 'complete', video)
        if not os.path.exists(original_dir):
            continue
        video_file = download.find_video_file(original_dir)
        if video_file is None:
            continue
        _, ext = os.path.splitext(video_file)
        os.symlink(
            os.path.join(original_dir, video_file),
            os.path.join(args.video_dir, video+ext))


if __name__ == '__main__':
    main()
