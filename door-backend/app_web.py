from flask import Flask, render_template, request, jsonify, Response
from camera import capture_frame
from rekognition import search_face
from mqtt_client import publish_command
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime
import cv2

load_dotenv()

app = Flask(__name__)

# Store access logs in memory (in production, use a database)
access_logs = []

# AWS Rekognition client
rekognition_client = boto3.client(
    'rekognition',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})

@app.route('/check', methods=['POST'])
def check_face():
    """
    Face recognition endpoint - can be called from web UI or curl
    """
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
        return jsonify({'error': 'Camera capture failed'}), 500

    # Step 2: Send to AWS Rekognition for face matching
    matched, name, confidence = search_face(image_bytes)

    # Step 3: Publish result to MQTT (ESP32 listens here)
    if matched:
        publish_command('UNLOCK')
        print(f"[ACCESS GRANTED] {name} — confidence: {confidence}%")
        
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'access': 'granted',
            'name': name,
            'confidence': confidence,
            'reason': None
        }
        access_logs.insert(0, log_entry)
        
        return jsonify({
            'access': 'granted',
            'name': name,
            'confidence': confidence
        })
    else:
        publish_command('DENY')
        print("[ACCESS DENIED] Face not recognised")
        
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'access': 'denied',
            'name': None,
            'confidence': 0,
            'reason': 'Face not recognized'
        }
        access_logs.insert(0, log_entry)
        
        return jsonify({'access': 'denied'})

@app.route('/enroll', methods=['POST'])
def enroll_user():
    """
    Enroll a new user by capturing their face and adding to AWS Rekognition
    """
    data = request.get_json()
    user_name = data.get('name', '').strip()
    
    if not user_name:
        return jsonify({'error': 'Name is required'}), 400
    
    # Capture face from webcam
    image_bytes = capture_frame()
    if image_bytes is None:
        return jsonify({'error': 'Camera capture failed'}), 500
    
    try:
        # Index face in AWS Rekognition
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
            
            print(f"[ENROLLMENT] {user_name} enrolled successfully (Face ID: {face_id})")
            
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
            
    except rekognition_client.exceptions.InvalidParameterException as e:
        return jsonify({'error': 'No face detected or image quality too low'}), 400
    except Exception as e:
        print(f"[ENROLLMENT ERROR] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/users', methods=['GET'])
def list_users():
    """
    List all enrolled users from AWS Rekognition
    """
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
        print(f"[LIST USERS ERROR] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<name>', methods=['DELETE'])
def delete_user(name):
    """
    Delete a user from AWS Rekognition by name
    """
    try:
        # First, list all faces to find the face_id for this name
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
        
        # Delete the faces
        rekognition_client.delete_faces(
            CollectionId=os.getenv('COLLECTION_ID'),
            FaceIds=face_ids_to_delete
        )
        
        print(f"[USER DELETED] {name} ({len(face_ids_to_delete)} faces)")
        
        return jsonify({
            'success': True,
            'deleted_count': len(face_ids_to_delete)
        })
        
    except Exception as e:
        print(f"[DELETE USER ERROR] {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """
    Get access logs (last 50 entries)
    """
    return jsonify({'logs': access_logs[:50]})

@app.route('/video_feed')
def video_feed():
    """
    Video streaming route for live camera preview
    """
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
    print("=" * 45)
    print("  Door Recognition Backend — Starting")
    print("=" * 45)
    print("  Dashboard : http://localhost:5001")
    print("  Health    : GET  http://localhost:5001/health")
    print("  Check     : POST http://localhost:5001/check")
    print("=" * 45)
    app.run(host='0.0.0.0', port=5001, debug=True)
