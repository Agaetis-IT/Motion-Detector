# import the necessary packages
import argparse
import datetime
import imutils
from utils.app_utils import WebcamVideoStream
import time
import cv2

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-a", "--min-area", type=int, default=5000,
                help="minimum area size")
ap.add_argument("-r", "--refresh-delay", type=int, default=5,
                help="Refresh delay (s)")
ap.add_argument("-d", "--detection-release", type=int, default=5,
                help="Detection release (s)")
ap.add_argument("-c", "--output-codec", type=str, default="mkv",
                help="Ouput video codec")
ap.add_argument("-l", "--display-level", type=int, default=0,
                help="Display level (0: no display)")
ap.add_argument("--record-camera", "--record-camera", type=int,
                default=0, help="Record device (720p)")
ap.add_argument("--detector-camera", "--detector-camera", type=int,
                default=0, help="detector device (480p)")
args = vars(ap.parse_args())

# Get input video stream(s)
print("Start video stream(s)")
detector_vs = None
record_vs = WebcamVideoStream(src=args['record_camera'], HD=True).start()
print("record device: FPS {} / Width {} / Height {}".format(
        record_vs.getFPS(), record_vs.getWidth(), record_vs.getHeight()))

if args['detector_camera'] != args['record_camera']:
        detector_vs = WebcamVideoStream(src=args['detector_camera']).start()
        print("detector device: FPS {} / Width {} / Height {}".format(
                detector_vs.getFPS(), detector_vs.getWidth(),
                detector_vs.getHeight()))
time.sleep(2.0)

# Define the output codec and create VideoWriter object
if args['output_codec'] == "avi":
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # avi
elif args['output_codec'] == "mkv":
        fourcc = cv2.VideoWriter_fourcc(*'X264')  # mkv
else:
        print("ERROR: {} is not an available codec, set mkv".format(
                args['output_codec']))
        fourcc = cv2.VideoWriter_fourcc(*'X264')  # mkv

# initialization parameters
refFrame = None
detectionNumber = 0
nFrames = 0
tLastRefresh = time.time()
tLastDetection = time.time()
tStartEvent = time.time()
text = "Motionless"
record = False

# loop over the frames of the video
print("Starting detection")
while True:
        # Update timer
        t = time.time()

        # grab the current frame from detector input if defined
        if detector_vs is None:
                ret, frame_dry = record_vs.read()
        else:
                ret, frame_dry = detector_vs.read()

        # if the frame could not be grabbed, there is an error: stop program
        if frame_dry is None:
                break

        # resize the frame, convert it to grayscale, and blur it
        frame = imutils.resize(frame_dry, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Refresh reference (and release video if detection occurs)
        if (refFrame is None) | (t - tLastRefresh > args['refresh_delay']):
                tLastRefresh = time.time()
                refFrame = gray

        # compute the absolute difference between the
        #    current frame and reference frame
        frameDelta = cv2.absdiff(refFrame, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

        # dilate the thresholded image to fill in holes,
        #    then find contour on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # loop over the contours
        text = "Motionless"
        for c in cnts:
                # if the contour is too small, ignore it
                if cv2.contourArea(c) < args["min_area"]:
                        continue

                # compute the bounding box for the contour,
                #    draw it on the frame and update the text
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                text = "Motion"
                if not record:
                        print("Motion detected: Event #{}".format(
                                detectionNumber))
                        tStartEvent = time.time()
                        out = cv2.VideoWriter('outputs/{}.{}'.format(
                                detectionNumber, args['output_codec']),
                                              fourcc, 30,
                                              (record_vs.getWidth(),
                                               record_vs.getHeight()))
                        record = True
                tLastDetection = time.time()

        # Close record if over release time
        if record & (t - tLastDetection > args['detection_release']):
                print("Release video of event #{} ({} frames, {} s)".format(
                        detectionNumber, nFrames, round(t - tStartEvent)))
                out.release()
                detectionNumber += 1
                nFrames = 0
                record = False

        # draw the text and timestamp on the frame
        cv2.putText(frame, "Room Status: {}".format(text), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, datetime.datetime.now().strftime(
                "%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        # show the frame and record if the user presses a key
        if args['display_level'] > 0:
                cv2.imshow("Security Feed", frame)
                cv2.imshow("Thresh", thresh)
                cv2.imshow("Frame Delta", frameDelta)
        key = cv2.waitKey(1) & 0xFF

        # write the frame
        if record:
                if detector_vs is not None:
                        ret, frame_dry = record_vs.read()
                cv2.putText(frame_dry, "Room Status: {}".format(text),
                            (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 255), 2)
                cv2.putText(frame_dry, datetime.datetime.now().strftime(
                        "%A %d %B %Y %I:%M:%S%p"),
                            (10, frame_dry.shape[0] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)
                nFrames += 1
                out.write(frame_dry)

        # if the `q` key is pressed, break from the lop
        if key == ord("q"):
                break

# cleanup the camera and close any open windows
record_vs.stop()
if detector_vs is not None:
        detector_vs.stop()
cv2.destroyAllWindows()
