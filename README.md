# Steganography Matrix Embedding

A Python project that hides messages inside images using **matrix embedding**, inspired by Hamming codes. It supports configurable embedding depth (e.g. LSB, 2-LSB...) and is built as an educational and experimental tool for steganography research.

## Features

- Hides binary messages in image pixel data using matrix embedding
- Supports configurable parameter `p` — the number of message bits per block
- Adjustable embedding depth (`depth`) — how many least significant bits are used
- Custom stop marker for automatic extraction
- Pure Python + NumPy
- Great efficency
- GUI planned

## Project Structure

- `open_image(path)` – loads and converts image into modifiable pixel data
- `convert(msg, p)` – splits message into binary blocks of length `p`
- `build_matrix(p)` – generates a matrix used for matrix embedding
- `hide(msg, cover, p, depth)` – hides message into image
- `extract(path, p, depth, stop)` – extracts and decodes hidden message
- `compile(...)` – saves image back to PNG after hiding

## Example Usage

```python
# Encoding
Cover, w, h = open_image("testimage.png")
Message = convert("Secret!" + "&#@", p=4)
hide(Message, Cover, p=4, depth=1)
compile(Cover, w, h)

# Decoding
text = extract("output.png", p=4, depth=1, stop="&#@")
print(text)
```

## Notes
- The message is padded to fit blocks of size p, using zeros if necessary.
- Use a unique stop string (like `&#@`) to automatically terminate extraction.
- Higher depth allows hiding more data per block but increases distortion risk.
- Do not use with JPEG for now (lossy compression will corrupt hidden data).