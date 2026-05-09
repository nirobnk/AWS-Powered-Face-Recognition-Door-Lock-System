from flask import Flask, jsonify
from camera import capture_frame
from rekognition import search_face
from mqtt_client import publish_command

app = Flask(__name__)


@app.route('/health', methods=['GET'])
def health():
    """Quick check that the server is alive."""
    return jsonify({'status': 'ok'})


@app.route('/check', methods=['POST'])
def check_face():
    """
    Main endpoint — runs the full face recognition pipeline:
      1. Capture frame from webcam
      2. Send to AWS Rekognition
      3. Publish UNLOCK or DENY to MQTT
      4. Return JSON result
    """
    # Step 1: Capture webcam frame
    image_bytes = capture_frame(camera_index=1)
    if image_bytes is None:
        return jsonify({'error': 'Camera capture failed'}), 500

    # Step 2: Send to AWS Rekognition for face matching
    matched, name, confidence = search_face(image_bytes)

    # Step 3: Publish result to MQTT (ESP32 listens here)
    if matched:
        publish_command('UNLOCK')
        print(f"[ACCESS GRANTED] {name} — confidence: {confidence}%")
        return jsonify({
            'access':     'granted',
            'name':       name,
            'confidence': confidence
        })
    else:
        publish_command('DENY')
        print("[ACCESS DENIED] Face not recognised")
        return jsonify({'access': 'denied'})


if __name__ == '__main__':
    print("=" * 45)
    print("  Door Recognition Backend — Starting")
    print("=" * 45)
    print("  Health : GET  http://localhost:5000/health")
    print("  Check  : POST http://localhost:5000/check")
    print("=" * 45)
    app.run(host='0.0.0.0', port=5001, debug=True)