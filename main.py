import cv2
from math import *
import numpy as np

# Sort each checker by its X position.
def compare(item):
    return item[0]

# Filter each square in column by its Y position.
def compare_col(item):
    return item[1]

# Use to divide each column of checker squares.
def split(list):
    for i in range(0, len(list), 8):
        yield list[i:i + 8]

images = [cv2.imread('im1.jpg'), cv2.imread('im2.jpg'), cv2.imread('im3.jpg')]

for img in images:

    # Read image and convert to gray scale.
    imgc = cv2.imread('im1.jpg')
    img = cv2.cvtColor(imgc, cv2.COLOR_BGR2GRAY)

    # Resize color image.
    dim = (int(imgc.shape[0] * 0.25), int(imgc.shape[1] * 0.25))
    imgc = cv2.resize(imgc, dim, interpolation = cv2.INTER_AREA)

    # Resize gray image.
    dim = (int(img.shape[0] * 0.25), int(img.shape[1] * 0.25))
    img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

    # Blur the himage for easier detection circle / rectangle detection
    img = cv2.blur(img, (3, 3))

    # Detect Circles.
    circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, 90, param1=30, param2=30, minRadius=12, maxRadius=35)
    circles = np.uint16(np.around(circles))

    # Detect edges using Canny
    threshold = 80
    canny_output = cv2.Canny(img, threshold, threshold * 2)
    contours, _ = cv2.findContours(canny_output, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Get bounding rects
    contours_poly = [None]*len(contours)
    boundRect = [None]*len(contours)
    checker_spaces = []

    for i, c in enumerate(contours):
        contours_poly[i] = cv2.approxPolyDP(c, 3, True)
        boundRect[i] = cv2.boundingRect(contours_poly[i])

    # Canvas to display only checker rectangles.
    drawing = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)

    # Capture rectangles
    for i in range(len(contours)):
        p1 = (int(boundRect[i][0]), int(boundRect[i][1]))
        p2 = (int(boundRect[i][0]+boundRect[i][2]), int(boundRect[i][1]+boundRect[i][3]))

        # Filter out any rectangles not part of the board.
        if(p2[0] - p1[0] > 100 and p2[0] - p1[0] < 130 and p2[1] - p1[1] > 50 and p2[1] - p1[1] < 110):
            checker_spaces.append(boundRect[i])

    # Filter rectangles by their x position
    checker_spaces.sort(key=compare)
    filtered_spaces = []

    # Filter out overlapping rectangles
    for rect1 in checker_spaces:
        add = True
        for rect2 in filtered_spaces:
            if (abs(rect1[0] - rect2[0]) < 10 and abs(rect1[1] - rect2[1]) < 10):
                add = False
                break

        if add:
            filtered_spaces.append(rect1)
    
    # Split the array of checkers into 8 columns
    sectioned_checker_spaces = list(split(filtered_spaces))
    for col in sectioned_checker_spaces:
        col.sort(key=compare_col)

    final_checker_spaces = []

    # Remove useless squares (Black Squares)
    i = 1
    for rect_col in sectioned_checker_spaces:
        filt_col = []
        j = i
        for rect in rect_col:
            if j % 2 == 0:
                filt_col.append(rect)

            j = j + 1

        final_checker_spaces.append(filt_col)

        if i == 0:
            i = 1
        else:
            i = 0

    # Finally draw rectangles.
    for rect_col in final_checker_spaces:
        for rect in rect_col:
            color = (0, 255, 0)

            p1 = (int(rect[0]), int(rect[1]))
            p2 = (int(rect[0]+rect[2]), int(rect[1]+rect[3]))

            cv2.rectangle(drawing, p1, p2, color, 2)
            cv2.rectangle(imgc, p1, p2, color, 2)

    # Draw circle outline + center dot.
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            center = (i[0], i[1])

            # Dot
            cv2.circle(imgc, center, 1, (0, 255, 100), 3)

            # Outline
            radius = i[2]
            cv2.circle(imgc, center, radius, (0, 255, 255), 3)

    # Show image.
    cv2.imshow('Final Image', imgc)

    # Show just bounding rectangles
    cv2.imshow('Bounding Rectangles', drawing)

    # Wait for keypress to close.
    cv2.waitKey(0)
    cv2.destroyAllWindows()