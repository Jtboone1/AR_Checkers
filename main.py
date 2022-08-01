import cv2
import numpy as np

first_move = True
blacks_move = [0, 0]
imgc = None

# Used to represent a square on the board.
class CheckerSpace:
    def __init__(self, checker_type, position, point = 0):
        self.checker_type = checker_type
        self.position = position
        self.point = point

    def print_check(self):
        print(self.checker_type + " " + str(self.position))

# This is all we need to start our board reading
board = [
    CheckerSpace("red", 16),
    CheckerSpace("red", 18),
    CheckerSpace("red", 20),
    CheckerSpace("red", 22),
    CheckerSpace("empty", 25),
    CheckerSpace("empty", 27),
    CheckerSpace("empty", 29),
    CheckerSpace("empty", 31)
]

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

# When we get the 64 rectangles, organize them first by X axis,
# and then by Y axis.
def organize_rects(rect_arr):

    # Filter rectangles by their X axis
    rect_arr.sort(key=compare)

    # Split the array of checkers into 8 columns, and sort them by their Y axis.
    # This will organize the squares from top left to bottom right.
    organized_checker_spaces = np.array_split(rect_arr, 8)
    arr = []
    for col in organized_checker_spaces:
        checker_list = list(col)
        checker_list.sort(key=compare_col, reverse=True)
        arr.append(checker_list)

    # Combine the 8 columns into a single array
    final_checkers = []
    for rect_col in arr:
        for rect in rect_col:
            final_checkers.append(rect)

    return final_checkers

# Used by AI to move computer piece
def set_move(position, destination):
    blacks_move[0] = position
    blacks_move[1] = destination

# Used by AI piece when it captures a red piece.
def remove_piece(position):
    for piece in board:
        if piece.position == position:
            piece.checker_type = "empty"

# Detects squares on board and returns those squares as OpenCV bounding Rectangles,
# and an empty canvas to display said rectangles.
def detect_rectangles(imgc):

    # convert to hsv
    hsv = cv2.cvtColor(imgc, cv2.COLOR_BGR2HSV)
    cv2.imshow("hsv", hsv)

    # Threshold the HSV, trying to extract the yellow lines from the board.
    hsv_thresh = cv2.inRange(hsv, (10, 100, 100), (30, 255, 255))

    # Dilate the line so that slightly broken lines become connected.
    kernel = np.ones((5,5), np.uint8)  
    hsv_thresh = cv2.dilate(hsv_thresh, kernel, iterations=1)
    cv2.imshow("hsv_thresh", hsv_thresh)

    # Detect edges using Canny
    threshold = 50
    canny_output = cv2.Canny(hsv_thresh, threshold, threshold * 2)
    contours, _ = cv2.findContours(canny_output, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Get bounding rects
    contours_poly = [None]*len(contours)
    boundRect = [None]*len(contours)
    checker_spaces = []

    for i, c in enumerate(contours):
        contours_poly[i] = cv2.approxPolyDP(c, 3, True)
        boundRect[i] = cv2.boundingRect(contours_poly[i])

    cnts = cv2.findContours(hsv_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    for cnt in cnts:
        approx = cv2.contourArea(cnt)

    # Capture rectangles by drawing bounding rectangles around contours.
    for i in range(len(contours)):
        p1 = (int(boundRect[i][0]), int(boundRect[i][1]))
        p2 = (int(boundRect[i][0]+boundRect[i][2]), int(boundRect[i][1]+boundRect[i][3]))

        # Filter out any rectangles not part of the board.
        if(abs(p2[0] - p1[0]) > 90 and abs(p2[0] - p1[0]) < 125 and abs(p2[1] - p1[1]) > 45 and p2[1] - p1[1] < 80):
            checker_spaces.append(boundRect[i])

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

    final_checkers = organize_rects(filtered_spaces)
    empty_canvas = np.zeros((canny_output.shape[0], canny_output.shape[1], 3), dtype=np.uint8)

    return (final_checkers, empty_canvas)

def detect_circles(imgc):

    # Read image and convert to gray scale.
    img = cv2.cvtColor(imgc, cv2.COLOR_BGR2GRAY)

    # Blur the image for easier detection circle / rectangle detection.
    img = cv2.blur(img, (3, 3))
    cv2.imshow('Median Blur', img)

    # Detect Circles.
    circles = cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, 1, 90, param1= 31, param2=24, minRadius=15, maxRadius=35)
    circles = np.uint16(np.around(circles))

    return circles

def make_move():
    global first_move
    global board
    global blacks_move
    global imgc

    # If this is the first move, we read an image
    if first_move:
        print("Move your piece, take a picture, and save it in the \"OurMoves\" folder")
        img_name = input("Please enter the name of the file: ")
        imgc = cv2.imread(f"./OurMoves/{img_name}.jpg")
        
    # Draw computers move so the Player can move their piece on the physical board.
    if not first_move:
        move_img = imgc

        p1 = (0, 0)
        p2 = (0, 0)

        for piece in board:
            if (piece.position == blacks_move[0]):
                p1 = piece.point
                piece.checker_type = "empty"
            if (piece.position == blacks_move[1]):
                p2 = piece.point
                piece.checker_type = "black"

        cv2.line(move_img, p1, p2, (0, 255, 0), 10)
        cv2.imshow("Move Black Piece", move_img)

        # Wait for keypress to close.
        print("AI has chosen! Move black piece to the displayed location, then press any key on the image to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # If its not the first move, we need to display the AIs move first, and then our move.
    if not first_move:
        print("Move your piece, take a picture, and save it in the \"OurMoves\" folder")
        img_name = input("Please enter the name of the file: ")
        imgc = cv2.imread(f"./OurMoves/{img_name}.jpg")
    
    # Resize color image.
    dim = (int(imgc.shape[0] * 0.25), int(imgc.shape[1] * 0.25))
    imgc = cv2.resize(imgc, dim, interpolation = cv2.INTER_AREA)

    # Get circles and rectangles
    board_circs = detect_circles(imgc)
    (board_rects, empty_canvas) = detect_rectangles(imgc)

    # Final image will have the empty canvas layered over the original image.
    final_img = imgc

    # Draw rectangles.
    for rect in board_rects:
        color = (0, 255, 0)

        p1 = (int(rect[0]), int(rect[1]))
        p2 = (int(rect[0]+rect[2]), int(rect[1]+rect[3]))

        cv2.rectangle(empty_canvas, p1, p2, color, 2)
        cv2.rectangle(final_img, p1, p2, color, 2)

    # Use rectangles to construct new board.
    new_board = []

    # Draw board_circs and while doing so, determine what each space on the board is (Red, Black or Empty).
    for index, rect in enumerate(board_rects):

        # Here we fill the new_board array with the position / type of each rectangle
        # The position will be 0 - 31 and the type can either be red, black or empty
        rect_type = "empty"

        for circle in board_circs[0, :]:
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

                # Find the RGB values within each board_circs mask
                data = []
                for i in range(3):
                    channel = dst[:, :, i]
                    indices = np.where(channel != 0)[0]
                    color = np.mean(channel[indices])
                    data.append(int(color))

                blue, green, red = data

                color_empty_canvas = (0, 0, 0)
                color_final = (0, 0, 0)

                if (red > 110 and blue < 210 and green < 210):
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

        new_board.append(CheckerSpace(rect_type, index, (rect[0] + 50, rect[1] + 30)))
        
    # Show programs output for spaces + checkers.
    cv2.imshow("Debug Canvas", empty_canvas)

    # Show img with the overlayed empty canvas.
    cv2.imshow("Final", final_img)

    # Find position of moved piece.
    position = 0
    destination = 0
    for space1 in board:
        for space2 in new_board:
            if space1.position == space2.position and space1.checker_type == "red" and space2.checker_type == "empty":
                position = space1.position

    # Find Destination of moved piece
    for space1 in board:
        for space2 in new_board:
            if space1.position == space2.position and space1.checker_type == "empty" and space2.checker_type == "red":
                destination = space1.position
    
    print("Piece moving from: " + str(position))
    print("Piece moving to: " + str(destination))

    first_move = False

    # Old board becomes new board.
    board = new_board

    print("Press any key on the images to continue...")

    # Wait for keypress to close.
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Tell AI what move we've made from reading the image.
    return (position, destination)
