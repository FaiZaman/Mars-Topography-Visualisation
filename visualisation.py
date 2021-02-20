import cv2

def visualise(elevation_path):

    # read in image and narrow down to colour map area
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    colour_map_img = img[2200:2550]

    # set dimensions and middle value
    height, width, channels = colour_map_img.shape
    middle = height // 2

    # loop through the middle row
    for x in range(0, width):

        pixel = colour_map_img[middle][x]  # set pixel

        # check if white
        if pixel[0] == pixel[1] == pixel[2] == 255:

            # show the colour map
            print(middle, x)
            cv2.imshow('Elevation', colour_map_img[0:2000, x:3500])
            cv2.waitKey(0)


path = 'data/elevationData.tif'
visualise(path)
