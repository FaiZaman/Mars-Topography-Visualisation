import vtk


def MakeElevations(src):
    '''
    Generate elevations over the surface.
    :param: src - the vtkPolyData source.
    :return: - vtkPolyData source with elevations.
    '''
    bounds = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ]
    src.GetBounds(bounds)
    elevFilter = vtk.vtkElevationFilter()
    elevFilter.SetInputData(src)
    elevFilter.SetLowPoint(0, bounds[2], 0)
    elevFilter.SetHighPoint(0, bounds[3], 0)
    elevFilter.SetScalarRange(bounds[2], bounds[3])
    elevFilter.Update()

    return elevFilter.GetPolyDataOutput()


def display_sphere():

    colors = vtk.vtkNamedColors()

    # Create a sphere
    sphereSource = vtk.vtkSphereSource()
    sphereSource.SetCenter(0.0, 0.0, 0.0)
    sphereSource.SetRadius(500)

    # Make the surface smooth.
    sphereSource.SetPhiResolution(1500)
    sphereSource.SetThetaResolution(1500)
    sphereSource.Update()
    src = MakeElevations(sphereSource.GetOutput())

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(sphereSource.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d("Cornsilk"))

    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetWindowName("Sphere")
    renderWindow.AddRenderer(renderer)
    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    renderer.AddActor(actor)
    renderer.SetBackground(colors.GetColor3d("DarkGreen"))

    renderWindow.Render()
    renderWindowInteractor.Start()

def main():
    named_colors = vtk.vtkNamedColors()

    # Create a grid points
    points = vtk.vtkPoints()
    GridSize = 20;
    xx=0.0 
    yy=0.0
    zz=0.0
    rng = vtk.vtkMinimalStandardRandomSequence()
    rng.SetSeed(8775586)  # For testing.
    for x in range(0, GridSize):
        for y in range(0, GridSize):
          rng.Next()
          xx = x + rng.GetRangeValue(-0.2, 0.2)
          rng.Next()
          yy = y + rng.GetRangeValue(-0.2, 0.2)
          rng.Next()
          zz = rng.GetRangeValue(-0.5, 0.5)
          points.InsertNextPoint(xx, yy, zz)


    # Add the grid points to a polydata object
    inputPolyData = vtk.vtkPolyData()
    inputPolyData.SetPoints(points)

    # Triangulate the grid points
    delaunay = vtk.vtkDelaunay2D()
    delaunay.SetInputData(inputPolyData)
    delaunay.Update()
    outputPolyData = delaunay.GetOutput()

    bounds= 6*[0.0]
    outputPolyData.GetBounds(bounds)

    # Find min and max z
    minz = bounds[4]
    maxz = bounds[5]

    print('minz: {:< 6.3}'.format(minz))
    print('maxz: {:< 6.3}'.format(maxz))

    # Create the color map
    colorLookupTable = vtk.vtkLookupTable()
    colorLookupTable.SetTableRange(minz, maxz)
    colorLookupTable.Build()

    # Generate the colors for each point based on the color map
    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName('Colors')

    print( 'There are '+str(outputPolyData.GetNumberOfPoints())+' points.')

    for i in range(0, outputPolyData.GetNumberOfPoints()):
        p= 3*[0.0]
        outputPolyData.GetPoint(i,p)

        dcolor = 3*[0.0]
        colorLookupTable.GetColor(p[2], dcolor);
        # print( 'dcolor: {:<8.6} {:<8.6} {:<8.6}'.format(*dcolor))
        color=3*[0.0]
        for j in range(0,3):
          color[j] = int(255.0 * dcolor[j])
        # print('color:  {:<8} {:<8} {:<8}'.format(*color))

        try:
            colors.InsertNextTupleValue(color)
        except AttributeError:
            # For compatibility with new VTK generic data arrays.
            colors.InsertNextTypedTuple(color)


    outputPolyData.GetPointData().SetScalars(colors)

    # Create a mapper and actor
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(outputPolyData)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # Create a renderer, render window, and interactor
    renderer = vtk.vtkRenderer()
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetWindowName('ColoredElevationMap')

    renderWindowInteractor = vtk.vtkRenderWindowInteractor()
    renderWindowInteractor.SetRenderWindow(renderWindow)

    # Add the actor to the scene
    renderer.AddActor(actor)
    renderer.SetBackground(named_colors.GetColor3d('DarkSlateGray'))

    # Render and interact
    renderWindow.Render()
    renderWindowInteractor.Start()

def sph():
    colors = vtk.vtkNamedColors()

    renderer = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(renderer)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    vol = vtk.vtkStructuredPoints()
    vol.SetDimensions(26, 26, 26)
    vol.SetOrigin(-0.5, -0.5, -0.5)
    sp = 1.0 / 25.0
    vol.SetSpacing(sp, sp, sp)

    scalars = vtk.vtkDoubleArray()
    scalars.SetNumberOfComponents(1)
    scalars.SetNumberOfTuples(26 * 26 * 26)
    for k in range(0, 26):
        z = -0.5 + k * sp
        kOffset = k * 26 * 26
        for j in range(0, 26):
            y = -0.5 + j * sp
            jOffset = j * 26
            for i in range(0, 26):
                x = -0.5 + i * sp
                s = x * x + y * y + z * z - (0.4 * 0.4)
                offset = i + jOffset + kOffset
                scalars.InsertTuple1(offset, s)
    vol.GetPointData().SetScalars(scalars)

    contour = vtk.vtkContourFilter()
    contour.SetInputData(vol)
    contour.SetValue(0, 0.0)

    volMapper = vtk.vtkPolyDataMapper()
    volMapper.SetInputConnection(contour.GetOutputPort())
    volMapper.ScalarVisibilityOff()
    volActor = vtk.vtkActor()
    volActor.SetMapper(volMapper)
    volActor.GetProperty().EdgeVisibilityOn()
    volActor.GetProperty().SetColor(colors.GetColor3d('Salmon'))
    renderer.AddActor(volActor)
    renderer.SetBackground(colors.GetColor3d('SlateGray'))
    renWin.SetSize(512, 512)
    renWin.SetWindowName('Vol')

    # Interact with the data.
    renWin.Render()

    iren.Start()

if __name__ == '__main__':

    #display_sphere()
    #main()
    sph()