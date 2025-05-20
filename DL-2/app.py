
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
from rembg import remove
import io
import logging
import traceback

app = Flask(__name__)
CORS(app, resources={r"/process": {"origins": "*"}})  # Explicit CORS for /process

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/process', methods=['POST', 'OPTIONS'])
def handle_request():
    try:
        logger.debug("Request headers: %s", request.headers)
        
        if request.method == 'OPTIONS':
            return _build_preflight_response()
        
        if 'files' not in request.files:
            logger.error("No files in request")
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        if len(files) != 2:
            logger.error("Incorrect file count: %d", len(files))
            return jsonify({"error": "Send exactly 2 images"}), 400

        # Process images
        content_file, style_file = files
        logger.info("Processing files: %s and %s", content_file.filename, style_file.filename)
        
        # Remove background and composite
        content = remove(Image.open(content_file).convert("RGBA"))
        content.thumbnail((1024, 1024))
        style = Image.open(style_file).convert("RGBA").resize(content.size)
        result = Image.alpha_composite(style, content).convert("RGB")

        # Prepare response
        img_bytes = io.BytesIO()
        result.save(img_bytes, "JPEG", quality=90)
        img_bytes.seek(0)
        
        response = send_file(img_bytes, mimetype="image/jpeg")
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        logger.error("SERVER ERROR: %s", traceback.format_exc())
        return jsonify({"error": str(e)}), 500

def _build_preflight_response():
    response = jsonify({"status": "preflight"})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type")
    response.headers.add("Access-Control-Allow-Methods", "POST")
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
