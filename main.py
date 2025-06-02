#       Steganography project
#
# +. Open photo and get all LSBs
# +. Get a message and encode it
# +. Create a matrix for encoding
# 4. Calculate the natural hidden msg
# 5. Change it to the one given
#
# ! Insert some cryptography
# ! OPTIMIZE
# ! 5 GODDAMN MINUTES TO ONE MATRIX

from PIL import Image
import numpy as np

def open_image(image_path):
    
    img = Image.open(image_path).convert("RGB")     # Opening image as rgb
    pixels = list(img.getdata())                    # Getting all info about pixels as list
    width, height = img.size

    Cover = []
    bits = []

    for r, g, b in pixels:
        temp = [[int(x) for x in list(format(r, '08b'))], [int(x) for x in list(format(g, '08b'))], [int(x) for x in list(format(b, '08b'))]]       # Format all data to binary
        Cover.append(temp)   
        bits.append([temp[0][-1], temp[1][-1], temp[2][-1]])                # Get last bites

    Cover = np.array(Cover)
    bits = np.array(bits)
        
    return Cover, bits, width, height


def Message(msg):
    msg_b = ''.join(format(x, '08b') for x in bytearray(msg, 'utf-8'))        # Converting msg to binary
    p = len(msg_b)

    #print(msg_b)

    return msg_b, p, 2**p-1

Matrix = []

def Mat(p, l, n, t):
    global Matrix

    if n == p:
        Matrix.append(t.copy())             # If collumn of p elements ready - Add to Matrix
        return

    t.append(0)
    Mat(p, l, n+1, t)                       # Recursion
    t.pop()

    t.append(1)
    Mat(p, l, n+1, t)
    t.pop()

def transform(bits, Matrix, msg_b, width, height):
    # --- Seeking what pixel to change ---

    global Cover

    color = 0                           # What color to use

    msg_b = np.array([int(x) for x in list(msg_b)])

    

    stego = (Matrix.T.dot([int(sub_array[color])for sub_array in bits[:len(Matrix)]]) - msg_b)%2    # Stego vector

    #stego = "".join(map(str, stego))
    #print(int(stego, 2).to_bytes(len(stego) // 7, 'big').decode())    - showing what character is this 
    
    
    # --- Changing that pixel ---
    one = np.array([0,0,0,0,0,0,0,1])
    pos = 0
    for i in Matrix:
        if np.array_equal(i, stego):
            #print(Cover[pos][color])
            Cover[pos][color] = (Cover[pos][color] +1)%2
            break
        pos +=1


    # --- Reconstructing the image ---
    new_image = []
    for r_bin, g_bin, b_bin in Cover:
        r = int("".join(map(str, r_bin)), 2)
        g = int("".join(map(str, g_bin)), 2)
        b = int("".join(map(str, b_bin)), 2)
        new_image.append((r, g, b))

    new_img = Image.new("RGB", (width, height))
    new_img.putdata(new_image)
    new_img.save("output.png")

def extract(image_path):
    global Matrix

    img = Image.open(image_path).convert("RGB")     # Opening image as rgb
    pixels = list(img.getdata())                    # Getting all info about pixels as list

    bits = []

    for r, g, b in pixels:
        temp = [format(r, '08b'), format(g, '08b'), format(b, '08b')]             # Format all data to binary  
        bits.append([temp[0][-1], temp[1][-1], temp[2][-1]])                # Get last bites

    color = 0
    
    n = 16

    Mat(n, 2**n-1, 0, [])
    del Matrix[0]
    Matrix = np.array(Matrix)

    s = [int(sub_array[color])for sub_array in bits[:len(Matrix)]]
    
    msg = np.dot(Matrix.T, s)%2

    msg = "".join(map(str, msg))
    print("Message is:")
    print(''.join(chr(int(msg[i:i+8], 2)) for i in range(0, len(msg), 8)))



Cover, bits, width, height = open_image("testimage.png")

msg_b, p, l = Message("Hi")

Mat(p, l, 0, [])
del Matrix[0]

Matrix = np.array(Matrix)


if len(Cover) > l:
    transform(bits, Matrix, msg_b, width, height)
else:
    print("Message too big for file")


"""
extract("output.png")
"""