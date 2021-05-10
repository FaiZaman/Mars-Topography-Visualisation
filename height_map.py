import cv2
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

        # assign height from west image
        if z_coordinate >= 0:

            # query tree for closest image and fetch height
            _, index = west_tree.query(sphere_point_xy, k=1)
            coordinate = west_image_coordinates[index]
            height = height_map_west[coordinate]

        # assign height from east image
        else:

            # query tree for closest image and fetch height
            _, index = east_tree.query(sphere_point_xy, k=1)
            coordinate = east_image_coordinates[index]
            height = height_map_east[coordinate]

        # add to list
        height_list.append(height)

    return height_list


# converts xyh to xyz for sphere geometry
def map_to_sphere(path):

    # read in image and separate west and east projections into two images
    image = cv2.imread(path, cv2.IMREAD_COLOR)
    image = cv2.GaussianBlur(image, (5, 5), 0)

    west_image = image[151:2111, 13:1975].copy()
    east_image = image[151:2111, 2027:3989].copy()

    # set image dimensions, centre and radius
    height, width, channels = west_image.shape
    centre = (980, 981)
    radius = 980

    # read colour map
    start = time.time()
    print("Reading colour map")
    colour_map_dict = read_colour_map(image)

    # read height data and save
    print("Reading height data")
    #height_map_west = assign_heights(west_image, centre, colour_map_dict)
    #height_map_east = assign_heights(east_image, centre, colour_map_dict)
    #save_obj(height_map_west, 'data/height_map_west')
    #save_obj(height_map_east, 'data/height_map_east')

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

    # initalise point data and their size
    point_data = sphere.GetOutput().GetPoints()
    num_points = point_data.GetNumberOfPoints()

    # retrieve list of corresponding heights and save
    print("Assigning scalar heights")
    #height_list = get_scalar_heights(point_data, num_points, height_map_west, height_map_east)
    #save_obj(height_list, 'data/elevation_map')

    # load height data
    height_list = load_obj('data/elevation_map')

    # create data structure for heights to set scalars
    height_scalars = vtk.vtkDoubleArray()
    height_scalars.SetNumberOfTuples(1046530)

    # set the height values in the data structure
    for index in range(0, len(height_list)):

        height = height_list[index]
        height_scalars.SetTuple1(index, height)

    # assign to sphere
    sphere.GetOutput().GetPointData().SetScalars(height_scalars)

    end = time.time()
    print("Time taken:", end - start)

    # creating a warp based on height values and setting the colours
    warp = vtk.vtkWarpScalar()
    warp.SetInputConnection(sphere.GetOutputPort())
    warp.SetScaleFactor(2.5)
    colors = vtk.vtkNamedColors()

    # initialise a mapper to map sphere data
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(warp.GetOutputPort())

    # use actor to set colours
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d("Cornsilk"))

    # initialise a renderer and set parameters
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetWindowName("Sphere")
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # add actor and set background colour
    renderer.AddActor(actor)
    renderer.SetBackground(colors.GetColor3d("Black"))

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

    # render the planet
    renderWindow.Render()
    renderWindowInteractor.Start()

if __name__ == '__main__':

    path = 'data/elevationData.tif'
    map_to_sphere(path)
