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

def remove_piece(position):
    for piece in board:
        if piece.position == position:
            piece.checker_type = "empty"

# If the black piece has skipped over a column, we know that it has capture
# one of our pieces, so we need to remove that piece from the board.
def capture_piece(blacks_move, position):
    if (blacks_move[0] - 16 + 2 == blacks_move[1]):
        print(f'REMOVING PIECE: {blacks_move[0] - 8 + 1}')
        remove_piece(blacks_move[0] - 8 + 1)
    if (blacks_move[0] - 16 - 2 == blacks_move[1]):
        print(f'REMOVING PIECE: {blacks_move[0] - 8 - 1}')
        remove_piece(blacks_move[0] - 8 - 1)
    if (blacks_move[0] + 16 + 2 == blacks_move[1]):
        print(f'REMOVING PIECE: {blacks_move[0] + 8 + 1}')
        remove_piece(blacks_move[0] + 8 + 1)
    if (blacks_move[0] + 16 - 2 == blacks_move[1]):
        print(f'REMOVING PIECE: {blacks_move[0] + 8 - 1}')
        remove_piece(blacks_move[0] + 8 - 1)

def resize(img):

    width = int(img.shape[1] * .15)
    height = int(img.shape[0] * .15)
    dim = (width, height)
    
    # resize image
    return cv2.resize(img, dim, interpolation = cv2.INTER_AREA)


# Detects squares on board and returns those squares as OpenCV bounding Rectangles,
# and an empty canvas to display said rectangles.
def detect_rectangles(imgc):

    # convert to hsv
    hsv = cv2.cvtColor(imgc, cv2.COLOR_BGR2HSV)
    cv2.imshow("hsv", resize(hsv))

    # Threshold the HSV, trying to extract the yellow lines from the board.
    hsv_thresh = cv2.inRange(hsv, (5, 100, 100), (30, 255, 255))
    cv2.imshow("HSV Threshold", resize(hsv_thresh))

    # Dilate the line so that slightly broken lines become connected.
    kernel = np.ones((30,30), np.uint8)  
    hsv_thresh = cv2.dilate(hsv_thresh, kernel, iterations=1)
    cv2.imshow("HSV Threshold Dilated", resize(hsv_thresh))

    # Detect edges using Canny
    canny_output = cv2.Canny(hsv_thresh, 90, 270)
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

    mean_height = 0
    mean_width = 0
    max_height = 0
    max_width = 0
    min_width = 1000
    min_height = 1000
    rec_count = 0

    # Capture rectangles by drawing bounding rectangles around contours.
    for i in range(len(contours)):
        p1 = (int(boundRect[i][0]), int(boundRect[i][1]))
        p2 = (int(boundRect[i][0]+boundRect[i][2]), int(boundRect[i][1]+boundRect[i][3]))

        width = abs(p2[0] - p1[0])
        height = abs(p2[1] - p1[1])

        # Filter out any rectangles not part of the board.
        if(width > 280 and width < 330 and height > 250 and height < 330):

            # Collect stats for debugging.
            max_width = max(max_width, width)
            max_height = max(max_height, height)
            min_width = min(min_width, width)
            min_height = min(min_height, height)
            rec_count += 1
            mean_width += width
            mean_height += height

            checker_spaces.append(boundRect[i])

    mean_width /= rec_count
    mean_height /= rec_count

    print(f'Rectangle Stats:\n-----\nMean Width: {int(mean_width)} \nMax Width: {int(max_width)} \nMin Width: {min_width} \nMean Height: {int(mean_height)} \nMax Height {max_height} \nMin Height {min_height}\n-----')

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

    print(f'Total Checkers Detected (Should be 64): {len(final_checkers)}')
    return (final_checkers, empty_canvas)

def detect_circles(imgc):

    # Read image and convert to gray scale.
    img_gray = cv2.cvtColor(imgc, cv2.COLOR_BGR2GRAY)

    # Blur the image for easier detection circle / rectangle detection.
    img_gray = cv2.blur(img_gray, (20, 20))
    # Detect Circles.
    circles = cv2.HoughCircles(img_gray, cv2.HOUGH_GRADIENT, 1, 350, param1=19, param2=20, minRadius=105, maxRadius=120)
    circles = np.uint16(np.around(circles))

    return (circles, img_gray)

def draw_board(imgc, images, board_rects, board_circs):

    # Draw rectangles.
    for rect in board_rects:
        color = (0, 255, 0)

        p1 = (int(rect[0]), int(rect[1]))
        p2 = (int(rect[0]+rect[2]), int(rect[1]+rect[3]))

        for img in images:
            cv2.rectangle(img, p1, p2, color, 15)

    # Use rectangles to construct new board by iterating over circles.
    new_board = []

    # Draw circles and while doing so, determine what each space on the board is (Red, Black or Empty).
    for position, rect in enumerate(board_rects):

        # Here we fill the new_board array with the position / type of each rectangle
        # The position will be 0 - 31 and the type can either be red, black or empty
        rect_type = "empty"

        for circle in board_circs[0, :]:
            x, y, r = circle

            # If their is a piece on the square
            if (x > rect[0] and x < rect[0]+rect[2] and y > rect[1] and y < rect[1]+rect[3]):
                # This next bit of code is how we find what color the piece is

                # Crete a black screen with a white circle as a mask
                mask = np.zeros(imgc.shape[:2], dtype="uint8")
                cv2.circle(mask, (x, y), circle[2], (255, 255, 255), -1)
            
                # Find the average values of the mask within said image.
                mean = cv2.mean(imgc, mask)

                # Only need average red value to figure out if it's red or black.
                b, g, r, _ = mean

                if (r > 115):
                    rect_type = "red"
                else:
                    rect_type = "black"

                color = (255, 255, 255)

                # Draw circle outline + center dot.
                center = (circle[0], circle[1])
                radius = circle[2]

                for index, img in enumerate(images):
                    color = None

                    if (rect_type == "red" and index == 0):
                        color = (255, 255, 255)
                    elif (rect_type == "red" and index == 1):
                        color = (0, 0, 255)
                    elif (rect_type == "red" and index == 2):
                        color = (0, 0, 0)
                    elif (rect_type == "black" and index == 0):
                        color = (0, 0, 0)
                    elif (rect_type == "black" and index == 1):
                        color = (255, 200, 0)
                    else:
                        color = (255, 255, 255)

                    cv2.circle(img, center, 1, color, 15)
                    cv2.circle(img, center, radius, color, 15)
                break

        new_board.append(CheckerSpace(rect_type, position, (rect[0] + 50, rect[1] + 30)))

    return new_board

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
        capture_piece(blacks_move, board)

        for piece in board:
            if (piece.position == blacks_move[0]):
                p1 = (piece.point[0] + 130, piece.point[1] + 130)
                piece.checker_type = "empty"
            if (piece.position == blacks_move[1]):
                p2 = (piece.point[0] + 130, piece.point[1] + 130)
                piece.checker_type = "black"

        cv2.line(move_img, p1, p2, (0, 255, 0), 30)

        # resize image and display
        cv2.imshow("Move Black Piece", resize(move_img))

        # Wait for keypress to close.
        print("AI has chosen! Move black piece to the displayed location, then press any key on the image to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # If its not the first move, we need to display the AIs move first, and then our move.
    if not first_move:
        print("Move your piece, take a picture, and save it in the \"OurMoves\" folder")
        img_name = input("Please enter the name of the file: ")
        imgc = cv2.imread(f"./OurMoves/{img_name}.jpg")
    
    # Get circles and rectangles
    (board_circs, img_gray) = detect_circles(imgc)
    (board_rects, empty_canvas) = detect_rectangles(imgc)

    # Create a new board as an array, and draw the rectangles and circles on the passed in array of images.
    new_board = draw_board(imgc, [img_gray, empty_canvas, imgc], board_rects, board_circs)

    # Show grayed image.
    cv2.imshow('Median Blur', resize(img_gray))
        
    # Show programs output for spaces + checkers.
    cv2.imshow("Debug Canvas", resize(empty_canvas))

    # Show img with the overlayed empty canvas.
    cv2.imshow("Final", resize(imgc))

    # Find Position of piece before it moves.
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
