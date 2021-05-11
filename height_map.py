import cv2
from numpy.lib.function_base import median
import vtk
import cv2
import time
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
        r, g, b = pixel[0], pixel[1], pixel[2]

        # check if white
        if r == g == b == 255:

            # once the colourmap has been reached start recording
            recording = True

        else:

            # once recording has started
            if recording:

                # break if we go out of bounds
                if r == g == b == 0:
                    break

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
    elevation_image = cv2.GaussianBlur(elevation_image, (5, 5), 0)

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
    save_obj(height_map_west, 'data/height_map_west')
    save_obj(height_map_east, 'data/height_map_east')

    # retrieve list of corresponding heights and save
    print("Assigning scalar heights")
    height_list = get_scalar_heights(point_data, num_points, height_map_west, height_map_east)
    save_obj(height_list, 'data/elevation_map')

    return height_list


def load_data():

    # load the height data
    height_map_west = load_obj('data/height_map_west')
    height_map_east = load_obj('data/height_map_east')

    # load height scalars
    height_list = load_obj('data/elevation_map')

    return height_map_west, height_map_east, height_list


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
def calculate_height(sphere_point_xy, tree, coordinates, height_map):

    # query tree for 500 closest image coordinates and initialise neighbour pixel heights
    _, index = tree.query(sphere_point_xy, k=500, workers=-1)
    neighbour_heights = []

    # retrieve heights for neighbouring pixels and add to list
    for neighbour_index in index:
        coordinate = coordinates[neighbour_index]
        neighbour_height = height_map[coordinate]
        neighbour_heights.append(neighbour_height)

    # take height as median of neighbour pixels
    height = np.median(neighbour_heights)
    return height


# match closest image coordinate to sphere xy coordinate and fetch its height
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

        # get xy coordinates of sphere point and fetch closest point in image coordinates
        sphere_point_xy = (point[0], point[1])
        z_coordinate = point[2]

        # fetch height for the current pixel
        if z_coordinate >= 0:
            height = calculate_height(sphere_point_xy, west_tree, west_image_coordinates, height_map_west)
        else:
            height = calculate_height(sphere_point_xy, east_tree, east_image_coordinates, height_map_east)

        # add to list
        height_list.append(height)

    return height_list


# texture and render height map of Mars using elevation data
def compute_height_map(elevation_data_path, texture_data_path):

    start = time.time()

    # create sphere and set values
    mars = vtk.vtkSphereSource()
    mars.SetCenter(0.0, 0.0, 0.0)
    mars.SetRadius(978)
    mars.SetThetaResolution(1962)
    mars.SetPhiResolution(1959)
    mars.Update()

    colours = vtk.vtkNamedColors()  # initalise colours

    # initalise point data and their size
    point_data = mars.GetOutput().GetPoints()
    num_points = point_data.GetNumberOfPoints()

    # preprocess or load data
    #height_list = preprocess(elevation_data_path, point_data, num_points)
    height_map_west, height_map_east, height_list = load_data()

    # create data structure for heights to set scalars
    height_scalars = vtk.vtkDoubleArray()
    height_scalars.SetNumberOfTuples(num_points)

    # set the height values in the data structure
    for index in range(0, len(height_list)):

        height = height_list[index]
        height_scalars.SetTuple1(index, height)

    # assign to sphere
    mars.GetOutput().GetPointData().SetScalars(height_scalars)

    # creating a warp based on height values and setting the colours
    warp = vtk.vtkWarpScalar()
    warp.SetInputConnection(mars.GetOutputPort())
    warp.SetScaleFactor(2.5)

    # initialise a mapper to map sphere data
    height_mapper = vtk.vtkPolyDataMapper()
    height_mapper.SetInputConnection(warp.GetOutputPort())
    height_mapper.ScalarVisibilityOff()

    # use actor to set colours
    height_actor = vtk.vtkActor()
    height_actor.SetMapper(height_mapper)

    # read the image data from a file
    reader = vtk.vtkJPEGReader()
    reader.SetFileName(texture_data_path)

    # create texture object
    texture = vtk.vtkTexture()
    texture.SetInputConnection(reader.GetOutputPort())

    # map texture coordinates onto warped geometry
    map_to_sphere = vtk.vtkTextureMapToSphere()
    map_to_sphere.SetInputConnection(warp.GetOutputPort())
    map_to_sphere.PreventSeamOn()

    # create mapper and set the mapped texture as input
    texture_mapper = vtk.vtkPolyDataMapper()
    texture_mapper.SetInputConnection(map_to_sphere.GetOutputPort())
    texture_mapper.ScalarVisibilityOff()

    # create actor and set the mapper and the texture
    texture_actor = vtk.vtkActor()
    texture_actor.SetMapper(texture_mapper)
    texture_actor.SetTexture(texture)

    # generate water sphere
    water = vtk.vtkSphereSource()
    water.SetCenter(0.0, 0.0, 0.0)
    water.SetRadius(978)
    water.SetThetaResolution(1962)
    water.SetPhiResolution(1959)
    water.Update()

    # set water mapper
    water_mapper = vtk.vtkPolyDataMapper()
    water_mapper.SetInputConnection(water.GetOutputPort())

    # create water actor and set to blue
    water_actor = vtk.vtkActor()
    water_actor.SetMapper(water_mapper)
    water_actor.GetProperty().SetColor(colours.GetColor3d("DeepSkyBlue"))

    # initialise a renderer and set parameters
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetWindowName("Mars Elevation Map")
    renderWindow.SetSize(1900, 1000)
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # add actor and set background colour
    renderer.AddActor(height_actor)
    renderer.AddActor(texture_actor)
    renderer.AddActor(water_actor)
    renderer.SetBackground(colours.GetColor3d("Black"))

    # changes scale factor based on slider
    def update_scale_factor(obj, event):

        scale_factor = obj.GetRepresentation().GetValue()
        warp.SetScaleFactor(scale_factor)

    # parameters for scale factor slider
    SliderRepresentation = vtk.vtkSliderRepresentation2D()
    SliderRepresentation.SetMinimumValue(0)
    SliderRepresentation.SetMaximumValue(5)
    SliderRepresentation.SetValue(2.5)

    # set coordinates of slider
    SliderRepresentation.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    SliderRepresentation.GetPoint1Coordinate().SetValue(0.25, 0.1)
    SliderRepresentation.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    SliderRepresentation.GetPoint2Coordinate().SetValue(0.75, 0.1)

    # more slider parameters
    SliderRepresentation.SetTitleText('Scale Factor')
    SliderRepresentation.SetSliderLength(0.02)
    SliderRepresentation.SetSliderWidth(0.03)

    # create slider widget, assign parameters, and update scale factor based on slider changes
    SliderWidget = vtk.vtkSliderWidget()
    SliderWidget.SetInteractor(renderWindowInteractor)
    SliderWidget.SetRepresentation(SliderRepresentation)
    SliderWidget.SetEnabled(True)
    SliderWidget.AddObserver("InteractionEvent", update_scale_factor)

    end = time.time()
    print("Total time taken:", round(end - start, 2), "seconds")

    # render the planet
    renderWindow.Render()
    renderWindowInteractor.Start()


if __name__ == '__main__':

    # passing paths to functions
    elevation_data_path = 'data/elevationData.tif'
    texture_data_path = 'data/marsTexture.jpg'
    compute_height_map(elevation_data_path, texture_data_path)
