import cv2
import math
import time
import pickle


# functions to save and load height data
def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name ):
    with open(name + '.pkl', 'rb') as f:
        return pickle.load(f)


# read the colour map
def read_colour_map(image):

    # initialise colour map and height dictionaries
    colour_map_dict = {}

    # read in image and narrow down to colour map area
    colour_map_image = image[2200:2550]

    # set dimensions and middle value
    _, width, _ = image.shape
    middle = colour_map_image.shape[0] // 2

    # initialise values to read in colour map
    recording = False
    pixel_height_change = 1/115
    pixel_height_value = -8 + pixel_height_change

    """
    10 pixels in initial white bar
    ~115 pixels between bars
    1/115 change per pixel
    """

    x = 0

    # loop through the middle row
    while x < width:

        pixel = colour_map_image[middle][x]  # set pixel

        # check if white
        if pixel[0] == pixel[1] == pixel[2] == 255:

            # once the colourmap has been reached start recording
            recording = True

        else:

            # once recording has started
            if recording:

                # break if we go out of bounds
                if pixel[0] == pixel[1] == pixel[2] == 0:
                    break

                # assign the height value for colour of current pixel
                colour_map_dict[tuple(pixel)] = pixel_height_value
                pixel_height_value += pixel_height_change

                if abs(pixel_height_value - int(pixel_height_value)) < pixel_height_change:
                    x += 7

        x += 1

    colour_map_dict[(255, 255, 255)] = 14   # edge case
    return colour_map_dict


# assign each pixel a height value based on colourmap
def assign_heights(image, colour_map_dict):

    # initialise height dictionary and dimensions
    pixel_height_dict = {}
    height, width, channels = image.shape
    print(height, width)
    # assign
    for y in range(0, height):
        for x in range(0, width):

            if y % 10 == 0 and x % 10 == 0:
                print(y, x)

            # retrieve height for pixel if not black
            pixel = tuple(image[y][x])
            if not (pixel[0] == pixel[1] == pixel[2] == 0):

                # get closest RGB pixel if not in dict
                if pixel not in colour_map_dict:
                    print('not there')
                    pixel = min(colour_map_dict, key=lambda x: difference(x, pixel))

                # assign height to pixel coordinates
                height = colour_map_dict[pixel]
                pixel_height_dict[(y, x)] = height

    return pixel_height_dict


# calculate difference between two RGB values
def difference(m, n):

    r1, g1, b1 = m[0], m[1], m[2]
    r2, g2, b2 = n[0], n[1], n[2]
    d = math.sqrt((r2-r1)**2+(g2-g1)**2+(b2-b1)**2)

    return d


# converts xyh to xyz for sphere geometry
def map_to_sphere(path):

    image = cv2.imread(path, cv2.IMREAD_COLOR)
    height, width, channels = image.shape
    radius = 3390

    west_image = image[0:height, :2000].copy()
    east_image = image[0:height, 2000:].copy()

    start = time.time()

    colour_map_dict = read_colour_map(image)
    #pixel_height_dict_1 = assign_heights(west_image, colour_map_dict)
    #pixel_height_dict_2 = assign_heights(east_image, colour_map_dict)
    end = time.time()
    print("Time taken: ", end - start)

    height_map_west = load_obj('height_map_west')
    height_map_east = load_obj('height_map_east')

if __name__ == '__main__':

    path = 'data/elevationData.tif'
    map_to_sphere(path)
