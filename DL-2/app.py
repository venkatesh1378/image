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

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        app.logger.info("New request received")
        
        if 'files' not in request.files:
            app.logger.warning("No files part in request")
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        app.logger.info(f"Received {len(files)} files")
        
        if len(files) != 2:
            app.logger.warning(f"Incorrect file count: {len(files)}")
            return jsonify({"error": "Exactly 2 images required"}), 400

        # Verify file content
        for f in files:
            if f.filename == '':
                app.logger.warning("Empty filename detected")
                return jsonify({"error": "Empty file submitted"}), 400
            if not f.content_type.startswith('image/'):
                app.logger.warning(f"Invalid file type: {f.content_type}")
                return jsonify({"error": "Only images allowed"}), 400

        content_file, style_file = files
        app.logger.info(f"Processing files: {content_file.filename} and {style_file.filename}")
        
        result_img = process_images(content_file, style_file)
        app.logger.info("Image processing completed")

        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, "JPEG", quality=90)
        img_byte_arr.seek(0)
        app.logger.info(f"Response size: {len(img_byte_arr.getvalue())} bytes")

        return send_file(img_byte_arr, mimetype="image/jpeg")

    except Exception as e:
        app.logger.error(f"Critical error: {traceback.format_exc()}")
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
