import vtk
from height_map import load_data

# custom lookup table for mapper and scalar bar
#lut = vtk.vtkLookupTable()
#lut.Build()

# set lookup table to mapper
#mapper.SetScalarRange(-8, 14)
#mapper.SetLookupTable(lut)

# create the scalar_bar
#scalar_bar = vtk.vtkScalarBarActor()
#scalar_bar.SetOrientationToHorizontal()
#scalar_bar.SetLookupTable(lut)

# create scalar bar widget
#scalar_bar_widget = vtk.vtkScalarBarWidget()
#scalar_bar_widget.SetInteractor(renderWindowInteractor)
#scalar_bar_widget.SetScalarBarActor(scalar_bar)
#scalar_bar_widget.On()

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
    map_to_sphere.PreventSeamOn()

    # create mapper and set the mapped texture as input
    texture_mapper = vtk.vtkPolyDataMapper()
    texture_mapper.SetInputConnection(map_to_sphere.GetOutputPort())
    texture_mapper.ScalarVisibilityOff()

    # create actor and set the mapper and the texture
    texture_actor = vtk.vtkActor()
    texture_actor.SetMapper(texture_mapper)
    texture_actor.SetTexture(texture)

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

    # assign to sphere and initialise scalar range of heights
    mars.GetOutput().GetPointData().SetScalars(height_scalars)
    scalarRange = [-8, 14]

    # create contour filter and generate values of 1km increments for isolines
    ContourFilter = vtk.vtkContourFilter()
    ContourFilter.SetInputConnection(mars.GetOutputPort())
    ContourFilter.GenerateValues(23, scalarRange)

    # create isoline mapper, set the contour filter as input, and set scalar range
    isoline_mapper = vtk.vtkPolyDataMapper()
    isoline_mapper.SetInputConnection(ContourFilter.GetOutputPort())
    isoline_mapper.SetScalarRange(scalarRange)

    # create isoline actor and set contour filter mapper
    isoline_actor = vtk.vtkActor()
    isoline_actor.SetMapper(isoline_mapper)

    # initialise a renderer and set parameters
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetWindowName("Mars Elevation Map")
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # add actor and set background colour
    renderer.AddActor(texture_actor)
    renderer.AddActor(isoline_actor)
    renderer.SetBackground(colours.GetColor3d("Black"))

    # render the planet
    renderWindow.Render()
    renderWindowInteractor.Start()


if __name__ == '__main__':

    elevation_data_path = 'data/elevationData.tif'
    texture_data_path = 'data/marsTexture.jpg'
    compute_isolines(elevation_data_path, texture_data_path)
