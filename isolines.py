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

    colors = vtk.vtkNamedColors()

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

    # initialise a renderer and set parameters
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetWindowName("Mars Elevation Map")
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # add actor and set background colour
    renderer.AddActor(texture_actor)
    renderer.SetBackground(colors.GetColor3d("Black"))

    # render the planet
    renderWindow.Render()
    renderWindowInteractor.Start()


if __name__ == '__main__':

    elevation_data_path = 'data/elevationData.tif'
    texture_data_path = 'data/marsTexture.jpg'
    compute_isolines(elevation_data_path, texture_data_path)
