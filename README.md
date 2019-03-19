

## How to use scripts

Initial directory structure:

```
$ROOT/
  yt_bb_detection_train.csv
  yt_bb_detection_validation.csv
  train/
  validation/
```

Note: Use `bash` and `xargs` to do slow things in parallel, and use `python` to do more involved tasks.

### Download videos

The following command will try to download all videos.
It will not re-download videos that have been succesfully downloaded.
It will also resume partial downloads that were interrupted.

```bash
$ download.sh $ROOT/train/download/ $ROOT/yt_bb_detection_train.csv
```

This script will create:

```
$ROOT/train/download/
  videos.txt
  complete/
  partial/
```

The video and audio will be saved in `complete/[VIDEO]/[VIDEO].f[FORMAT].[EXT]`.

The script `download.sh` invokes `download_one.sh` many times in parallel using `xargs -P`.
To change the number of parallel processes, change `$num_parallel` in `download.sh`.
To modify the resolution that is downloaded, change `$format` in `download_one.sh`.

It is not obvious which file is the video and which is the audio.
The script `make_video_links.py` can be used to create a directory with a single file per video.

```bash
$ python make_video_links.py $ROOT/train/download/ $ROOT/train/download/video/
```
