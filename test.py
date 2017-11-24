import numpy as np
import cv2
import sys
from Hardware import *
import MouseInteraction as mouse
from Colour import Colour
import OpenCVHelpers as cvh
from framespersecond import FramesPerSecond
import time
from videostream import VideoStream
from BallTracker import BallTracker
from OctaveGrid import OctaveGrid
from soundsocketserver import SoundSocketServer
from simplewebserver import *
from web import *
from propertiesopencvui import *
from transitions import Machine  # https://github.com/pytransitions/transitions


def setup_pygame_mixer():
    pass


def nothing(x):
    pass


the_kernel = None


def load_colours(colours):
    for colour in colours:
        create_colour_ui(colour.name)
        colour.load_from_file()
        set_colour_ui_values(colour.name, colour.low, colour.high)


def morph_kernel():
    global the_kernel
    if the_kernel is None:
        the_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # RPI cannot handle large kernels....
        the_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    return the_kernel


def track_colour(input_frame_hsv, lower_range, higher_range):
    mask = cv2.inRange(input_frame_hsv, lower_range, higher_range)

    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel=morph_kernel(), iterations=1)
    #  mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel=morph_kernel(), iterations=2)

    # http://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
    # we use external so any small 'gaps' are ignored, e.g. a highlight for example within a sphere..
    image, contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return mask, contours


def create_colour_ui(name):
    cv2.namedWindow(name)
    cv2.createTrackbar('H_LOW', name, 0, 255, nothing)
    cv2.createTrackbar('S_LOW', name, 0, 255, nothing)
    cv2.createTrackbar('V_LOW', name, 0, 255, nothing)
    cv2.createTrackbar('H_HIGH', name, 0, 255, nothing)
    cv2.createTrackbar('S_HIGH', name, 0, 255, nothing)
    cv2.createTrackbar('V_HIGH', name, 0, 255, nothing)


def set_colour_ui_values(name, low, high):
    cv2.setTrackbarPos('H_LOW', name, low[0])
    cv2.setTrackbarPos('S_LOW', name, low[1])
    cv2.setTrackbarPos('V_LOW', name, low[2])
    cv2.setTrackbarPos('H_HIGH', name, high[0])
    cv2.setTrackbarPos('S_HIGH', name, high[1])
    cv2.setTrackbarPos('V_HIGH', name, high[2])


def get_colour_ui_values(name):
    return (
        [
            cv2.getTrackbarPos('H_LOW', name),
            cv2.getTrackbarPos('S_LOW', name),
            cv2.getTrackbarPos('V_LOW', name)
        ],
        [
            cv2.getTrackbarPos('H_HIGH', name),
            cv2.getTrackbarPos('S_HIGH', name),
            cv2.getTrackbarPos('V_HIGH', name)
        ])


DRAW_ALL = -1


def find_coloured_balls(frame, colours):
    # this is SLOW apparantly - check 
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    min_enclosing = get_ui('min_enclosing')
    max_enclosing = get_ui('max_enclosing')

    show_masks = get_ui('show_masks')
    min_area = get_ui('min_area')

    new_balls = []

    for colour in colours:
        mask, contours = track_colour(hsv, colour.low_as_numpy, colour.high_as_numpy)
        colour.mask = mask
        colour.contours = contours
        if show_masks > 50:
            cv2.imshow('mask_' + colour.name, mask)

        for contour in colour.contours:

            is_valid = True

            (x, y), radius = cv2.minEnclosingCircle(contour)

            col = (0, 0, 255)
            if min_enclosing < radius < max_enclosing:
                col = (255, 255, 0)  # is valid
            else:
                is_valid = False

            area = 0
            if is_valid:
                area = cv2.contourArea(contour)
                if area < (min_area * min_area):
                    is_valid = False

            if is_valid:
                # do some other stuff to validate...

                cv2.drawContours(frame, [contour], DRAW_ALL, colour.rgb)

                center = (int(x), int(y))

                cv2.circle(frame, center, int(radius), col, thickness=1)
                # cv2.circle(frame, (int(x), int(y)), 4, (255, 255, 0), thickness=cv2.FILLED)

                # moments = cv2.moments(contour)

                # m00 = moments["m00"]
                # if m00 != 0:
                #   center = (int(moments["m10"] / m00), int(moments["m01"] / m00))

                #  cv2.circle(img=frame, center=center, radius=3, color=(0, 0, 255), thickness=cv2.FILLED)



                new_balls.append((colour, radius, (x, y), area))

    return frame, new_balls
    # mask = cv2.bitwise_or(maskgreen, maskblue)

    # Bitwise-AND mask and original image
    # res = cv2.bitwise_and(frame, frame, mask=blue_mask)
    # filter on size...
    # http://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_houghcircles/py_houghcircles.html
    # circles = cv2.HoughCircles(blue_mask, cv2.HOUGH_GRADIENT, 1, 20,
    #    param1=50, param2=30, minRadius=0, maxRadius=0)
    # if circles is not None and len(circles) > 0:
    #     print(str(len(circles)))

    # circles = np.uint16(np.around(circles))
    # for i in circles[0, :]:
    #     # draw the outer circle
    # cv2.circle(res, (i[0], i[1]), i[2], (0, 255, 0), 2)
    #    # draw the center of the circle
    #    cv2.circle(res, (i[0], i[1]), 2, (0, 0, 255), 3)


    # cv2.imshow('maskblue', blue_mask)
    #    cv2.imshow('maskgreen', maskgreen)
    # cv2.imshow('res', res)

    # Display the resulting frame
    # cv2.rectangle(grey, (0, 0), (20, 20), (255, 255, 255), 5)

    #    cv2.imshow('frame',grey)

    # class Prop:
    #     def __init__(self, name, min_val, max_val, cur_val, group='ui'):
    #         self.name = name
    #         self.min_value = min_val
    #         self.max_value = max_val
    #         self.cur_value = cur_val
    #         self.range_value = self.max_value - self.min_value
    #         self.group = group


def prep_ui(name='ui'):
    cv2.namedWindow(name)
    cv2.createTrackbar('blur', name, 0, 255, nothing)
    cv2.createTrackbar('min_enclosing', name, 0, 255, nothing)
    cv2.setTrackbarPos('min_enclosing', name, 5)
    cv2.createTrackbar('max_enclosing', name, 0, 800, nothing)
    cv2.setTrackbarPos('max_enclosing', name, 200)
    cv2.createTrackbar('show_masks', name, 0, 400, nothing)
    cv2.setTrackbarPos('show_masks', name, 50)
    cv2.createTrackbar('min_area', name, 0, 400, nothing)
    cv2.setTrackbarPos('min_area', name, 6)

    #  cv2.createTrackbar('iso', name, 0, 800, nothing)
    #  cv2.setTrackbarPos('iso', name, 200)
    #  cv2.createTrackbar('shutter_speed', name, 0, 800000, nothing)
    #  cv2.setTrackbarPos('shutter_speed', name, 160000)
    #  cv2.createTrackbar('brightness', name, 0, 100, nothing)
    #  cv2.setTrackbarPos('brightness', name, 50)
    #  cv2.createTrackbar('contrast', name, 0, 200, nothing)
    #  cv2.setTrackbarPos('contrast', name, 100)
    #  cv2.createTrackbar('sharpness', name, 0, 200, nothing)
    #  cv2.setTrackbarPos('sharpness', name, 100)
    cv2.createTrackbar('saturation', name, 0, 200, nothing)
    cv2.setTrackbarPos('saturation', name, 100)


def get_ui(name, window_name='ui'):
    return cv2.getTrackbarPos(name, window_name)


server = None


def process_frame(colours, frame, ball_tracker, original, grid):
    global server
    # global guitar
    # get UI values before frame update
    for colour in colours:
        low, high = get_colour_ui_values(colour.name)
        colour.update(low, high)


        # we should blur
        # cv2
    blur = get_ui('blur')
    if blur > 0:
        # force uneven.
        if blur % 2 == 0:
            blur = blur + 1
        frame = cv2.GaussianBlur(frame, (blur, blur), 0)
        # might be useful - not sure on RPI

    # frame = cv2.bilateralFilter(frame, 9, 75, 75)  # might be better

    # frame = cv2.medianBlur(frame, 15)

    # todo - only when sampling...

    # if original is not None:
    #    diff = cv2.absdiff(original, frame)
    #    cv2.imshow('diff', diff)

    # 

    # do the processing
    frame, new_balls = find_coloured_balls(frame, colours)

    ball_tracker.update(new_balls)

    # cv2.subtract()

    grid_messages = []

    grid.draw(frame)

    for ball in ball_tracker.balls:
        x = int(ball.pos[0])
        y = int(ball.pos[1])
        cvh.draw_text(frame, str(ball.id), (x, y))

        division = grid.pos_to_division(x, y)

        dx, dy, ok = division

        location = (dx, dy)

        should_play = False

        if ok:
            if (ball.division is None):
                should_play = True
            elif ball.division != location:
                should_play = True
            ball.division = location

            if should_play:
                grid_messages.append((ball.colour.name, ball.area_of_circle(), dx, dy))
                # note = 0 + (dx * 1) + (dy * 12)
                # size = ((ball.area_of_circle() / (frame.shape[0]*frame.shape[1]) * 100.0))
                # for client in server.clients:
                #    client.sendMessage(ball.colour.name+','+str(note)+','+str(size))

        grid.draw_division_cell(frame, dx, dy, ok)

    return frame, grid_messages


IS_RASPBERRY_PI = is_raspberry_pi()

state = 'none'
stabilizing_counter = 0


def start_state(new_state):
    global state
    print("change state from " + state + " -> " + new_state)
    state = new_state


def start_stabilize(vs):
    global stabilizing_counter
    global IS_RASPBERRY_PI
    start_state('stabilize')
    stabilizing_counter = 0
    if IS_RASPBERRY_PI:
        vs.stream.camera.exposure_mode = 'auto'
        vs.stream.camera.awb_mode = "auto"  # PiCamera.AWB_MODES, aslo awb_gain


def end_stabilize(vs):
    global IS_RASPBERRY_PI
    if IS_RASPBERRY_PI:
        gains = vs.stream.camera.awb_gains
        vs.stream.camera.awb_mode = "off"
        vs.stream.camera.awb_gains = gains
        vs.stream.camera.exposure_mode = 'off'







def do(colours):
    global stabilizing_counter
    global state
    global server
    global IS_RASPBERRY_PI

    props = Properties()
    ui = props.group("ui")
    ui.add("blur", PropType.unsigned_int, maximum=250)
    ui.add("min_circle", PropType.unsigned_int, maximum=250)
    ui.add("max_circle", PropType.unsigned_int, maximum=250)
    ui.add("show_masks", PropType.bool)
    ui.add("min_area", PropType.unsigned_int)
    colours2 = props.group("colours")
    col = ["blue", "green", "yellow", "orange", "pink"]
    for name in col:
        colour = colours2.group(name)
        colour.add('min_hsv', PropType.hsv)
        colour.add('max_hsv', PropType.hsv)

    if IS_RASPBERRY_PI:
        filename = "pi.json"
    else:
        filename = "onno.json"

    props.load(filename)

    prop_ui = PropertiesOpenCVUI(props)
    prop_ui.show('colours/blue')


    try:
        # //full
        # //2592 x 1944
        # //1296 x 972
        # //1296 x 730
        # //
        if IS_RASPBERRY_PI:
            mult = 100  # 120 is fine for 30fps, 2 colours
            resolution = (4 * mult, 3 * mult + 4)
            framerate = 30
        else:
            resolution = (int(1280 / 2), int(720 / 2))
            framerate = 60

        vs = VideoStream(use_pi_camera=IS_RASPBERRY_PI, resolution=resolution, frame_rate=framerate)

        if IS_RASPBERRY_PI:
            vs.stream.camera.hflip = True

        vs.start()

        time.sleep(2.0)
        if IS_RASPBERRY_PI:
            # rpi tends to change the res...
            res_x, res_y = vs.stream.camera.resolution
        else:
            res_x, res_y = resolution

        grid = OctaveGrid(res_x, res_y, padding=10, divisions_x=10, divisions_y=2)


        main_window_name = 'frame'

        # pprint(vs)
        cv2.namedWindow(main_window_name)  # for mouse events

        mouse.connect(main_window_name)

        prep_ui()

        fps = FramesPerSecond()
        ips = FramesPerSecond()
        # original = None

        ball_tracker = BallTracker(res_x)

        show_video = True
        last_frame_count = -1

        web_server = startWebServerInSeperateProcess(8000)
        server = SoundSocketServer('', 8001)

        # if IS_RASPBERRY_PI:
        startBrowserInSeperateProcess("http://localhost:8000/socket.html")

        start_stabilize(vs)

        running = True
        frame = None

        while running:

            frame_count, new_frame = vs.read_with_count()

            if frame_count != last_frame_count and new_frame is not None:

                pixel_count = (new_frame.shape[0] * new_frame.shape[1])

                frame = new_frame
                ips.add()
                last_frame_count = frame_count
                original = cvh.clone_image(frame)

                if state == 'stabilize':
                    stabilizing_counter = stabilizing_counter + 1
                    cvh.draw_text(frame, str(stabilizing_counter) +
                                  ' stabilising', (5, 40), (255, 255, 255))
                    if stabilizing_counter > 50:
                        end_stabilize(vs)
                        start_state('normal')

                if state == 'normal':

                    frame, grid_messages = process_frame(colours, frame, ball_tracker, original, grid)

                    m = mouse.mouse()
                    # mouse overlay
                    if m.mode == mouse.MouseInteraction.DRAWING:
                        cv2.circle(frame, m.draw_pos, m.draw_size, (255, 0, 0), 1)
                        cvh.draw_shadow_arrow(frame, m.draw_pos, m.draw_last_pos)
                        (mean, stddev) = cvh.mean_and_stddev_of_circle(original, m.draw_pos, m.draw_size)
                        hsv = cvh.bgr_to_hsv(mean[0], mean[1], mean[2])
                        cvh.draw_text(frame, str(hsv) + ' ' + str(stddev), m.draw_last_pos)

                    if len(grid_messages) > 0:
                        sound_messages = []
                        for message in grid_messages:
                            colour, ball_size, dx, dy = message
                            note = 0 + (dx * 1) + (dy * 12)
                            percent_of_screen = ((ball_size / pixel_count) * 100.0)
                            sound_messages.append(colour + ',' + str(note) + ',' + str(percent_of_screen))
                        sound_message = ";".join(sound_messages)

                        if IS_RASPBERRY_PI:
                            server.send_to_all(sound_message)
                            # for client in server.clients:
                            #    client.sendMessage(sound_message)
            else:
                # print("Same Frame: " + str(frame_count) + ' = ' + str(last_frame_count))
                pass

            fps.add()  # show fps
            if frame is not None:
                cvh.draw_text(frame,
                              str(fps.fps) + 'fps ' +
                              str(ips.fps) + 'pips' +
                              str(vs.fps()) + 'cips', (5, 20), (255, 255, 255))

                if show_video:
                    cv2.imshow(main_window_name, frame)

            server.serveonce()  # this is slow....

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            if key == ord('t'):
                show_video = not show_video

            if key == ord('s'):
                start_stabilize(vs)

            if key == ord("f"):
                if IS_RASPBERRY_PI:
                    vs.stream.camera.hflip = not vs.stream.camera.hflip

    except KeyboardInterrupt:
        print("CRTL+C")


    except:
        print("Unexpected error:", sys.exc_info()[0])
        raise

    # When everything done, release the capture
    vs.stop()

    stopWebServerInSeperateProcess(web_server)
    # pygame.mixer.quit()
    # if IS_RASPBERRY_PI:


# https://stackoverflow.com/questions/18204782/runtimeerror-on-windows-trying-python-multiprocessing
if __name__ == '__main__':
    colours = [
        Colour(name="blue", low=[54, 171, 154], high=[130, 255, 255], rgb=[255, 0, 0]),
        Colour(name="green", low=[0, 0, 0], high=[255, 255, 255], rgb=[0, 255, 0]),
        Colour(name="yellow", low=[0, 0, 0], high=[255, 255, 255], rgb=[0, 255, 255]),
        Colour(name="pink", low=[0, 0, 0], high=[255, 255, 255], rgb=[255, 0, 255]),
        #   Colour(name="ornage", low=[0, 0, 0], high=[255, 255, 255], rgb=[0, 165, 255])
    ]

    load_colours(colours=colours)

    do(colours=colours)

    cv2.destroyAllWindows()
# https://www.pyimagesearch.com/2017/02/06/faster-video-file-fps-with-cv2-videocapture-and-opencv/
#  - optimize and rpi compatible...
