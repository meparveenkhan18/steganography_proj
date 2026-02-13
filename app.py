from flask import Flask, render_template, request, send_file
from PIL import Image
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
    
    # Add delimiter to mark end of message
    binary_msg = message_to_binary(message) + '1111111111111110'
    
    # Check if message is too long for the image
    width, height = image.size
    if len(binary_msg) > width * height * 3:
        raise ValueError("Message is too long for this image. Please use a larger image or shorter message.")

    # Create a new image to store the encoded data
    encoded_image = image.copy()
    pixels = encoded_image.load()
    
    index = 0
    data_len = len(binary_msg)
    
    for y in range(height):
        for x in range(width):
            if index < data_len:
                r, g, b = pixels[x, y]
                
                # Encode bits into R, G, B channels
                if index < data_len:
                    r = (r & 254) | int(binary_msg[index])
                    index += 1
                if index < data_len:
                    g = (g & 254) | int(binary_msg[index])
                    index += 1
                if index < data_len:
                    b = (b & 254) | int(binary_msg[index])
                    index += 1
                    
                pixels[x, y] = (r, g, b)
            else:
                break
        if index >= data_len:
            break
    
    # Save the encoded image to a memory buffer instead of disk
    buffer = io.BytesIO()
    encoded_image.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Convert to base64 string to send to template
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return img_str

def decode_image(image_file):
    image = Image.open(image_file).convert('RGB')
    width, height = image.size
    pixels = image.load()
    
    binary_data = ""
    delimiter = "1111111111111110"
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            binary_data += str(r & 1)
            if binary_data.endswith(delimiter):
                break
                
            binary_data += str(g & 1)
            if binary_data.endswith(delimiter):
                break
                
            binary_data += str(b & 1)
            if binary_data.endswith(delimiter):
                break
        
        if delimiter in binary_data:
            break

    if delimiter in binary_data:
        binary_data = binary_data[:binary_data.find(delimiter)]
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