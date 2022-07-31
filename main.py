import cv2
import numpy as np
from checkers import Board

# Sort each checker by its X position.
def compare(item):
    return item[0]

# Filter each checker in each column by its Y position.
def compare_col(item):
    return item[1]

# Use to divide the array of checker squares into 8 columns.
def split(list):
    for i in range(0, len(list), 8):
        yield list[i:i + 8]

class CheckerSpace:
    def __init__(self, checker_type, position):
        self.checker_type = checker_type
        self.position = position

board = [
    CheckerSpace("red", 0),
    CheckerSpace("red", 1),
    CheckerSpace("red", 2),
    CheckerSpace("red", 3),
    CheckerSpace("red", 4),
    CheckerSpace("red", 5),
    CheckerSpace("red", 6),
    CheckerSpace("red", 7),
    CheckerSpace("red", 8),
    CheckerSpace("red", 9),
    CheckerSpace("red", 10),
    CheckerSpace("red", 11),
    CheckerSpace("empty", 12),
    CheckerSpace("empty", 13),
    CheckerSpace("empty", 14),
    CheckerSpace("empty", 15),
    CheckerSpace("empty", 16),
    CheckerSpace("empty", 17),
    CheckerSpace("empty", 18),
    CheckerSpace("empty", 19),
    CheckerSpace("black", 20),
    CheckerSpace("black", 21),
    CheckerSpace("black", 22),
    CheckerSpace("black", 23),
    CheckerSpace("black", 24),
    CheckerSpace("black", 25),
    CheckerSpace("black", 25),
    CheckerSpace("black", 27),
    CheckerSpace("black", 28),
    CheckerSpace("black", 29),
    CheckerSpace("black", 30),
    CheckerSpace("black", 31)
]

imgc = cv2.imread("im4.jpg")

# Read image and convert to gray scale.
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
threshold = 20
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
empty_canvas = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)

# Capture rectangles
for i in range(len(contours)):
    p1 = (int(boundRect[i][0]), int(boundRect[i][1]))
    p2 = (int(boundRect[i][0]+boundRect[i][2]), int(boundRect[i][1]+boundRect[i][3]))

    # Filter out any rectangles not part of the board.
    if(p2[0] - p1[0] > 90 and p2[0] - p1[0] < 140 and p2[1] - p1[1] > 40 and p2[1] - p1[1] < 120):
        checker_spaces.append(boundRect[i])

# Filter rectangles by their X axis
checker_spaces.sort(key=compare)
filtered_spaces = []

# Filter out overlapping rectangles. The Contour function will detect multiple rectangles in the same spot.
# This just gets rid of those extra rectangles.
for rect1 in checker_spaces:
    add = True
    for rect2 in filtered_spaces:
        if (abs(rect1[0] - rect2[0]) < 15 and abs(rect1[1] - rect2[1]) < 15):
            add = False
            break

    if add:
        filtered_spaces.append(rect1)

print("Should now have 64 checker squares:")
print(len(filtered_spaces))

# Split the array of checkers into 8 columns, and sort them by their Y axis.
# This will organize the squares from top left to bottom right.
organized_checker_spaces = list(split(filtered_spaces))
for col in organized_checker_spaces:
    col.sort(key=compare_col, reverse=True)

non_useless_checker_spaces = []

# Remove useless squares (Black Squares)
i = 0
for rect_col in organized_checker_spaces:
    filt_col = []
    j = i
    for rect in rect_col:
        if j % 2 == 0:
            filt_col.append(rect)

        j = j + 1

    non_useless_checker_spaces.append(filt_col)

    if i == 0:
        i = 1
    else:
        i = 0

# Combine the 8 columns into a single array
final_checkers = []
for rect_col in non_useless_checker_spaces:
    for rect in rect_col:
        final_checkers.append(rect)

final_img = imgc

# Finally draw rectangles.
for rect in final_checkers:
    color = (0, 255, 0)

    p1 = (int(rect[0]), int(rect[1]))
    p2 = (int(rect[0]+rect[2]), int(rect[1]+rect[3]))

    cv2.rectangle(empty_canvas, p1, p2, color, 2)
    cv2.rectangle(final_img, p1, p2, color, 2)

new_board = []

for index, rect in enumerate(final_checkers):

    # Here we fill the new_board array with the position / type of each rectangle
    # The position will be 0 - 31 and the type can either be red, black or empty
    rect_type = "empty"

    for circle in circles[0, :]:
        x, y, r = circle

        # If their is a piece on the square
        if (x > rect[0] and x < rect[0]+rect[2] and y > rect[1] and y < rect[1]+rect[3]):
            # This next bit of code is how we find what color the piece is

            roi = imgc[y - r: y + r, x - r: x + r]

            # Generate mask
            width, height = roi.shape[:2]
            mask = np.zeros((width, height, 3), roi.dtype)
            cv2.circle(mask, (int(width / 2), int(height / 2)), r, (255, 255, 255), -1)
            dst = cv2.bitwise_and(roi, mask)

            # Find the RGB values within each circles mask
            data = []
            for i in range(3):
                channel = dst[:, :, i]
                indices = np.where(channel != 0)[0]
                color = np.mean(channel[indices])
                data.append(int(color))

            # We only really need the red to determine what type of piece we have
            _, _, red = data

            color_empty_canvas = (0, 0, 0)
            color_final = (0, 0, 0)

            if (red > 150):
                color_empty_canvas = (30, 30, 255)
                color_final = (0, 255, 0)
                rect_type = "red"
            else:
                color_empty_canvas = (255, 0, 0)
                color_final = (255, 50, 50)
                rect_type = "black"

            # Draw circle outline + center dot.
            center = (circle[0], circle[1])
            radius = circle[2]
            cv2.circle(empty_canvas, center, 1, color_empty_canvas, 3)
            cv2.circle(empty_canvas, center, radius, color_empty_canvas, 3)
            cv2.circle(final_img, center, 1, color_final, 3)
            cv2.circle(final_img, center, radius, color_final, 3)

            break

    new_board.append(CheckerSpace(rect_type, index))
    
for piece in new_board:
    print("Square " + str(piece.position) + " : Type " + piece.checker_type)

# Show image.
cv2.imshow("Final Image", imgc)

# Show programs output for spaces + checkers.
cv2.imshow("Empty Canvas", empty_canvas)

# Show img with empty canvas overlayed.
cv2.imshow("Final", final_img)

# Wait for keypress to close.
cv2.waitKey(0)
cv2.destroyAllWindows()
