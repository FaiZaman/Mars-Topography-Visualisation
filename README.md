# Mars-Topography-Visualisation

This repository visualises the topography of the planet Mars in an interactive format, using two orthographically projected, equatorial elevation maps of Mars.

## Preprocessing

The `preprocessing.py` file reads the data and performs preprocessing for Problem 1. The output is a pickle file saved in the `/data` folder to a `elevation_map.pkl` file, which contains the height information used for Problems 2 and 3. This program should be run before the height warp and isoline programs, although an existing `elevation_map.pkl` file is provided for convenience.

The file can be run with the following command:

```
$ python preprocessing.py data/elevationData.tif marsTexture.jpg
```

## Height Warp

The `height_warp.py` file applies the texture file to a VTK sphere and renders the warped geometry of Mars based on the height.

The file can be run with the following command:

```
$ python preprocessing.py data/elevationData.tif marsTexture.jpg
```

## Isolines

The `isolines.py` file applies the texture file to a VTK sphere and renders the isolines of Mars for the height range -8 to 14 kilometers.

The file can be run with the following command:

```
$ python isolines.py data/elevationData.tif marsTexture.jpg
```
