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