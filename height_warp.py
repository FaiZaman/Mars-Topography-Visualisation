import sys
import cv2
import vtk
import time
from preprocessing import load_obj


# texture and render height map of Mars using elevation data
def compute_height_map(elevation_data_path, texture_data_path):

    start = time.time()
    sphere_height, sphere_width = 1959, 1962

    # create sphere and set values
    mars = vtk.vtkSphereSource()
    mars.SetCenter(0.0, 0.0, 0.0)
    mars.SetRadius(978)
    mars.SetThetaResolution(sphere_width)
    mars.SetPhiResolution(sphere_height)
    mars.Update()

    colours = vtk.vtkNamedColors()  # initalise colours
    num_points = mars.GetOutput().GetPoints().GetNumberOfPoints()

    # load data
    height_list = load_obj('data/elevation_map')

    # create data structure for heights to set scalars
    height_scalars = vtk.vtkDoubleArray()
    height_scalars.SetNumberOfTuples(num_points)

    # set the height values in the data structure
    for index in range(0, len(height_list)):

        height = height_list[index] + 8
        height_scalars.SetTuple1(index, height)

    # assign to sphere
    mars.GetOutput().GetPointData().SetScalars(height_scalars)

    # creating a warp based on height values and setting the colours
    warp = vtk.vtkWarpScalar()
    warp.SetInputConnection(mars.GetOutputPort())
    warp.SetScaleFactor(5)

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
    map_to_sphere.PreventSeamOff()

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
    water.SetRadius(950)
    water.SetThetaResolution(sphere_width)
    water.SetPhiResolution(sphere_height)
    water.Update()

    # set water mapper
    water_mapper = vtk.vtkPolyDataMapper()
    water_mapper.SetInputConnection(water.GetOutputPort())

    # create water actor and set to blue
    water_actor = vtk.vtkActor()
    water_actor.SetMapper(water_mapper)
    water_actor.GetProperty().SetColor(colours.GetColor3d("DeepSkyBlue"))

    # set camera perspective
    camera = vtk.vtkCamera()
    camera.SetPosition(1000, 1000, 1000)
    camera.SetFocalPoint(0, 978, 0)

    # initialise a renderer and set parameters
    renderer = vtk.vtkRenderer()
    #renderer.SetActiveCamera(camera)
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetWindowName("Mars Elevation Map")
    renderWindow.SetSize(1500, 700)
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # add actors and set background colour
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
    SliderRepresentation.SetMaximumValue(10)
    SliderRepresentation.SetValue(5)

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

    # changes scale factor based on slider
    def update_water_radius(obj, event):

        water_radius = obj.GetRepresentation().GetValue()
        water.SetRadius(water_radius)
    
    # parameters for water radius slider
    WaterSliderRepresentation = vtk.vtkSliderRepresentation2D()
    WaterSliderRepresentation.SetMinimumValue(950)
    WaterSliderRepresentation.SetMaximumValue(1100)
    WaterSliderRepresentation.SetValue(950)

    # set coordinates of slider
    WaterSliderRepresentation.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    WaterSliderRepresentation.GetPoint1Coordinate().SetValue(0.25, 0.9)
    WaterSliderRepresentation.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    WaterSliderRepresentation.GetPoint2Coordinate().SetValue(0.75, 0.9)

    # more slider parameters
    WaterSliderRepresentation.SetTitleText('Water Radius')
    WaterSliderRepresentation.SetSliderLength(0.02)
    WaterSliderRepresentation.SetSliderWidth(0.03)

    # create slider widget, assign parameters, and update water radius based on slider changes
    WaterSliderWidget = vtk.vtkSliderWidget()
    WaterSliderWidget.SetInteractor(renderWindowInteractor)
    WaterSliderWidget.SetRepresentation(WaterSliderRepresentation)
    WaterSliderWidget.SetEnabled(True)
    WaterSliderWidget.AddObserver("InteractionEvent", update_water_radius)

    end = time.time()
    print("Total time taken:", round(end - start, 2), "seconds")

    # render the planet
    renderWindow.Render()
    renderWindowInteractor.Start()


if __name__ == '__main__':

    # get arguments
    file_paths = sys.argv
    elevation_data_path, texture_path = file_paths[1], file_paths[2]

    # flip the texture and save it to align properly with warp
    texture = cv2.imread(texture_path, cv2.IMREAD_COLOR)
    flipped_texture = cv2.flip(texture, 1)
    flipped_texture_path = 'data/flipped_texture.jpg'
    cv2.imwrite(flipped_texture_path, flipped_texture)

    compute_height_map(elevation_data_path, flipped_texture_path)
