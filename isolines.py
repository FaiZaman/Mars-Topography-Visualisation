import sys
import cv2
import vtk
from preprocessing import load_obj


def compute_isolines(elevation_data_path, texture_data_path):

    # create sphere and set values
    mars = vtk.vtkSphereSource()
    mars.SetCenter(0.0, 0.0, 0.0)
    mars.SetRadius(978)
    mars.SetThetaResolution(1962)
    mars.SetPhiResolution(1959)
    mars.Update()

    colours = vtk.vtkNamedColors()  # initalise colours

    # read the image data from a file
    reader = vtk.vtkJPEGReader()
    reader.SetFileName(texture_data_path)

    # create texture object
    texture = vtk.vtkTexture()
    texture.SetInputConnection(reader.GetOutputPort())

    # map texture coordinates onto warped geometry
    map_to_sphere = vtk.vtkTextureMapToSphere()
    map_to_sphere.SetInputConnection(mars.GetOutputPort())
    map_to_sphere.PreventSeamOff()

    # create mapper and set the mapped texture as input
    texture_mapper = vtk.vtkPolyDataMapper()
    texture_mapper.SetInputConnection(map_to_sphere.GetOutputPort())
    texture_mapper.ScalarVisibilityOff()

    # create actor and set the mapper and the texture
    texture_actor = vtk.vtkActor()
    texture_actor.SetMapper(texture_mapper)
    texture_actor.SetTexture(texture)

    # initalise point data and their size
    num_points = mars.GetOutput().GetPoints().GetNumberOfPoints()

    # load data
    height_list = load_obj('data/elevation_map')

    # create data structure for heights to set scalars
    height_scalars = vtk.vtkDoubleArray()
    height_scalars.SetNumberOfTuples(num_points)

    # set the height values in the data structure
    for index in range(0, len(height_list)):

        height = height_list[index]
        height_scalars.SetTuple1(index, height)

    # assign to sphere and initialise scalar range of heights
    mars.GetOutput().GetPointData().SetScalars(height_scalars)
    scalarRange = [-8, 14]
    num_isolines = 23

    # initialise a renderer and set parameters
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetWindowName("Mars Isolines Map")
    renderWindow.SetSize(1500, 700)
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # create a colour transfer function and set blue/red/yellow colours for isoline colourmap
    ctf = vtk.vtkColorTransferFunction()
    ctf.SetColorSpaceToDiverging()
    ctf.AddRGBPoint(-8, 0, 0, 1)     # blue
    ctf.AddRGBPoint(-1, 1, 1, 1)   # white
    ctf.AddRGBPoint(0, 1, 0, 0)      # red
    ctf.AddRGBPoint(0.1, 1, 1, 1)    # white
    ctf.AddRGBPoint(14, 1, 1, 0)     # yellow

    # create the scalar_bar
    scalarBar = vtk.vtkScalarBarActor()
    scalarBar.SetOrientationToHorizontal()
    scalarBar.SetTitle("Altitude (km)")
    scalarBar.SetNumberOfLabels(num_isolines)
    scalarBar.SetMaximumNumberOfColors(num_isolines)
    scalarBar.SetLookupTable(ctf)

    # create scalar bar widget
    scalarBarWidget = vtk.vtkScalarBarWidget()
    scalarBarWidget.SetInteractor(renderWindowInteractor)
    scalarBarWidget.SetScalarBarActor(scalarBar)
    scalarBarWidget.On()

    # create contour filter and generate values of 1km increments for isolines
    ContourFilter = vtk.vtkContourFilter()
    ContourFilter.SetInputConnection(mars.GetOutputPort())
    ContourFilter.GenerateValues(num_isolines, scalarRange)

    # create isoline mapper, set the contour filter as input, and set scalar range
    isoline_mapper = vtk.vtkPolyDataMapper()
    isoline_mapper.SetInputConnection(ContourFilter.GetOutputPort())
    isoline_mapper.SetScalarRange(scalarRange)
    isoline_mapper.SetLookupTable(ctf)

    # create isoline actor and set contour filter mapper
    isoline_actor = vtk.vtkActor()
    isoline_actor.SetMapper(isoline_mapper)

    # create tube filter
    TubeFilter = vtk.vtkTubeFilter()
    TubeFilter.SetInputConnection(ContourFilter.GetOutputPort())
    TubeFilter.SetRadius(2)
    TubeFilter.SetNumberOfSides(50)
    TubeFilter.Update()

    # create tube mapper and set tube filter as input
    tube_mapper = vtk.vtkPolyDataMapper()
    tube_mapper.SetInputConnection(TubeFilter.GetOutputPort())
    tube_mapper.SetLookupTable(ctf)

    # create tube actor and set tube mapper
    tube_actor = vtk.vtkActor()
    tube_actor.SetMapper(tube_mapper)

    # add actors and set background colour
    renderer.AddActor(texture_actor)
    renderer.AddActor(isoline_actor)
    renderer.AddActor(tube_actor)
    renderer.SetBackground(colours.GetColor3d("Black"))

    # changes tube radius based on slider
    def update_tube_radius(obj, event):

        tube_radius = obj.GetRepresentation().GetValue()
        TubeFilter.SetRadius(tube_radius)

    # parameters for tube radius slider
    SliderRepresentation = vtk.vtkSliderRepresentation2D()
    SliderRepresentation.SetMinimumValue(0)
    SliderRepresentation.SetMaximumValue(5)
    SliderRepresentation.SetValue(3)

    # set coordinates of slider
    SliderRepresentation.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
    SliderRepresentation.GetPoint1Coordinate().SetValue(0.25, 0.1)
    SliderRepresentation.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
    SliderRepresentation.GetPoint2Coordinate().SetValue(0.75, 0.1)

    # more slider parameters
    SliderRepresentation.SetTitleText('Tube Radius')
    SliderRepresentation.SetSliderLength(0.02)
    SliderRepresentation.SetSliderWidth(0.03)

    # create slider widget, assign parameters, and update tube radius based on slider changes
    SliderWidget = vtk.vtkSliderWidget()
    SliderWidget.SetInteractor(renderWindowInteractor)
    SliderWidget.SetRepresentation(SliderRepresentation)
    SliderWidget.SetEnabled(True)
    SliderWidget.AddObserver("InteractionEvent", update_tube_radius)

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

    compute_isolines(elevation_data_path, flipped_texture_path)
