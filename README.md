# Door Security System - Backend

Face recognition door lock system using AWS Rekognition, MQTT, and Flask.

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure .env file:**
   - Add your AWS credentials
   - Set MQTT broker details
   - Adjust camera settings

3. **Run the server:**
   ```bash
   python app.py
   ```

## API Endpoints

- `GET /` - Video feed web interface
- `GET /video_feed` - Live video stream
- `GET /verify` - Capture & verify face
- `POST /add_face` - Add new face (body: `{"user_id": "name"}`)
- `POST /lock` - Lock door
- `POST /unlock` - Unlock door (body: `{"user_id": "name"}`)
- `GET /faces` - List all registered faces
- `DELETE /face/<face_id>` - Delete face
- `GET /health` - Health check

## MQTT Commands to ESP32

Published to topic (default: `door/control`):

```json
{
  "command": "UNLOCK|LOCK|DENIED",
  "user_id": "username",
  "timestamp": null
}
```

## Usage Flow

1. Camera captures face
2. Image sent to AWS Rekognition
3. If matched → MQTT sends UNLOCK to ESP32
4. If not matched → MQTT sends DENIED to ESP32
5. Manual lock/unlock via API
