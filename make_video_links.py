import argparse
import os

from ytbbdl import download


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('download_dir', metavar='download/')
    parser.add_argument('video_dir', metavar='video/')
    args = parser.parse_args()

    with open(os.path.join(args.download_dir, 'videos.txt'), 'r') as f:
        videos = [line.strip() for line in f if line]

    if not os.path.exists(args.video_dir):
        os.makedirs(args.video_dir, 0o755)

    for i, video in enumerate(videos):
        print('video {} of {}: {}'.format(i + 1, len(videos), video))
        original_dir = os.path.join(args.download_dir, 'complete', video)
        if not os.path.exists(original_dir):
            continue
        video_file = download.find_video_file(original_dir)
        if video_file is None:
            continue
        # _, ext = os.path.splitext(video_file)
        # os.symlink(
        #     os.path.join(original_dir, video_file),
        #     os.path.join(args.video_dir, video+ext))
        _symlink_rel(
            os.path.join(original_dir, video_file),
            os.path.join(args.video_dir, video_file))


def _symlink_rel(source, link_name):
    source_rel = os.path.relpath(source, os.path.dirname(link_name))
    return os.symlink(source_rel, link_name)


if __name__ == '__main__':
    main()
