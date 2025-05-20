from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
from rembg import remove
import io
import logging
import traceback

app = Flask(__name__)
CORS(app, resources={r"/process": {"origins": "*"}})

# Configure server settings
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit
app.config['UPLOAD_TIMEOUT'] = 300  # 5 minutes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/process', methods=['POST', 'OPTIONS'])
def handle_request():
    try:
        logger.info("New request received from IP: %s", request.remote_addr)
        
        # Handle OPTIONS preflight
        if request.method == 'OPTIONS':
            response = jsonify({'status': 'ok'})
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            return response

        # Validate request content type
        if not request.content_type.startswith('multipart/form-data'):
            logger.error("Invalid content type: %s", request.content_type)
            return jsonify({"error": "Only form-data accepted"}), 400

        # Check files existence
        if 'files' not in request.files:
            logger.error("No files part in request")
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        if len(files) != 2:
            logger.error("Invalid file count: %d", len(files))
            return jsonify({"error": "Exactly 2 images required"}), 400

        # Validate file sizes
        for f in files:
            f.stream.seek(0, 2)  # Seek to end
            file_size = f.stream.tell()
            f.stream.seek(0)  # Reset cursor
            if file_size > 8 * 1024 * 1024:  # 8MB per file
                logger.error("File %s too large: %d bytes", f.filename, file_size)
                return jsonify({"error": "Max file size 8MB"}), 413

        # Process files
        content_file, style_file = files
        logger.info("Processing files: %s (%s) and %s (%s)", 
                   content_file.filename, content_file.content_type,
                   style_file.filename, style_file.content_type)

        # Image processing
        content = remove(Image.open(content_file).convert("RGBA"))
        content.thumbnail((1024, 1024))
        style = Image.open(style_file).convert("RGBA").resize(content.size)
        result = Image.alpha_composite(style, content).convert("RGB")

        # Prepare response
        img_bytes = io.BytesIO()
        result.save(img_bytes, "JPEG", quality=85)
        img_bytes.seek(0)

        logger.info("Successfully processed request")
        return send_file(img_bytes, mimetype="image/jpeg")

    except Exception as e:
        logger.error("Server Error: %s", traceback.format_exc())
        return jsonify({"error": "Processing failed", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
