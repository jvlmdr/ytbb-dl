import argparse
import csv
import numpy as np
import os
import os.path
import subprocess
# import scipy.misc
from PIL import Image

import ytbb
import download

import pdb

# Input: frames/ has structure:
#   frames/{video}/{time}.jpg
#
# Output: crops/ has structure:
#   crops/{video}/{category}-{index}/{time}.jpg

def main():
    parser = argparse.ArgumentParser(description='Extracts clips from larger video')
    parser.add_argument('boxes_file', metavar='boxes.csv')
    parser.add_argument('frame_dir', metavar='frames/')
    parser.add_argument('crop_dir', metavar='crops/')
    parser.add_argument('tmp_dir', metavar='tmp/')
    parser.add_argument('--context', type=float, default=0.5,
        help='Context times mean dimension is padded on all sides')
    parser.add_argument('--context_size', type=int, default=127,
        help='Size of context region')
    parser.add_argument('--search_size', type=int, default=255,
        help='Size of search region')
    args = parser.parse_args()

    print 'read CSV file'
    with open(args.boxes_file, 'r') as f:
        d = split_tracks(f)

    for video_id in d.keys():
        # Confirm that input files exist.
        src_dir = os.path.join(args.frame_dir, video_id)
        if not os.path.isdir(src_dir):
            print '%s: frames not found' % video_id
            continue

        for track_id in d[video_id].keys():
            category, instance = track_id
            track_str = '%s-%d' % (category.replace(' ', '-'), instance)
            prefix = '%s %s: ' % (video_id, track_str)
            # Skip if output directory already exists.
            dst_video_dir = os.path.join(args.crop_dir, video_id)
            dst_track_dir = os.path.join(dst_video_dir, track_str)
            if os.path.isdir(dst_track_dir):
                print prefix + 'skip'
                continue

            print prefix + 'process'
            # objs = [row for row in d[video_id][track_id] if row['object_presence'] == 'present']
            objs = d[video_id][track_id]
            tmp_dir = os.path.join(args.tmp_dir, '%s-%s' % (video_id, track_str))
            create_tmp_dir(tmp_dir)

            crop_objs = []
            for obj in objs:
                if obj['object_presence'] == 'present':
                    fname = obj['timestamp_ms'] + '.jpg'
                    src_im = os.path.join(src_dir, fname)
                    dst_im = os.path.join(tmp_dir, fname)
                    if not os.path.isfile(src_im):
                        print prefix + 'skip missing frame: {}'.format(src_im)
                        continue
                    crop_obj = crop(dst_im, src_im, obj,
                        context=args.context,
                        context_size=args.context_size,
                        search_size=args.search_size)
                else:
                    crop_obj = obj
                crop_objs.append(crop_obj)

            # Write CSV file
            boxes_file = os.path.join(tmp_dir, 'boxes.csv')
            with open(boxes_file, 'w') as f:
                w = csv.DictWriter(f, fieldnames=ytbb.DETECTION_FIELDS)
                for row in crop_objs:
                    w.writerow(row)

            # Ensure that parent directory exists.
            if not os.path.isdir(dst_video_dir):
                os.makedirs(dst_video_dir, 0755)
            # Move from temporary location.
            os.rename(tmp_dir, dst_track_dir)

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

def crop(dst_file, src_file, obj, context=None, context_size=None, search_size=None):
    # Load image and convert relative coords to absolute using its size.
    # im = scipy.misc.imread(src_file)
    # height, width = im.shape[0:2]
    im = Image.open(src_file)
    width, height = im.size
    im_size = np.array((width, height))
    r_min = np.array((float(obj['xmin']), float(obj['ymin'])))
    r_max = np.array((float(obj['xmax']), float(obj['ymax'])))
    # Convert to absolute coordinates.
    r_min = im_size * r_min
    r_max = im_size * r_max

    # Pad on either side to get context size.
    r_size = r_max - r_min
    # Ensure rectangle is not empty.
    r_size = np.maximum(1, r_size)
    c_size = r_size + 2*context*np.mean(r_size)
    c_size = np.exp(np.mean(np.log(c_size)))
    # Get size of search rectangle.
    s_size = c_size * float(search_size) / float(context_size)
    # Get coords of search rectangle.
    r_center = (r_min + r_max) / 2
    s_min = r_center - s_size/2
    s_max = r_center + s_size/2
    # Convert to discrete pixels.
    s_min = np.rint(s_min).astype(int)
    s_max = np.rint(s_max).astype(int)

    # Find intersection of search area with image to give valid search area.
    im_min = np.zeros(2, dtype=int)
    im_max = im_size
    sv_min = np.maximum(s_min, im_min)
    sv_max = np.minimum(s_max, im_max)
    # Find corresponding valid region in output image.
    v_min_rel = np.asfarray(sv_min - s_min) / np.asfarray(s_max - s_min)
    v_max_rel = np.asfarray(sv_max - s_min) / np.asfarray(s_max - s_min)
    ov_min = search_size * v_min_rel
    ov_max = search_size * v_max_rel
    # Convert to discrete pixels.
    ov_min = np.rint(ov_min).astype(int)
    ov_max = np.rint(ov_max).astype(int)

    # Extract valid region.
    # valid = im[sv_min[1]:sv_max[1], sv_min[0]:sv_max[0], :]
    valid = im.crop(box=(sv_min[0], sv_min[1], sv_max[0], sv_max[1]))
    # Resize to valid part of output image.
    # valid = scipy.misc.imresize(valid, ov_max-ov_min)
    valid = valid.resize(size=tuple(ov_max-ov_min), resample=Image.BICUBIC)
    # Compute mean image.
    im_arr = np.array(im)
    # Assert that image data type is integer.
    if not np.issubdtype(im_arr.dtype, np.integer):
        raise ValueError('image type is not integer: {}'.format(im_arr.dtype))
    mean_color = np.rint(np.mean(im_arr, axis=(0, 1))).astype(im_arr.dtype)
    # out_shape = (search_size, search_size, im.shape[2])
    # out = np.zeros(out_shape) + mean_color
    out = Image.new(im.mode, (search_size, search_size), color=tuple(mean_color))
    # out[ov_min[1]:ov_max[1], ov_min[0]:ov_max[0], :] = valid
    out.paste(valid, box=(ov_min[0], ov_min[1], ov_max[0], ov_max[1]))
    out.save(dst_file, quality=90)

    f_center = float(search_size) / 2
    # Final size of object within search image.
    f_size = r_size / s_size * search_size
    f_min = f_center - f_size/2
    f_max = f_center + f_size/2
    f_min_rel = f_min / search_size
    f_max_rel = f_max / search_size

    crop_obj = dict(obj)
    crop_obj['xmin'] = '{:.6f}'.format(f_min_rel[0])
    crop_obj['ymin'] = '{:.6f}'.format(f_min_rel[1])
    crop_obj['xmax'] = '{:.6f}'.format(f_max_rel[0])
    crop_obj['ymax'] = '{:.6f}'.format(f_max_rel[1])
    return crop_obj

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
