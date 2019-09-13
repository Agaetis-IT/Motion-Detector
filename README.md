# Motion Detector

Motion detection and video capture from two video stream (a detector and a record source) using Python, OpenCV and Docker.
It is possible to use same source for both detect and record video.

One video file per detection event is recorded.

# To use it:

Clone repo in your working directory

Build docker image:

> docker build -t motion-det .

Configure script (see bellow)

Launch script:

> bash runDocker.sh

CAUTION: In runDocker.sh, be careful to declare video devices correctly. E.g, if you have one video device set:

> --device=/dev/video0

if you have two devices:

> --device=/dev/video0 --device=/dev/video1

# To configure it:

Configuration is made in exec.sh at python function call:

> python3 motion_detector.py ...

All possible arguments are:

```
-a (--min-area): type=int, default=5000: minimum area size used to trigger motion

-r (--refresh-delay): type=int, default=5: Reference Frame refresh delay (s)

-d (--detection-release): type=int, default=5: Detection release (s) e.g. delay to stop record after the last motion detected

-c (--output-codec): type=str, default="mkv": Ouput video codec. Supported codec (for now): "mkv" and "avi"

-l (--display-level): type=int, default=0: Display level (0: no display)

--record-camera: type=int, default=0: Record device (720p)

--detector-camera: type=int, default=0: detector device (480p)
```

Outputs file are in outputs/ folder
