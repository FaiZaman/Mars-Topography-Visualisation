import vtk
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
def assign_heights(image, centre, colour_map_dict):

    # initialise height dictionary and dimensions
    pixel_height_dict = {}
    height, width, channels = image.shape

    # initialise centre coordinates
    y_centre, x_centre = centre[0], centre[1]

    # assign
    for y in range(0, height):
        for x in range(0, width):

            # retrieve height for pixel if not black
            pixel = tuple(image[y][x])
            if not (pixel[0] == pixel[1] == pixel[2] == 0):

                # get closest RGB pixel if not in dict
                if pixel not in colour_map_dict:
                    pixel = min(colour_map_dict, key=lambda x: difference(x, pixel))

                # set coordinates for sphere
                x_coordinate = x - x_centre
                y_coordinate = y - y_centre

                # get height and assign
                height = colour_map_dict[pixel]
                pixel_height_dict[(y_coordinate, x_coordinate)] = height

    return pixel_height_dict


# calculate difference between two RGB values
def difference(m, n):

    r1, g1, b1 = m[0], m[1], m[2]
    r2, g2, b2 = n[0], n[1], n[2]
    d = math.sqrt((r2-r1)**2+(g2-g1)**2+(b2-b1)**2)

    return d


# converts xyh to xyz for sphere geometry
def map_to_sphere(path):

    # read in image and set dimensions
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    height, width, channels = image.shape
    radius = 3390

    # separate west and east projections into two images
    west_image = image[151:2111, 13:1975].copy()
    east_image = image[151:2111, 2027:3989].copy()
    centre = (980, 981)

    start = time.time()

    # read colour map
    colour_map_dict = read_colour_map(image)

    # read height data and assign
    pixel_height_dict_1 = assign_heights(west_image, centre, colour_map_dict)
    pixel_height_dict_2 = assign_heights(east_image, centre, colour_map_dict)
    end = time.time()
    print("Time taken: ", end - start)

    # projecting data onto sphere
    warp = vtk.vtkWarpScalar()
    warp.SetInputConnection(height_map_west)
    warp.SetScaleFactor(-0.1)

if __name__ == '__main__':

    path = 'data/elevationData.tif'
    map_to_sphere(path)
