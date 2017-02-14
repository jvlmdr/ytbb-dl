import argparse
import csv
import os
import os.path

import ytbb

# Creates directory structure:
# boxes/{video}.csv

def main():
    parser = argparse.ArgumentParser(description='Splits the dataset CSV file into one file per video')
    parser.add_argument('boxes_file', metavar='boxes.csv')
    parser.add_argument('box_dir', metavar='boxes/')
    args = parser.parse_args()

    print 'read CSV file'
    with open(args.boxes_file, 'r') as f:
        d = split_videos(f)

    if not os.path.isdir(args.box_dir):
        os.makedirs(args.box_dir, 0755)

    for i, video_id in enumerate(d.keys()):
        progress = '%d / %d: %s' % (i+1, len(d), video_id)
        print progress
        fname = os.path.join(args.box_dir, video_id+'.csv')
        with open(fname, 'w') as f:
            w = csv.DictWriter(f, fieldnames=ytbb.DETECTION_FIELDS)
            for row in d[video_id]:
                w.writerow(row)

def split_videos(r):
    d = {}
    reader = csv.DictReader(r, ytbb.DETECTION_FIELDS)
    for row in reader:
        video_id = row['youtube_id']
        d.setdefault(video_id, []).append(row)
    return d

if __name__ == '__main__':
    main()
