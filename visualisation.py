import math
import cv2


def visualise(elevation_path):

    # initialise colour map and height dictionaries
    colour_map_dict = {}
    pixel_height_dict = {}

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
                pixel_height_value += pixel_height_change

                if abs(pixel_height_value - int(pixel_height_value)) < pixel_height_change:
                    x += 7

        x += 1

    colour_map_dict[(255, 255, 255)] = 14   # edge case

    # assign
    for y in range(0, height):
        for x in range(0, width):

            # retrieve height for pixel if not black
            pixel = tuple(colour_map_img[y][x])
            if not (pixel[0] == pixel[1] == pixel[2] == 0):

                # get closest RGB pixel if not in dict
                if pixel not in colour_map_dict:
                    pixel = min(colour_map_dict, key=lambda x: difference(x, pixel))

                # assign height to pixel coordinates
                height = colour_map_dict[pixel]
                pixel_height_dict[(y, x)] = height

    return colour_map_dict, pixel_height_dict


# calculate difference between two RGB values
def difference(m, n):

    r1, g1, b1 = m[0], m[1], m[2]
    r2, g2, b2 = n[0], n[1], n[2]
    d = math.sqrt((r2-r1)**2+(g2-g1)**2+(b2-b1)**2)

    return d


path = 'data/elevationData.tif'
colour_map_dict, pixel_height_dict = visualise(path)

for key, value in pixel_height_dict.items():
    print(key, value)
