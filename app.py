from flask import Flask, render_template, request, send_file
from PIL import Image
import numpy as np
import io
import base64

app = Flask(__name__)

def message_to_binary(message):
    return ''.join(format(ord(char), '08b') for char in message)

def binary_to_message(binary_data):
    chars = [binary_data[i:i+8] for i in range(0, len(binary_data), 8)]
    # Filter out empty or incomplete bits
    chars = [c for c in chars if len(c) == 8]
    return ''.join(chr(int(char, 2)) for char in chars)

def encode_image(image_file, message):
    # Open image directly from the file upload stream (in-memory)
    image = Image.open(image_file).convert('RGB')
    
    # Resize if too large to prevent serverless timeout/memory issues
    max_size = (1000, 1000)
    image.thumbnail(max_size, Image.Resampling.LANCZOS)
    
    np_img = np.array(image)
    
    # Add delimiter to mark end of message
    binary_msg = message_to_binary(message) + '1111111111111110'
    index = 0
    flat_img = np_img.flatten()
    
    # Check if message is too long for the image
    if len(binary_msg) > len(flat_img):
        raise ValueError("Message is too long for this image. Please use a larger image or shorter message.")

    for i in range(len(flat_img)):
        if index < len(binary_msg):
            # LSB method
            flat_img[i] = (int(flat_img[i]) & 254) | int(binary_msg[index])
            index += 1
        else:
            break

    encoded_img = flat_img.reshape(np_img.shape)
    
    # Save the encoded image to a memory buffer instead of disk
    buffer = io.BytesIO()
    Image.fromarray(encoded_img.astype('uint8')).save(buffer, format="PNG")
    buffer.seek(0)
    
    # Convert to base64 string to send to template
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str

def decode_image(image_file):
    image = Image.open(image_file).convert('RGB')
    np_img = np.array(image)
    flat_img = np_img.flatten()
    
    binary_data = ""
    for pixel_val in flat_img:
        binary_data += str(pixel_val & 1)
        if "1111111111111110" in binary_data:
            break

    if '1111111111111110' in binary_data:
        binary_data = binary_data[:binary_data.find('1111111111111110')]
        return binary_to_message(binary_data)
    else:
        return "No hidden message found or message is corrupted."

@app.route('/', methods=['GET', 'POST'])
def index():
    encoded_image = None
    decoded_message = None
    error_message = None

    if request.method == 'POST':
        try:
            file = request.files.get('image')
            
            if file:
                # Basic validation
                if file.filename == '':
                    error_message = "No selected file"
                else:
                    if 'encode' in request.form:
                        text = request.form.get('secret', '')
                        if not text:
                            error_message = "Please enter a secret message to encode."
                        else:
                            encoded_image = encode_image(file, text)
                    
                    elif 'decode' in request.form:
                        decoded_message = decode_image(file)
            else:
                error_message = "No file part in the request"

        except Exception as e:
            # 500 errors are often silent in serverless, this helps debug
            print(f"Error: {e}") 
            error_message = f"An error occurred: {str(e)}"

    return render_template('index.html', encoded_image=encoded_image, decoded_message=decoded_message, error=error_message)

if __name__ == '__main__':
    app.run(debug=True)