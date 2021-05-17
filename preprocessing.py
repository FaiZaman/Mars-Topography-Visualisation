import sys
import cv2
import vtk
import pickle
import numpy as np
from scipy.spatial import KDTree
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
    hsvImage = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # set value to 255
    for y in range(0, hsvImage.shape[0]):
        for x in range(0, hsvImage.shape[1]):
            hsvImage[y][x][2] = 255

    image = cv2.cvtColor(hsvImage, cv2.COLOR_HSV2BGR)

    # initialise values to read in colour map
    pixel_height_change = 1/115
    pixel_height_value = -8 + pixel_height_change

    """
    ~115 pixels between bars
    1/115 change per pixel
    """

    x = 651

    while x < 3340:

        # get pixel and its rgb values
        pixel = image[2350][x]
        r, g, b = pixel[0], pixel[1], pixel[2]

        # assign the height value for colour of current pixel
        colour_map_dict[(r, g, b)] = pixel_height_value
        pixel_height_value += pixel_height_change

        if abs(pixel_height_value - int(pixel_height_value)) < pixel_height_change:
            x += 7

        x += 1

    colour_map_dict[(255, 255, 255)] = 14   # edge case
    return colour_map_dict


# preprocess by computing colourmap, heights, and their scalars
def preprocess(elevation_data_path, point_data, num_points):

    # read in image and separate west and east projections into two images
    elevation_image = cv2.imread(elevation_data_path, cv2.IMREAD_COLOR)

    # split west and east hemisphere images and set centre
    west_image = elevation_image[151:2111, 13:1975].copy()
    east_image = elevation_image[151:2111, 2027:3989].copy()
    centre = (980, 981)

    # read colour map
    print("Reading colour map")
    colour_map_dict = read_colour_map(elevation_image)

    # read height data and save
    print("Reading height data")
    height_map_west = assign_heights(west_image, centre, colour_map_dict)
    height_map_east = assign_heights(east_image, centre, colour_map_dict)

    # retrieve list of corresponding heights and save
    print("Assigning scalar heights")
    height_list = get_scalar_heights(point_data, num_points, height_map_west, height_map_east)
    save_obj(height_list, 'data/elevation_map')

    return height_list


# assign each pixel a height value based on colourmap
def assign_heights(image, centre, colour_map_dict):

    # assign colours in colourmap to image
    colours = np.array(list(colour_map_dict.keys()))    
    image = colours[cKDTree(colours).query(image, k=1, workers=-1)[1]]

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


# get height for current pixel by calculating median of heights of neighbouring pixels for smoother sphere
def calculate_height(sphere_point_xz, tree, coordinates, height_map):

    # query tree for 500 closest image coordinates and initialise neighbour pixel heights
    _, index = tree.query(sphere_point_xz, k=500, workers=-1)
    neighbour_heights = []

    # retrieve heights for neighbouring pixels and add to list
    for neighbour_index in index:
        coordinate = coordinates[neighbour_index]
        neighbour_height = height_map[coordinate]
        neighbour_heights.append(neighbour_height)

    # take height as median of neighbour pixels
    height = np.median(neighbour_heights)
    return height


# match closest image coordinate to sphere xz coordinate and fetch its height
def get_scalar_heights(point_data, num_points, height_map_west, height_map_east):

    # initialise height list
    height_list = []

    # get list of image coordinates
    west_image_coordinates = list(height_map_west.keys())
    east_image_coordinates = list(height_map_east.keys())

    # initialise trees for west and east images
    west_tree = KDTree(west_image_coordinates)
    east_tree = KDTree(east_image_coordinates)

    # get list of points in sphere currently
    for i in range(0, num_points):

        point = point_data.GetPoint(i)  # initialise point

        # get xz coordinates of sphere point and fetch closest point in image coordinates
        sphere_point_xz = (point[2], point[0])
        y_coordinate = point[1]

        # fetch height for the current pixel
        if y_coordinate >= 0:
            height = calculate_height(sphere_point_xz, west_tree, west_image_coordinates, height_map_west)
        else:
            height = calculate_height(sphere_point_xz, east_tree, east_image_coordinates, height_map_east)

        # add to list
        height_list.append(height)

    return height_list


if __name__ == '__main__':

    # get arguments
    file_paths = sys.argv
    elevation_data_path, texture_path = file_paths[1], file_paths[2]
    sphere_height, sphere_width = 1959, 1962

    # create sphere and set values
    mars = vtk.vtkSphereSource()
    mars.SetCenter(0.0, 0.0, 0.0)
    mars.SetRadius(978)
    mars.SetThetaResolution(sphere_width)
    mars.SetPhiResolution(sphere_height)
    mars.Update()

    # initalise point data and their size
    point_data = mars.GetOutput().GetPoints()
    num_points = point_data.GetNumberOfPoints()

    preprocess(elevation_data_path, point_data, num_points)
