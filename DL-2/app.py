from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import io
import logging
from rembg import remove

app = Flask(__name__)

# Configure CORS properly
CORS(app, resources={
    r"/process": {
        "origins": ["*"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.route('/process', methods=['POST', 'OPTIONS'])
def handle_processing():
    try:
        # Handle OPTIONS preflight
        if request.method == 'OPTIONS':
            return _build_cors_preflight_response()
            
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        if len(files) != 2:
            return jsonify({"error": "Exactly 2 images required"}), 400

        content_file, style_file = files
        result_img = process_images(content_file, style_file)

        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, "JPEG")
        img_byte_arr.seek(0)

        response = send_file(img_byte_arr, mimetype="image/jpeg")
        response = _corsify_actual_response(response)
        return response

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

def _build_cors_preflight_response():
    response = jsonify({"status": "preflight"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST")
    return response

def _corsify_actual_response(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def process_images(content_img, style_img):
    try:
        content_image = Image.open(content_img).convert("RGBA")
        content_image.thumbnail((1024, 1024))
        content_clean = remove(content_image)
        
        style_image = Image.open(style_img).convert("RGBA")
        style_image = style_image.resize(content_clean.size)
        
        composite = Image.alpha_composite(style_image, content_clean)
        return composite.convert("RGB")
    
    except Exception as e:
        logging.error(f"Processing error: {str(e)}")
        raise

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
