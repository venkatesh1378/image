from flask import Flask, render_template, request, jsonify
import os
import cv2
import numpy as np
from rembg import remove
from PIL import Image
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['RESULT_FOLDER'] = 'static/results'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_images(content_path, style_path, result_filename):
    # Remove background from content image
    content_image = cv2.imread(content_path)
    output = remove(content_image)
    foreground = output[:, :, :3]
    mask = output[:, :, 3]

    # Process style image
    styled_image = cv2.imread(style_path)
    
    # Resize images to match dimensions
    height, width = foreground.shape[:2]
    styled_image = cv2.resize(styled_image, (width, height))
    
    # Blend images
    mask = mask.astype(np.float32) / 255.0
    mask = np.expand_dims(mask, axis=-1)
    blended = (foreground * mask) + (styled_image * (1 - mask))
    
    # Save result
    result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
    cv2.imwrite(result_path, blended)
    return result_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'content' not in request.files or 'style' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
        
    content_file = request.files['content']
    style_file = request.files['style']
    
    if not (allowed_file(content_file.filename) and allowed_file(style_file.filename)):
        return jsonify({'error': 'Invalid file type'}), 400

    try:
        # Save uploaded files
        content_path = os.path.join(app.config['UPLOAD_FOLDER'], 'content.jpg')
        style_path = os.path.join(app.config['UPLOAD_FOLDER'], 'style.jpg')
        content_file.save(content_path)
        style_file.save(style_path)
        
        # Process images
        result_filename = f'result_{int(time.time())}.jpg'
        result_path = process_images(content_path, style_path, result_filename)
        
        return jsonify({
            'result': f'/static/results/{result_filename}',
            'content': f'/static/uploads/content.jpg',
            'style': f'/static/uploads/style.jpg'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)