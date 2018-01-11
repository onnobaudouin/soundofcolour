import cv2
import numpy as np
import base64
from typing import Optional, Union, Any, List, Dict


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


def image_as_base64_encoded_image(image, quality=20, image_format="jpg", ratio=1.0):
    """
    Returns a string with base64 encoded (and/or resized) image or None
    :param image:
    :param quality:
    :param image_format:
    :param ratio:
    :return:
    """
    if image is None:
        return None
    encode_as = ".jpg"
    if image_format == "png":
        encode_as = ".png"
    if ratio != 1.0:
        if ratio <= 0.01 or ratio > 1:
            return None
        new_size = (int(image.shape[1] * ratio), int(image.shape[0] * ratio))
        image = cv2.resize(image, new_size,
                           interpolation=cv2.INTER_LINEAR)  # INTER_CUBIC | INTER_LINEAR | INTER_AREA

    if encode_as == ".jpg":
        ret, buf = cv2.imencode(encode_as, image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    else:
        ret, buf = cv2.imencode(encode_as, image)

    if ret is True:
        return str(base64.b64encode(buf).decode())
    else:
        return None


def resolution_of(frame=None):
    if frame is not None:
        return frame.shape[1], frame.shape[0]  # height / width?
    else:
        return None


def mean_and_stddev_of_circle(source_image, center=(0, 0), radius=1):
    # todo: use ROI

    width_index = 0
    height_index = 1
    circle_mask = np.zeros((source_image.shape[width_index], source_image.shape[height_index]), dtype=np.uint8)
    cv2.circle(circle_mask, center, int(radius), (255, 255, 255), cv2.FILLED)
    # cv2.imshow('samplemask', image_from_mask(source_image, circle_mask))

    mean_colour, stds = cv2.meanStdDev(source_image, mask=circle_mask)

    return np.concatenate(mean_colour).flatten(), np.concatenate(stds).flatten()


def histogram_of_disc(bgr_image, center=(0, 0), radius=1):
    """

    :param source_image:
    :param channel: 0=b, 1=g 2=r
    :param center:
    :param radius:
    :return:
    """
    width_index = 0
    height_index = 1
    circle_mask = np.zeros((bgr_image.shape[width_index], bgr_image.shape[height_index]), dtype=np.uint8)
    cv2.circle(circle_mask, center, int(radius), (255, 255, 255), cv2.FILLED)
    histogram = []
    for channel in range(0, 3):
        channel = cv2.calcHist([bgr_image], [channel], circle_mask, [256], [0, 256])
        channel_in = [int(x) for x in channel]
        histogram.append(channel_in)

    return histogram

def histogram_hsv_of_disc(hsv_image, center=(0, 0), radius=1):
    """

    :param source_image:
    :param channel: 0=b, 1=g 2=r
    :param center:
    :param radius:
    :return:
    """
    width_index = 0
    height_index = 1
    circle_mask = np.zeros((hsv_image.shape[width_index], hsv_image.shape[height_index]), dtype=np.uint8)
    cv2.circle(circle_mask, center, int(radius), (255, 255, 255), cv2.FILLED)
    histogram = []
    channel = cv2.calcHist([hsv_image], [0], circle_mask, [180], [0, 180])
    channel_in = [int(x) for x in channel]
    histogram.append(channel_in)
    for channel_index in range(1, 3):
        channel = cv2.calcHist([hsv_image], [channel_index], circle_mask, [256], [0, 256])
        channel_in = [int(x) for x in channel]
        histogram.append(channel_in)


    return histogram



def get_mean_hsv_from_circle(rgb_frame, center, radius):
    (mean, stddev) = mean_and_stddev_of_circle(rgb_frame, center, radius)
    hsv = bgr_to_hsv(mean[0], mean[1], mean[2])
    return hsv


def bgr_to_hsv(b, g, r) :
    """
    Takes an RGB in and sends out an HSV in 0..360, 0..255, 0..255 range
    :param b:
    :param g:
    :param r:
    :return:
    """
    image = np.uint8([[[b, g, r]]])
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv = hsv_image[0, 0]
    return [int(hsv[0] * 2.0),int(hsv[1]), int(hsv[2])]


def get_mean_hsv_from_circle_and_draw_debug(rgb_frame, center, radius, output_frame) -> List:
    (mean, stddev) = mean_and_stddev_of_circle(rgb_frame, center, radius)
    hsv = bgr_to_hsv(mean[0], mean[1], mean[2])

    cv2.circle(output_frame, center, radius, (255, 0, 0), 1)

    draw_disc(output_frame, center, radius=5, colour=mean)
    p = [int(x) for x in stddev]
    draw_text(output_frame, str(hsv) + ' ' + str(p), center)

    return hsv


def draw_text(image, text, pos=(0, 50), color=(255, 255, 255), size=0.5, align=None):
    cv2.putText(image, text=text, org=pos, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=size, color=color)


def image_from_mask(image, mask):
    return cv2.bitwise_and(image, image, mask=mask)


# https://stackoverflow.com/questions/16533078/clone-an-image-in-cv2-python
def clone_image(image):
    return cv2.copyMakeBorder(image, 0, 0, 0, 0, cv2.BORDER_REPLICATE)


def draw_shadow_arrow(frame, from_point, to_point, colour=(255, 255, 255), thickness=1):
    if from_point is None:
        print("Warning: from point is None in draw_shadow_arrow")
        return
    if to_point is None:
        print("Warning: from point is None in draw_shadow_arrow")
        return

    cv2.arrowedLine(img=frame, pt1=(from_point[0] + 1, from_point[1] + 1), pt2=(to_point[0] + 1, to_point[1] + 1),
                    color=(0, 0, 0), thickness=thickness)
    cv2.arrowedLine(img=frame, pt1=from_point, pt2=to_point, color=colour, thickness=thickness)


def draw_line(frame, from_point, to_point, colour=(255, 255, 255), thickness=1):
    cv2.line(img=frame, pt1=from_point, pt2=to_point, color=colour, thickness=thickness)


def draw_rect(frame, from_point, to_point, colour=(255, 255, 255), thickness=1):
    cv2.rectangle(img=frame, pt1=from_point, pt2=to_point, color=colour, thickness=thickness)


def draw_disc(frame, center, radius, colour):
    cv2.circle(img=frame, center=center, radius=radius, color=colour, thickness=cv2.FILLED)
