import cv2
import numpy as np


# TODO: this is close to opencvhelpers.py
def blur(frame, size):
    # todo: change dependant on platform?
    # frame = cv2.bilateralFilter(frame, 9, 75, 75)  # might be better
    # frame = cv2.medianBlur(frame, 15)
    if size % 2 == 0:
        size = size + 1
    return cv2.GaussianBlur(frame, (size, size), 0)


def show_difference(original_frame, new_frame):
    if original_frame is not None:
        diff = cv2.absdiff(original_frame, new_frame)
        cv2.imshow('diff', diff)


def mask_of_colour(input_frame_hsv, lower_range, higher_range):
    return cv2.inRange(input_frame_hsv, lower_range, higher_range)


def contours_of_colour_range_in(mask_frame):
    # http://docs.opencv.org/trunk/d9/d8b/tutorial_py_contours_hierarchy.html
    # we use external so any small 'gaps' are ignored, e.g. a highlight for example within a sphere..
    image, contours, hierarchy = cv2.findContours(mask_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


def hue_saturation_value_frame_of(bgr_frame):
    return cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)


def hsv_to_np_array(hsv):
    """
    Convert a normal Properties HSV (360.0, 0.0->1.0, 0.0->1.0) to a openCV one (0-180,0->255,0->255)
    :param hsv:
    :return:
    """
    hsv_tuple = (int(hsv[0] / 2.0), int(hsv[1] * 255.0), int(hsv[1] * 255.0))
    return np.array(hsv_tuple)


def bgr_of(rgb):
    """
    Return a Blue,Green,Red from a Red Green Blue
    :param rgb:
    :return:
    """
    (r, g, b) = rgb
    return b, g, r
