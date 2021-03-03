import cv2

def visualise(elevation_path):

    colour_map_dict = {}    # initialise colour map

    # read in image and narrow down to colour map area
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    colour_map_img = img[2200:2550]

    # set dimensions and middle value
    height, width, channels = colour_map_img.shape
    middle = height // 2

    # initialise values to read in colour map
    recording = False
    pixel_height_value = -8 + 1/115

    """
    10 pixels in initial white bar
    ~115 pixels between bars
    1/115 change per pixel
    """

    # loop through the middle row
    for x in range(0, width):

        pixel = colour_map_img[middle][x]  # set pixel
        print(x, pixel)

        # check if white
        if pixel[0] == pixel[1] == pixel[2] == 255:

            # once the colourmap has been reached, start recording
            recording = True

        else:

            # once recording has started
            if recording:

                # assign the height value for colour of current pixel
                colour_map_dict[tuple(pixel)] = pixel_height_value
                pixel_height_value += 1/115

                if abs(pixel_height_value - int(pixel_height_value)) < 1/115:
                    print(int(pixel_height_value))
                    # set x += 8 somehow
                
            




path = 'data/elevationData.tif'
visualise(path)
