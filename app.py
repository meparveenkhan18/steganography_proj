from flask import Flask, render_template, request, send_from_directory
from PIL import Image
import numpy as np
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/'

# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def message_to_binary(message):
    return ''.join(format(ord(char), '08b') for char in message)

def binary_to_message(binary_data):
    chars = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    # Filter out empty or incomplete bits to prevent errors
    chars = [c for c in chars if len(c) == 8]
    return ''.join(chr(int(char, 2)) for char in chars)

def encode_image(image_path, message):
    image = Image.open(image_path).convert('RGB')
    np_img = np.array(image)
    binary_msg = message_to_binary(message) + '1111111111111110'
    index = 0

    # Flatten the image to 1D to avoid deep nested loop issues and speed up the process
    flat_img = np_img.flatten()

    for i in range(len(flat_img)):
        if index < len(binary_msg):
            # FIX: Use int() to avoid uint8 overflow and bitmask 254 to clear the last bit
            flat_img[i] = (int(flat_img[i]) & 254) | int(binary_msg[index])
            index += 1
        else:
            break

    # Reshape back to image format
    encoded_img = flat_img.reshape(np_img.shape)
    encoded_filename = "encoded.png"
    encoded_path = os.path.join(app.config['UPLOAD_FOLDER'], encoded_filename)
    
    # Save as PNG (must be PNG to avoid compression ruining the data)
    Image.fromarray(encoded_img.astype('uint8')).save(encoded_path)
    return encoded_filename

def decode_image(image_path):
    image = Image.open(image_path).convert('RGB')
    np_img = np.array(image)
    flat_img = np_img.flatten()
    
    binary_data = ""
    for pixel_val in flat_img:
        binary_data += str(pixel_val & 1)
        # Check if the delimiter is in the string to stop early
        if "1111111111111110" in binary_data:
            break

    binary_data = binary_data[:binary_data.find('1111111111111110')]
    return binary_to_message(binary_data)

@app.route('/', methods=['GET', 'POST'])
def index():
    encoded = None
    decoded = None

    if request.method == 'POST':
        file = request.files['image']
        if file:
            path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(path)

            if 'encode' in request.form:
                text = request.form['secret']
                encoded = encode_image(path, text)

            if 'decode' in request.form:
                decoded = decode_image(path)

    return render_template('index.html', encoded=encoded, decoded=decoded)

# NEW: Route to handle the actual downloading of the file
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)