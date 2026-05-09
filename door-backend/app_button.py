from flask import Flask, render_template, request, jsonify, Response
from camera import capture_frame
from rekognition import search_face
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime
import cv2
import paho.mqtt.client as mqtt
import threading

load_dotenv()

app = Flask(__name__)

# Store access logs in memory
access_logs = []

# AWS Rekognition client
rekognition_client = boto3.client(
    'rekognition',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

# MQTT Configuration
MQTT_BROKER = os.getenv('MQTT_BROKER', '192.168.8.112')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC_COMMAND = 'door/command'  # Publishes UNLOCK/DENY
MQTT_TOPIC_TRIGGER = 'door/trigger'  # Subscribes to CHECK_FACE requests

mqtt_client = mqtt.Client(client_id="door-backend-button")

def publish_command(command: str):
    """Publish UNLOCK or DENY to ESP32"""
    try:
        # Check if MQTT client is connected
        if not mqtt_client.is_connected():
            print(f"[MQTT] ⚠ Client not connected! Reconnecting...")
            mqtt_client.reconnect()
            import time
            time.sleep(0.5)  # Wait for connection
        
        # Publish with QoS 1 (at least once delivery)
        result = mqtt_client.publish(MQTT_TOPIC_COMMAND, payload=command, qos=1)
        
        if result.rc == 0:
            print(f"[MQTT] ✓ Published: {command} → {MQTT_TOPIC_COMMAND}")
        else:
            print(f"[MQTT] ✗ Publish failed with code: {result.rc}")
            
    except Exception as e:
        print(f"[MQTT] Error publishing: {e}")

def perform_face_check():
    """
    Core face check logic - called by both web UI and physical button
    """
    print("\n" + "="*50)
    print("🎯 FACE CHECK TRIGGERED")
    print("="*50)
    
    # Step 1: Capture webcam frame
    image_bytes = capture_frame()
    if image_bytes is None:
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'access': 'error',
            'name': None,
            'confidence': 0,
            'reason': 'Camera capture failed'
        }
        access_logs.insert(0, log_entry)
        publish_command('DENY')
        print("[ERROR] Camera capture failed")
        return {'error': 'Camera capture failed'}

    # Step 2: Send to AWS Rekognition
    matched, name, confidence = search_face(image_bytes)

    # Step 3: Publish result to MQTT
    if matched:
        publish_command('UNLOCK')
        print(f"[✓ ACCESS GRANTED] {name} — confidence: {confidence}%")
        
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'access': 'granted',
            'name': name,
            'confidence': confidence,
            'reason': None
        }
        access_logs.insert(0, log_entry)
        
        return {
            'access': 'granted',
            'name': name,
            'confidence': confidence
        }
    else:
        publish_command('DENY')
        print("[✗ ACCESS DENIED] Face not recognised")
        
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'access': 'denied',
            'name': None,
            'confidence': 0,
            'reason': 'Face not recognized'
        }
        access_logs.insert(0, log_entry)
        
        return {'access': 'denied'}

def on_mqtt_connect(client, userdata, flags, rc):
    """Called when MQTT connects"""
    if rc == 0:
        print(f"[MQTT] ✓ Connected to broker at {MQTT_BROKER}:{MQTT_PORT}")
        # Subscribe to trigger topic (receives CHECK_FACE from ESP32 button)
        client.subscribe(MQTT_TOPIC_TRIGGER)
        print(f"[MQTT] ✓ Subscribed to: {MQTT_TOPIC_TRIGGER}")
    else:
        print(f"[MQTT] ✗ Connection failed with code {rc}")

def on_mqtt_message(client, userdata, msg):
    """Called when MQTT message received"""
    message = msg.payload.decode('utf-8').strip()
    topic = msg.topic
    
    print(f"\n[MQTT] Message received on {topic}: '{message}'")
    
    # If ESP32 button sends CHECK_FACE request
    if topic == MQTT_TOPIC_TRIGGER and message == "CHECK_FACE":
        print("[MQTT] 🔘 Physical button pressed - triggering face check...")
        perform_face_check()

def start_mqtt_client():
    """Start MQTT client in background thread"""
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message
    
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()  # Non-blocking loop
        print(f"[MQTT] Started background listener")
    except Exception as e:
        print(f"[MQTT] Error starting client: {e}")

# Flask routes (same as before)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/check', methods=['POST'])
def check_face():
    """
    Face check endpoint - called from web UI
    """
    result = perform_face_check()
    if 'error' in result:
        return jsonify(result), 500
    return jsonify(result)

@app.route('/enroll', methods=['POST'])
def enroll_user():
    data = request.get_json()
    user_name = data.get('name', '').strip()
    
    if not user_name:
        return jsonify({'error': 'Name is required'}), 400
    
    image_bytes = capture_frame()
    if image_bytes is None:
        return jsonify({'error': 'Camera capture failed'}), 500
    
    try:
        response = rekognition_client.index_faces(
            CollectionId=os.getenv('COLLECTION_ID'),
            Image={'Bytes': image_bytes},
            ExternalImageId=user_name,
            DetectionAttributes=['DEFAULT'],
            MaxFaces=1,
            QualityFilter='AUTO'
        )
        
        if response['FaceRecords']:
            face_id = response['FaceRecords'][0]['Face']['FaceId']
            confidence = response['FaceRecords'][0]['Face']['Confidence']
            
            print(f"[ENROLLMENT] {user_name} enrolled successfully")
            
            return jsonify({
                'success': True,
                'name': user_name,
                'face_id': face_id,
                'confidence': round(confidence, 1)
            })
        else:
            return jsonify({
                'error': 'No face detected in image. Please ensure face is clearly visible.'
            }), 400
            
    except rekognition_client.exceptions.InvalidParameterException:
        return jsonify({'error': 'No face detected or image quality too low'}), 400
    except Exception as e:
        print(f"[ENROLLMENT ERROR] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/users', methods=['GET'])
def list_users():
    try:
        response = rekognition_client.list_faces(
            CollectionId=os.getenv('COLLECTION_ID'),
            MaxResults=100
        )
        
        users = []
        for face in response.get('Faces', []):
            users.append({
                'name': face['ExternalImageId'],
                'face_id': face['FaceId'],
                'confidence': round(face.get('Confidence', 0), 1)
            })
        
        return jsonify({'users': users})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/users/<name>', methods=['DELETE'])
def delete_user(name):
    try:
        response = rekognition_client.list_faces(
            CollectionId=os.getenv('COLLECTION_ID'),
            MaxResults=100
        )
        
        face_ids_to_delete = []
        for face in response.get('Faces', []):
            if face['ExternalImageId'] == name:
                face_ids_to_delete.append(face['FaceId'])
        
        if not face_ids_to_delete:
            return jsonify({'error': f'User "{name}" not found'}), 404
        
        rekognition_client.delete_faces(
            CollectionId=os.getenv('COLLECTION_ID'),
            FaceIds=face_ids_to_delete
        )
        
        print(f"[USER DELETED] {name}")
        
        return jsonify({
            'success': True,
            'deleted_count': len(face_ids_to_delete)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': access_logs[:50]})

@app.route('/video_feed')
def video_feed():
    from camera import get_camera
    
    def generate():
        camera = get_camera()
        while True:
            if camera is None or not camera.isOpened():
                break
            success, frame = camera.read()
            if not success:
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print("=" * 50)
    print("  Door Recognition Backend — BUTTON MODE")
    print("=" * 50)
    print("  Dashboard : http://localhost:5001")
    print("  MQTT Mode : Physical button triggers face check")
    print("=" * 50)
    
    # Start MQTT client in background
    start_mqtt_client()
    
    # Start Flask web server
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
