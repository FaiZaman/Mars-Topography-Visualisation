import vtk
import cv2
import math
import time
import pickle
import numpy as np
from scipy.spatial import cKDTree


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

    # assign colours in colourmap to image
    colours = np.array(list(colour_map_dict.keys()))    
    image = colours[cKDTree(colours).query(image, k=1)[1]]

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

                # set coordinates for sphere
                x_coordinate = x - x_centre
                y_coordinate = y - y_centre

                # get height and assign
                height = colour_map_dict[pixel]
                pixel_height_dict[(y_coordinate, x_coordinate)] = height

    return pixel_height_dict


# converts xyh to xyz for sphere geometry
def map_to_sphere(path):

    # read in image and separate west and east projections into two images
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    west_image = image[151:2111, 13:1975].copy()
    east_image = image[151:2111, 2027:3989].copy()

    # set image dimensions, centre and radius
    height, width, channels = west_image.shape
    centre = (980, 981)
    radius = 980

    # read colour map
    start = time.time()
    colour_map_dict = read_colour_map(image)

    # read height data and assign
    #pixel_height_dict_1 = assign_heights(west_image, centre, colour_map_dict)
    #pixel_height_dict_2 = assign_heights(east_image, centre, colour_map_dict)
    end = time.time()
    print("Time taken:", end - start)

    # load the height data
    height_map_west = load_obj('data/height_map_west')
    height_map_east = load_obj('data/height_map_east')

    # create sphere and set values
    sphere = vtk.vtkSphereSource()
    sphere.SetCenter(0.0, 0.0, 0.0)
    sphere.SetRadius(radius)
    sphere.SetThetaResolution(width)
    sphere.SetPhiResolution(height)
    sphere.Update()

    # initalise point data and list of points on sphere
    point_data = sphere.GetOutput().GetPoints()
    point_list = []

    # get list of points in sphere currently
    for i in range(0, 1046530):
        point = point_data.GetPoint(i)
        point_list.append(point)

    vol = vtk.vtkStructuredPoints()

    # projecting data onto sphere
    warp = vtk.vtkWarpScalar()
    warp.SetInputConnection(height_map_west)
    warp.SetScaleFactor(-0.1)

if __name__ == '__main__':

    path = 'data/elevationData.tif'
    map_to_sphere(path)
