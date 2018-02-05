import cv2
import numpy as np
import base64
from typing import List
import math


def blank_image(width, height, channels=3, dtype=np.uint8):
    return np.zeros((height, width, channels), dtype)


def blur(frame, size):
    # todo: change dependant on platform?
    # frame = cv2.bilateralFilter(frame, 9, 75, 75)  # might be better
    # frame = cv2.medianBlur(frame, 15)
    if size % 2 == 0:
        size = size + 1
    return cv2.GaussianBlur(frame, (size, size), 0)


def blur_median(frame, size=15):
    if size % 2 == 0:
        size = size + 1
    return cv2.medianBlur(frame, size)


def add(dst, add):
    # print(str(dst.shape)+' '+str(dst.dtype))
    # print(str(add.shape)+' '+str(add.dtype))
    # cv2.add(dst, add, dst, None, -1)
    return dst + add
    #


def show(image, name):
    if image is not None:
        cv2.imshow(name, image)


def multiply(src, scalar):
    return src * scalar
    # cv2.convertScaleAbs(src, dst, scalar)


def absolute_difference(original_frame, new_frame):
    if original_frame is not None and new_frame is not None:
        return cv2.absdiff(original_frame, new_frame)
    return None


def show_difference(original_frame, new_frame):
    diff = absolute_difference(original_frame, new_frame)
    if diff is not None:
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
    hsv_tuple = (int(hsv[0] / 2.0), int(hsv[1] * 255.0), int(hsv[2] * 255.0))
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
    """
    Returns width / height
    :param frame:
    :return:
    """
    if frame is not None:
        return frame.shape[1], frame.shape[0]  # height / width?
    else:
        return None


def mean_and_stddev_of_disc(source_image, center=(0, 0), radius=1):
    # todo: use ROI
    circle_mask = disc_mask(source_image, center, radius)
    mean_colour, stds = cv2.meanStdDev(source_image, mask=circle_mask)
    return np.concatenate(mean_colour).flatten(), np.concatenate(stds).flatten()


def mean_and_stddev_of_torus(source_image, center=(0, 0), inner_radius=1, outer_radius=2):
    # todo: use ROI
    circle_mask = torus_mask(source_image, center, inner_radius, outer_radius)
    mean_colour, stds = cv2.meanStdDev(source_image, mask=circle_mask)
    return np.concatenate(mean_colour).flatten(), np.concatenate(stds).flatten()


def local_maxima_indices_in_histogram_1d(hist, window_size=9, circular=False):
    if (window_size % 2) == 0:
        print("window_size must be uneven. local_maxima_in_histogram")
        return None
    length = len(hist)
    output = []
    index = 0
    either_side = math.floor(window_size / 2.0)
    while index < length:
        current_value = hist[index]
        is_highest = True
        for window_index in range(index - either_side, index + either_side + 1, 1):
            if window_index != index:

                if circular is False:
                    if (window_index >= 0) and (window_index < length):
                        if hist[window_index] > current_value:
                            is_highest = False
                            break
                else:
                    t_index = window_index
                    if window_index < 0:
                        t_index = length + window_index
                    elif window_index >= length:
                        t_index = window_index - length + 1
                    if hist[t_index] > current_value:
                        is_highest = False
                        break

        if is_highest:
            if current_value != 0:
                output.append(index)
        index = index + 1
    return output


def histogram_of_disc(bgr_image, center=(0, 0), radius=1):
    circle_mask = disc_mask(bgr_image, center, radius)
    histogram = []
    for channel in range(0, 3):
        channel = cv2.calcHist([bgr_image], [channel], circle_mask, [256], [0, 256])
        channel_in = [int(x) for x in channel]
        histogram.append(channel_in)
    return histogram


def histogram_hsv_of_disc(hsv_image, center=(0, 0), radius=1):
    circle_mask = disc_mask(hsv_image, center, radius)
    return histogram_hsv_of_mask(hsv_image, circle_mask)


def histogram_hsv_of_mask(hsv_image, mask):
    histogram = []
    channel = cv2.calcHist([hsv_image], [0], mask, [180], [0, 180])
    channel_in = [int(x) for x in channel]
    histogram.append(channel_in)
    for channel_index in range(1, 3):
        channel = cv2.calcHist([hsv_image], [channel_index], mask, [256], [0, 256])
        channel_in = [int(x) for x in channel]
        histogram.append(channel_in)

    return histogram


def disc_mask(frame, center=(0, 0), radius=1):
    width_index = 1
    height_index = 0
    mask = blank_image(frame.shape[width_index], frame.shape[height_index], 1)
    draw_disc(mask, center, int(radius), (255, 255, 255))
    return mask


def torus_mask(frame, center=(0, 0), inner_radius=1, outer_radius=2):
    mask = disc_mask(frame, center, outer_radius)  # draw big white disc
    draw_disc(mask, center, int(inner_radius), (0, 0, 0))  # fill inside with black - torus!
    return mask


def histogram_hsv_of_torus(hsv_image, center=(0, 0), inner_radius=1, outer_radius=2):
    mask = torus_mask(hsv_image, center, outer_radius)  # draw big white dis
    return histogram_hsv_of_mask(hsv_image, mask)


def get_mean_hsv_from_circle(rgb_frame, center, radius):
    (mean, stddev) = mean_and_stddev_of_disc(rgb_frame, center, radius)
    hsv = bgr_to_hsv(mean[0], mean[1], mean[2])
    return hsv


def bgr_to_hsv(b, g, r):
    image = np.uint8([[[b, g, r]]])
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    hsv = hsv_image[0, 0]
    return [int(hsv[0] * 2.0), int(hsv[1]), int(hsv[2])]


def hsv_to_bgr(h, s, v):
    hue = math.floor(h / 2.0)
    image = np.uint8([[[hue, s, v]]])
    rgb_image = cv2.cvtColor(image, cv2.COLOR_HSV2BGR)
    rgb = rgb_image[0, 0]
    return [int(rgb[0]), int(rgb[1]), int(rgb[2])]


def get_mean_hsv_from_circle_and_draw_debug(rgb_frame, center, radius, output_frame) -> List:
    (mean, stddev) = mean_and_stddev_of_disc(rgb_frame, center, radius)
    hsv = bgr_to_hsv(mean[0], mean[1], mean[2])

    cv2.circle(output_frame, center, radius, (255, 0, 0), 1)

    draw_disc(output_frame, center, radius=5, colour=mean)
    p = [int(x) for x in stddev]
    draw_text(output_frame, str(hsv) + ' ' + str(p), center)

    return hsv


def auto_canny(image, sigma=0.33):
    # compute the median of the single channel pixel intensities
    v = np.median(image)

    # apply automatic Canny edge detection using the computed median
    lower = int(max(0, (1.0 - sigma) * v))
    upper = int(min(255, (1.0 + sigma) * v))
    edged = cv2.Canny(image, lower, upper)

    # return the edged image
    return edged


def bgr_from_hue_image(hue_image):
    lst = np.zeros((256, 1, 3), dtype=np.uint8)
    for i in range(256):
        bgr = hsv_to_bgr(i * 2, 255, 250)
        for j in range(3):
            lst[i, 0, j] = bgr[j]

    cv2_image = cv2.cvtColor(hue_image, cv2.COLOR_GRAY2BGR)
    # lut = []
    # for hue in range(0, 256):
    #    lut.append(hsv_to_bgr(hue * 2, 255, 128))
    # nplut = np.array(lut).astype(np.uint8)
    # return cv2.LUT(hue_image, lst)
    # hue_image *= 180.0/256.0

    return cv2.applyColorMap(cv2_image, userColor=lst)


def draw_text(image, text, pos=(0, 50), color=(255, 255, 255), size=0.5):
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


def draw_circle(frame, center, radius, colour, thickness=1):
    cv2.circle(img=frame, center=center, radius=radius, color=colour, thickness=thickness)


def draw_histogram(frame, point, hist, scale, colour=(255, 255, 255), normalize=False):
    x, y = point
    if normalize:
        max = np.amax(hist)
    else:
        max = 1
    h2 = [int((a * scale) / max) for a in hist]
    for p in range(0, len(h2) - 1):
        draw_line(frame, (x + p, y - h2[p]), (x + p + 1, y - h2[p + 1]), colour=colour)


def draw_histograms(x, y, hists, draw_frame, size=30, normalize=True, color=(0, 255, 126)):
    for index, histogram in enumerate(hists):
        offset = (x, y + (index * size))
        draw_histogram(draw_frame, offset, histogram, scale=size, normalize=normalize,
                                       colour=color)

def colour_distance_between_inner_disc_and_outer_torus(rgb_frame, inner_circle, torus_r1, torus_r2):
    x, y, r = inner_circle
    (inner_mean, none) = mean_and_stddev_of_disc(rgb_frame, (x, y), r)
    (outer_mean, none) = mean_and_stddev_of_torus(rgb_frame, (x, y), torus_r1, torus_r2)
    return distance_between_rgb_colours(inner_mean, outer_mean)


def colour_distance_signal(rgb_frame, circle, sample_radius_size=2, extra_range=6):
    """calculate the series of difference in rgb colour between an inner disc, and outer radius"""
    x, y, r = circle
    offset = 2
    signal = []
    for radius in range(1, r + extra_range):
        torus_r1 = radius + offset
        distance = colour_distance_between_inner_disc_and_outer_torus(rgb_frame,
                                                                      (x, y, radius),
                                                                       torus_r1,
                                                                       torus_r1 + sample_radius_size)
        signal.append(distance)
    return signal


def low_filter_histogram(histogram, low_threshold):
    ret = []
    for x in histogram:
        if x < low_threshold:
            ret.append(0)
        else:
            ret.append(x)
    return ret


#  http://dev.theomader.com/gaussian-kernel-calculator/
def normalize_histogram(histogram):
    max = np.amax(histogram)
    if max == 0:
        print("histogram has no data???")
        return None
    return [x / max for x in histogram]


def minimum_angle_between_2_angles(x, y, radians=True):
    if radians is False:
        x = x * math.pi / 180.0
        y = y * math.pi / 180.0
    value = min(y - x, y - x + 2 * math.pi, y - x - 2 * math.pi, key=abs)
    if radians is False:
        return value * 180 / math.pi
    return value


def distance_between_rgb_colours(mean, mean2):
    delta_b = (mean2[0] / 255.0) - (mean[0] / 255.0)
    delta_r = (mean2[1] / 255.0) - (mean[1] / 255.0)
    delta_g = (mean2[2] / 255.0) - (mean[2] / 255.0)
    return math.sqrt(delta_b ** 2 + delta_g ** 2 + delta_r ** 2)


def distance_between_hsv_colours(hsv1, hsv2):
    hue_difference = abs(minimum_angle_between_2_angles(hsv1[0], hsv2[0], radians=False)) / 360.0
    sat_difference = (hsv1[1] / 255.0) - (hsv2[1] / 255.0)
    lum_difference = (hsv1[2] / 255.0) - (hsv2[2] / 255.0)
    return math.sqrt(hue_difference ** 2 + sat_difference ** 2 + lum_difference ** 2)


def min_max_indices_if_over_strength(histogram, threshold, normalize=False, percentage=False):
    if normalize is True:
        histogram = normalize_histogram(histogram)

    size = len(histogram)
    if size <= 0:
        return None
    min_index = None
    for index, value in enumerate(histogram):
        if value > threshold:
            min_index = index
            break
    max_index = None
    for index in range(size - 1, -1, -1):
        if histogram[index] > threshold:
            max_index = index
            break
    if min_index is not None and max_index is not None:
        if min_index < max_index:
            if percentage:
                return min_index / size, max_index / size
            else:
                return min_index, max_index
    return None


def spread_min_max(histogram, threshold, normalize=False, percentage=False):
    min_max = min_max_indices_if_over_strength(histogram, threshold=threshold, normalize=normalize,
                                               percentage=percentage)
    if min_max is not None:
        min_index, max_index = min_max
        return max_index - min_index
    return None


def gaussian_normalised_kernel_1d(size):
    kernels = [
        [1],
        None,
        [0.27901, 0.44198, 0.27901],
        None,
        [0.06136, 0.24477, 0.38774, 0.24477, 0.06136],
        None,
        [0.00598, 0.060626, 0.241843, 0.383103, 0.241843, 0.060626, 0.00598]
    ]
    if 1 <= size < 8:
        return kernels[size - 1]
    return None


def gaussian_blur_1d(hist, size=5, circular=True):
    kernel = gaussian_normalised_kernel_1d(size)
    if kernel is None:
        print('Not A Valid Gaussian Kernel 1D Size ' + str(size))
        return hist

    length = len(hist)
    output = np.zeros(length)
    neg = math.floor(size / 2.0)
    for index in range(0, length):
        value = 0
        for kern_index in range(0, size):
            offset = index + kern_index - neg
            if offset < 0:
                if circular:
                    offset = length + offset
                else:
                    offset = 0
            elif offset >= length:
                if circular:
                    offset = offset % length
                else:
                    offset = length - 1
            value += (kernel[kern_index] * hist[offset])
        output[index] = value
    return output


def convert_to_32bit_per_color_depth(frame):
    return np.uint32(frame)


def blur_histogram(hist, size=5, circular=True, times=1):
    output = hist
    for i in range(0, times):
        output = gaussian_blur_1d(output, size, circular)
    return output

# def start_find_blobs(self):
#  https://github.com/opencv/opencv/blob/master/samples/python/mser.py
#  https://stackoverflow.com/questions/9860667/writing-robust-color-and-size-invariant-circle-detection-with-opencv-based-on/10128487
#  http://answers.opencv.org/question/19015/how-to-use-mser-in-python/
#   if self.average_background_frame is not None:
#      mser = cv2.MSER_create()
#      regions = mser.detectRegions(self.average_background_frame)
#     hulls = [cv2.convexHull(p.reshape(-1, 1, 2)) for p in regions[1]]
#    cv2.polylines(self.median_blur_frame, hulls, 1, (0, 255, 0))

#  self.state.start("normal")


def draw_circles(draw_frame, circles, sample_image, colour=(0, 128, 255), draw_hist=False):
    if circles is None:
        return

    # convert the (x, y) coordinates and radius of the circles to integers

    for (x, y, r) in circles:
        # draw the circle in the output image, then draw a rectangle
        # corresponding to the center of the circle
        draw_circle(draw_frame, (x, y), r, colour)
        # cv2.rectangle(draw_frame, (x - 5, y - 5), (x + 5, y + 5), colour, -1)

        if draw_hist:
            hist = histogram_hsv_of_disc(sample_image, (x, y), r)
            for index, histogram in enumerate(hist):
                size = 30
                offset = (x, y + (index * size))

                # draw_histogram(draw_frame, offset, histogram, scale=size, normalize=True)
                circular = False
                if index == 0:
                    circular = True
                blurred = blur_histogram(histogram, 7, circular=circular, times=9)

                # local_maxima = local_maxima_indices_in_histogram_1d(blurred, circular=circular)

                # normalized_histogram = normalize_histogram(blurred)

                draw_histogram(draw_frame, offset, blurred, scale=size, normalize=True,
                                           colour=(0, 255, 126))