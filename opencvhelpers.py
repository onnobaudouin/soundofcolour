import numpy as np
import cv2


def mean_and_stddev_of_circle(source_image, center=(0, 0), radius=1):
    # todo: use ROI

    width_index = 0
    height_index = 1
    circle_mask = np.zeros((source_image.shape[width_index], source_image.shape[height_index]), dtype=np.uint8)
    cv2.circle(circle_mask, center, int(radius), (255, 255, 255), cv2.FILLED)
    # cv2.imshow('samplemask', image_from_mask(source_image, circle_mask))

    mean_colour, stds = cv2.meanStdDev(source_image, mask=circle_mask)

    return np.concatenate(mean_colour).flatten(), np.concatenate(stds).flatten()


def draw_text(image, text, pos=(0, 50), color=(255, 255, 255), size=0.5, align=None):
    cv2.putText(image, text=text, org=pos, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=size, color=color)


def image_from_mask(image, mask):
    return cv2.bitwise_and(image, image, mask=mask)


# https://stackoverflow.com/questions/16533078/clone-an-image-in-cv2-python
def clone_image(image):
    return cv2.copyMakeBorder(image, 0, 0, 0, 0, cv2.BORDER_REPLICATE)


def bgr_to_hsv(b, g, r):
    image = np.uint8([[[b, g, r]]])
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    return hsv_image[0, 0]


def draw_shadow_arrow(frame, from_point, to_point, colour=(255, 255, 255), thickness=1):
    cv2.arrowedLine(img=frame, pt1=(from_point[0] + 1, from_point[1] + 1), pt2=(to_point[0] + 1, to_point[1] + 1),
                    color=(0, 0, 0), thickness=thickness)
    cv2.arrowedLine(img=frame, pt1=from_point, pt2=to_point, color=colour, thickness=thickness)


def draw_line(frame, from_point, to_point, colour=(255, 255, 255), thickness=1):
    cv2.line(img=frame, pt1=from_point, pt2=to_point, color=colour, thickness=thickness)


def draw_rect(frame, from_point, to_point, colour=(255, 255, 255), thickness=1):
    cv2.rectangle(img=frame, pt1=from_point, pt2=to_point, color=colour, thickness=thickness)


def draw_disc(frame, center, radius, colour):
    cv2.circle(img=frame, center=center, radius=radius, color=colour, thickness=cv2.FILLED)
