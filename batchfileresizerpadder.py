import os
import cv2 as cv2


input_directory = ''
output_directory = ''
output_ext = "png"
excluded = ['avif']


def get_file_ext(filename):
    # this will return a tuple of root and extension
    split_tup = os.path.splitext(filename)
    file_name = split_tup[0]
    file_extension = split_tup[1]
    return file_extension[1:]


def get_output_filename(filename):
    f_name = os.path.basename(filename)
    new_filename = output_directory + "/" + f_name.replace("."+str(get_file_ext(filename)), "."+output_ext).replace(" ", "_")
    return new_filename


#gets the nearest larger 64, starting with 512
def get_nearest_larger(number):
    nearest_larger = 512
    while nearest_larger < number:
        nearest_larger = nearest_larger + 64
    return nearest_larger


def processFile(filename):
    print("Process image "+filename)
    img = cv2.imread(filename, cv2.IMREAD_COLOR)
    height = img.shape[0]
    width = img.shape[1]
    if height > width:
        preferred_width = 512
        preferred_height = round(preferred_width / width * height)
        pad_bot = get_nearest_larger(preferred_height) - preferred_height
        pad_right = 0
    else:
        preferred_height = 512
        preferred_width = round(preferred_height / height * width)
        pad_bot = 0
        pad_right = get_nearest_larger(preferred_width) - preferred_width

    img_new = cv2.resize(img, (preferred_width, preferred_height))
    img_new_padded = cv2.copyMakeBorder(img_new, 0, pad_bot, 0, pad_right, borderType=cv2.BORDER_CONSTANT, value=0)
    cv2.imwrite(get_output_filename(filename), img_new_padded)
    print("Outputfile: "+get_output_filename(filename))


def processDirectory(dir_name):
    for filename in os.listdir(dir_name):
        f = os.path.join(dir_name, filename)
        # checking if it is a file
        if os.path.isfile(f):
            ext = get_file_ext(f)
            if not ext in excluded:
                processFile(f)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    processDirectory(input_directory)
