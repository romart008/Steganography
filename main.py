#       Steganography project
#
# 1. Open photo and get all LSBs
# 2. Get a message and encode it
# 3. Create a matrix for encoding
# 4. Calculate the natural hidden msg
# 5. Change it to the one given
#
# ! Insert some cryptography

from PIL import Image

def open_image(image_path):
    
    img = Image.open(image_path).convert("RGB")     # Opening image as rgb
    pixels = list(img.getdata())                    # Getting all info about pixels as list

    bits = []

    for r, g, b in pixels:
        bits.append([format(r, 'b')[-1], format(g, 'b')[-1], format(b, 'b')[-1]])   # Format all data in binary and get last pixel
        
    return bits



print(open_image("testimage.png"))