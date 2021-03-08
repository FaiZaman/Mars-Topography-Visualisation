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

        pixel = colour_map_img[middle][x]  # set pixel

        # check if white
        if pixel[0] == pixel[1] == pixel[2] == 255:

            # once the colourmap has been reached start recording
            recording = True

        else:

            # once recording has started
            if recording:

                # break if we go out of bounds
                if pixel[0] == pixel[1] == pixel[2] == 0:
                    break

                # assign the height value for colour of current pixel
                colour_map_dict[tuple(pixel)] = pixel_height_value
                print(pixel, pixel_height_value)
                pixel_height_value += pixel_height_change

                if abs(pixel_height_value - int(pixel_height_value)) < pixel_height_change:
                    x += 7

        x += 1

    return colour_map_dict            




path = 'data/elevationData.tif'
colour_map_dict = visualise(path)

#for key, value in colour_map_dict.items():
#    print(key, value)
