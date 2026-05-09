# Face Recognition Door Lock System

An intelligent, cloud-powered biometric access control system that uses facial recognition for secure, contactless door access. Built as part of the Embedded Systems Design (EE6304) course at the Department of Electrical and Electronic Engineering, University of Ruhuna.

## 👥 Team Members

- **Niroshan**
- **Irasha**
- **Oshini**
- **Niluminda**

## 📋 Project Overview

This system combines embedded hardware (ESP32), cloud AI (AWS Rekognition), and IoT protocols (MQTT) to create a keyless door lock that recognizes authorized users by their faces. When a user presses a physical button, the system captures their face, verifies it against a cloud database, and automatically unlocks the door if authorized - all in under 2 seconds.

### Key Features

- ✅ **Contactless Biometric Authentication** - No keys, cards, or PIN codes required
- ✅ **99%+ Recognition Accuracy** - Powered by AWS Rekognition AI
- ✅ **Real-time Response** - Sub-2-second verification and unlock
- ✅ **Web Dashboard** - User enrollment, management, and access logs
- ✅ **MQTT IoT Communication** - Industry-standard messaging protocol
- ✅ **Complete Audit Trail** - Logs all access attempts with timestamps

### System Architecture

```
Physical Button (ESP32) → MQTT → Python Backend → AWS Rekognition
                                         ↓
                                  Webcam Capture
                                         ↓
                            UNLOCK/DENY → ESP32 → Servo Motor
```

### Technologies Used

**Hardware:**
- ESP32-CAM microcontroller
- Servo motor (door lock)
- Push button, LEDs

**Software:**
- Backend: Python, Flask, OpenCV, Boto3
- Firmware: Embedded C++ (Arduino)
- Cloud: AWS Rekognition
- Protocol: MQTT (Mosquitto broker)

---

## 🚀 Setup

### Prerequisites

- Python 3.8+
- AWS account with Rekognition access
- MQTT broker (Mosquitto)
- Webcam

### Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd door-backend
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   
   Create a `.env` file in the project root:

   ```env
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   AWS_REGION=us-east-1
   COLLECTION_ID=door-faces

   MQTT_BROKER=192.168.8.148
   MQTT_PORT=1883
   MQTT_TOPIC=door/command
   ```

4. **Create AWS Rekognition collection:**

   ```bash
   python -c "import boto3; boto3.client('rekognition').create_collection(CollectionId='door-faces')"
   ```

5. **Run the server:**

   ```bash
   # For basic version
   python app.py

   # For web dashboard + physical button support
   python app_button.py
   ```

6. **Access the dashboard:**
   
   Open browser: `http://localhost:5001`

---

## 📡 API Endpoints

### Web Interface
- `GET /` - Main dashboard with live camera feed and controls

### Face Recognition
- `GET /verify` - Capture current frame and verify face
- `POST /check` - Trigger face check (called by physical button or web UI)

### User Management
- `POST /enroll` - Add new authorized user
  ```json
  {
    "name": "John Doe"
  }
  ```
- `GET /users` - List all enrolled users
- `DELETE /users/<name>` - Remove user from system

### Door Control
- `POST /lock` - Manually lock door
- `POST /unlock` - Manually unlock door
  ```json
  {
    "user_id": "John Doe"
  }
  ```

### System
- `GET /health` - Health check endpoint
- `GET /logs` - Retrieve access logs
- `GET /video_feed` - Live video stream (MJPEG)

---

## 🔌 MQTT Communication

### Topics

**Published by Backend:**
- `door/command` - Sends UNLOCK/DENY commands to ESP32

**Subscribed by Backend:**
- `door/trigger` - Receives CHECK_FACE requests from ESP32 button

### Message Format

```json
{
  "command": "UNLOCK",
  "user_id": "John Doe",
  "confidence": 98.5,
  "timestamp": "2026-05-06 12:34:56"
}
```

**Command Types:**
- `UNLOCK` - Authorized user detected
- `DENY` - Unauthorized user or no face detected

---

## 🎯 Usage Flow

### Enrollment Process

1. Open web dashboard (`http://localhost:5001`)
2. Enter user's name in enrollment form
3. Ensure user is facing the camera
4. Click "Capture & Enroll Face"
5. System confirms enrollment with confidence score

### Access Process

**Method 1: Physical Button (Embedded)**
1. User presses physical button on ESP32
2. ESP32 publishes `CHECK_FACE` via MQTT
3. Backend captures webcam frame
4. AWS Rekognition verifies face
5. Backend publishes `UNLOCK` or `DENY` via MQTT
6. ESP32 controls servo motor and LED indicators

**Method 2: Web Dashboard**
1. User faces the camera
2. Click "Check Face & Unlock Door" button
3. Same verification process as above

### System Response

**Authorized User:**
- ✅ Green LED turns ON
- 🔓 Servo rotates 90° (door unlocks)
- ⏱️ Stays unlocked for 5 seconds
- 🔒 Servo returns to 0° (door locks)
- 📝 Access logged with name and timestamp

**Unauthorized User:**
- ❌ Red LED turns ON for 2 seconds
- 🔒 Door remains locked
- 📝 Denial logged with timestamp

---

## 🛠️ Project Structure

```
door-backend/
├── app.py                  # Basic Flask server
├── app_web.py             # Flask server with web dashboard
├── app_button.py          # Flask server with MQTT button support
├── camera.py              # Webcam capture module
├── rekognition.py         # AWS Rekognition integration
├── mqtt_client.py         # MQTT publishing module
├── .env                   # Environment variables (not in repo)
├── requirements.txt       # Python dependencies
└── templates/
    └── index.html         # Web dashboard UI
```

---

## 🔧 ESP32 Firmware

Upload the Arduino code to ESP32-CAM:

**Pin Configuration:**
- GPIO 15 → Push Button (trigger)
- GPIO 13 → Servo Motor (door lock)
- GPIO 2 → Green LED (access granted)
- GPIO 14 → Red LED (access denied)

**Libraries Required:**
- WiFi.h
- PubSubClient.h (MQTT)
- ESP32Servo.h

---

## 🔒 Security Considerations

- AWS credentials stored in `.env` (never committed to Git)
- HTTPS encrypted communication to AWS
- MQTT over local network (use TLS for production)
- Access logs provide complete audit trail
- Confidence threshold (85%) prevents false positives

---

## 📊 System Specifications

| Metric | Value |
|--------|-------|
| Response Time | 1-2 seconds |
| Recognition Accuracy | 99%+ (AWS) |
| Unlock Duration | 5 seconds |
| Confidence Threshold | 85% |
| Max Users | 20 million (AWS limit) |
| Network | WiFi (2.4GHz) |

---

## 🎓 Academic Context

**Course:** EE6304 - Embedded Systems Design  
**Institution:** University of Ruhuna  
**Department:** Electrical and Electronic Engineering  
**Duration:** 4 weeks  
**Year:** 2026

---

## 🤝 Contributing

This is an academic project. For questions or suggestions, please contact the team members.

---

## 📝 License

This project was developed for educational purposes as part of the EE6304 course curriculum.

---

## 🙏 Acknowledgments

- Department of Electrical and Electronic Engineering, University of Ruhuna
- Course instructors for guidance and support
- AWS for providing cloud AI services

---

## 📞 Contact

For technical inquiries about this project, please reach out to any team member via LinkedIn.

---

**Built by Team Niroshan, Irasha, Oshini, and Niluminda**