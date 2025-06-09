# Steganography project
#
# 1. Use root of number to encode a message in specific way
# 2. Add GUI
#
# ! OPTIMIZE

from PIL import Image
import numpy as np

def open_image(image_path):
    img = Image.open(image_path).convert("RGB")  # Opening image as rgb
    pixels = list(img.getdata())                 # Getting all info about pixels as list
    width, height = img.size

    Cover = []

    for r, g, b in pixels:
        t1 = [int(x) for x in format(r, '08b')]
        t2 = [int(x) for x in format(g, '08b')]
        t3 = [int(x) for x in format(b, '08b')]

        Cover.extend([t1, t2, t3])               # Data of the image

    return np.array(Cover), width, height

def convert(msg, p):
    new_msg = []
    res = ''.join(format(ord(i), '08b') for i in msg)
    l = len(res)

    for i in range(l//p):
        new_msg.append(res[i*p:i*p+p])
    #"""
    if l%p != 0:
        new_msg.append(res[(l//p)*p:])
        for i in range(p - len(new_msg[-1])):
            new_msg[-1] += '0'
    #"""
    print(new_msg)
    return new_msg

def build_matrix(p):
    return np.array([
        [int(x) for x in format(i, f'0{p}b')]
        for i in range(1, 2**p)
    ])  # Transpose to get shape (p x 2^p - 1)

def change(Mat, cov_elem, msg, i, d):
    global Cover
    l = 2**p-1

    Mat.shape = (p, l)                                                          # Aligning matrix for correct multiplication
    cov_elem.shape = (l)
    vector = (Mat.dot(cov_elem) - np.array([int(b) for b in msg[i]])) % 2       # Getting the vector
    pos = 0
    for j in Mat.T:
        if np.array_equal(vector, j):
            Cover[i*l+pos][-d] = (Cover[i*l+pos][-d]+1)%2
            break
        pos +=1


def hide(msg, cov, p, depth):
    Mat = build_matrix(p)                             # Creating the matrix
    l = 2**p-1                                      # lengh of Matrix and all possible variations

    
    for i in range(int(len(msg))):                                      
        block = np.array([s[-depth:] for s in cov[i*l:i*l+l]])                  # Creating Cover 

        # !!! This method allows to hide [depth] times more information in one block, than just LSB, 
        # !!! but the risk of discovering message rises exponentionaly
        if depth >1:                                                    # In case we use more than last bit
            for d in range(depth):
                msg_idx = i * depth + d                                 # Iteration, aka how many times we alredy perfomed hiding 
                if msg_idx >= len(msg):
                    break

                cov_elem = np.array([s[-(d + 1)] for s in block])
                change(Mat, cov_elem, msg, msg_idx, d + 1)              

        else:
            change(Mat, block, msg, i, depth)
            

def compile(Cover, width, height):
    new_image = []
    for i in range(int(len(Cover)/3)):                       # Converting back to base 10
        r_bin, g_bin, b_bin = Cover[i*3:i*3+3]
        r = int("".join(map(str, r_bin)), 2)
        g = int("".join(map(str, g_bin)), 2)
        b = int("".join(map(str, b_bin)), 2)
        new_image.append((r, g, b))

    new_img = Image.new("RGB", (width, height))             # Recreating Image
    new_img.putdata(new_image)
    new_img.save("output.png")

def extract(image_path, p, d, stop):
    img = Image.open(image_path).convert("RGB")  # Opening image as rgb
    pixels = list(img.getdata())                 # Getting all info about pixels as list

    Cover = []
    
    Mat = build_matrix(p)

    msg = []
    l = 2**p-1

    for r, g, b in pixels:
        t1 = [int(x) for x in format(r, '08b')]
        t2 = [int(x) for x in format(g, '08b')]
        t3 = [int(x) for x in format(b, '08b')]

        Cover.extend([t1, t2, t3])               # Data of the image
    
    #len(Cover)//l
    for i in range(80):
        block = np.array([s[-d:] for s in Cover[i*l:i*l+l]])
        stop_bits = [int(b) for b in ''.join(format(ord(i), '08b') for i in stop)]
        Mat.shape = (p, l)                                                          # Aligning matrix for correct multiplication
        block.shape = (l,1)
        
        if d > 1:
            continue

        else:
            if len(msg) >= len(stop_bits):
                if msg[-len(stop_bits):] == stop_bits:
                    print("Stop pattern found at", i)
                    break
            temp = (np.dot(Mat, block))%2
            temp = [int(x.item()) for x in temp]
            msg.extend(temp)

    msg = "".join(map(str, msg))
    msg = ''.join(chr(int(msg[i:i+8], 2)) for i in range(0, len(msg), 8))
    return msg

    

# --- Entry Point ---
if __name__ == "__main__":
    n = 1
    depth = 1               # The ammount of last bites taken to change, recommended - 1, aka LSB
    p = 4                   # Ammount of bits we hide per some space
    stop = "&#@"
    if n == 0:
        Cover, width, height = open_image("testimage.png")
        print("Image opened")

        Message = convert("Hello" + stop, p)
        print("Message converted")

        hide(Message, Cover, p, depth)
        print("Message hiden")

        compile(Cover, width, height)
        print("Image Created. Done")
    else:
        print(extract("output.png",p,depth,stop))

        

"""
⠀⠀⠀⠀   ⠀⢀⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀ ⠀ ⠀⠀⢀⣾⣿⡇⠀⠀⠀⠀⠀⢀⣼⡇⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⠀⠀⠀⠀⣴⣿⣿⠇⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣇⠀⠀⢀⣾⣿⣿⣿⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠐⠀⡀
⠀⠀⠀⠀⢰⡿⠉⠀⡜⣿⣿⣿⡿⠿⢿⣿⣿⡃⠀⠀⠂⠄⠀
⠀⠀⠒⠒⠸⣿⣄⡘⣃⣿⣿⡟⢰⠃⠀⢹⣿⡇⠀⠀⠀⠀⠀
⠀⠀⠚⠉⠀⠊⠻⣿⣿⣿⣿⣿⣮⣤⣤⣿⡟⠁⠘⠠⠁⠀⠀
⠀⠀⠀⠀⠀⠠⠀⠀⠈⠙⠛⠛⠛⠛⠛⠁⠀⠒⠤⠀⠀⠀⠀
   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""