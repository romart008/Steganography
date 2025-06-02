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

    Cover = []
    bits = []

    for r, g, b in pixels:
        temp = [format(r, 'b'), format(g, 'b'), format(b, 'b')]             # Format all data to binary
        Cover.append(temp)   
        bits.append([temp[0][-1], temp[1][-1], temp[2][-1]])                # Get last bites
        
    return Cover, bits


def Message(msg):
    msg_b = ''.join(format(x, 'b') for x in bytearray(msg, 'utf-8'))        # Переведення повідомлення двійковий код
    p = len(msg_b)

    return msg_b, p, 2**p-1

Matrix = []

def Mat(p, l, n, t):
    global Matrix

    if n == p:
        Matrix.append(t.copy())             # Якщо стовпець з p символів готовий - додаємо його в масив
        return

    t.append(0)
    Mat(p, l, n+1, t)                       # Запускаємо цю ж функцію яка кожен раз додає 0 або 1 поки не буде повний стовпець
    t.pop()

    t.append(1)
    Mat(p, l, n+1, t)
    t.pop()

def transform(bits, Matrix, msg_b):
    color = 0

    nat_msg = np.dot(Matrix.T, [int(sub_array[color])for sub_array in bits[:len(Matrix)]])%2

    print(nat_msg)

Cover, bits = open_image("testimage.png")

msg_b, p, l = Message("Heh")

Mat(p, l, 0, [])
del Matrix[0]

Matrix = np.array(Matrix)

transform(bits, Matrix, msg_b)