# Steganography project
#
# 1. Use every bit of file
# 2. Use root of number to encode a message in specific way
#
# ! OPTIMIZE

from PIL import Image
import numpy as np

Matrix = []


def open_image(image_path):
    img = Image.open(image_path).convert("RGB")  # Opening image as rgb
    pixels = list(img.getdata())                 # Getting all info about pixels as list
    width, height = img.size

    Cover = []
    bits = []

    for r, g, b in pixels:
        t1 = [int(x) for x in format(r, '08b')]
        t2 = [int(x) for x in format(g, '08b')]
        t3 = [int(x) for x in format(b, '08b')]

        Cover.extend([t1, t2, t3])               # Data of the image
        bits.extend([t1[-1], t2[-1], t3[-1]])     # Last bits

    return np.array(Cover), np.array(bits), width, height


def Message(msg):
    msg_b = ''.join(format(x, '08b') for x in bytearray(msg, 'utf-8'))  # Converting msg to binary
    p = len(msg_b)
    return msg_b, p, 2**p - 1  # 2**p - 1 - length of matrix for hiding


def Mat(p, l, n, t):
    global Matrix

    if n == p:
        Matrix.append(t.copy())  # If column of p elements ready - Add to Matrix
        return

    t.append(0)
    Mat(p, l, n + 1, t)  # Recursion
    t.pop()

    t.append(1)
    Mat(p, l, n + 1, t)
    t.pop()


def transform(bits, Matrix, msg_b, width, height):
    global Cover

    msg_b = np.array([int(x) for x in msg_b])  # Converting to numpy

    stego = (Matrix.T.dot([int(b) for b in bits[:len(Matrix)]]) - msg_b) % 2  # Stego vector

    # --- Changing that pixel ---
    for pos, i in enumerate(Matrix):
        if np.array_equal(i, stego):
            Cover[pos] = (Cover[pos] + 1) % 2
            break

    # --- Reconstructing the image ---
    new_image = []
    for i in range(len(Cover) // 3):  # Converting back to base 10
        r_bin, g_bin, b_bin = Cover[i * 3:i * 3 + 3]
        r = int("".join(map(str, r_bin)), 2)
        g = int("".join(map(str, g_bin)), 2)
        b = int("".join(map(str, b_bin)), 2)
        new_image.append((r, g, b))

    new_img = Image.new("RGB", (width, height))  # Recreating Image
    new_img.putdata(new_image)
    new_img.save("output.png")


def extract(image_path):
    global Matrix

    img = Image.open(image_path).convert("RGB")  # Opening image as rgb
    pixels = list(img.getdata())                 # Getting all info about pixels as list

    bits = []
    for r, g, b in pixels:
        t1 = [int(x) for x in format(r, '08b')]
        t2 = [int(x) for x in format(g, '08b')]
        t3 = [int(x) for x in format(b, '08b')]
        bits.extend([t1[-1], t2[-1], t3[-1]])  # Last bits

    n = 16
    Mat(n, 2**n - 1, 0, [])
    del Matrix[0]
    Matrix = np.array(Matrix)

    s = [int(b) for b in bits[:len(Matrix)]]
    msg = np.dot(Matrix.T, s) % 2

    msg = "".join(map(str, msg))
    print("Message is:")
    print(''.join(chr(int(msg[i:i + 8], 2)) for i in range(0, len(msg), 8)))


# --- Entry Point ---
if __name__ == "__main__":
    n = 0
    if n == 0:
        Cover, bits, width, height = open_image("testimage.png")
        msg_b, p, l = Message("Hi")

        Mat(p, l, 0, [])
        del Matrix[0]
        Matrix = np.array(Matrix)

        if len(Cover) > l:
            transform(bits, Matrix, msg_b, width, height)
        else:
            print("Message too big for file")
    else:
        extract("output.png")

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