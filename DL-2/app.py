from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
from rembg import remove
import io
import logging
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_images(content_img, style_img):
    try:
        logger.info("Processing images...")
        
        # Process content image (remove background)
        content = Image.open(content_img).convert("RGBA")
        content.thumbnail((1024, 1024))  # Resize to manageable size
        content = remove(content)  # Remove background
        
        # Process style image (resize to match content)
        style = Image.open(style_img).convert("RGBA")
        style = style.resize(content.size)
        
        # Composite images
        result = Image.alpha_composite(style, content)
        return result.convert("RGB")
    
    except Exception as e:
        logger.error(f"Processing error: {traceback.format_exc()}")
        raise

@app.route('/process', methods=['POST'])
def handle_request():
    try:
        logger.info("Received new request")
        
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400
            
        files = request.files.getlist('files')
        if len(files) != 2:
            return jsonify({"error": "Send exactly 2 images"}), 400

        # Validate files
        for f in files:
            if f.filename == '':
                return jsonify({"error": "Empty file submitted"}), 400
            if not f.content_type.startswith('image/'):
                return jsonify({"error": "Only images allowed"}), 400

        # Process images
        result = process_images(files[0], files[1])
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        result.save(img_bytes, "JPEG", quality=90)
        img_bytes.seek(0)
        
        logger.info("Sending response")
        return send_file(img_bytes, mimetype="image/jpeg")

    except Exception as e:
        logger.error(f"Server error: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
