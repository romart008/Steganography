#       Steganography project
#
# +. Open photo and get all LSBs
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

    Cover = []
    bits = []

    for r, g, b in pixels:
        temp = [format(r, 'b'), format(g, 'b'), format(b, 'b')]             # Format all data to binary
        Cover.append(temp)   
        bits.append([temp[0][-1], temp[1][-1], temp[2][-1]])                # Get last bites
        
    return Cover, bits


def Message(msg):
    p = len(msg)
    msg_b = ''.join(format(x, 'b') for x in bytearray(msg, 'utf-8'))

    return msg_b, p



Cover, bits = open_image("testimage.png")

msg_b, p = Message("Hello")

print(msg_b)