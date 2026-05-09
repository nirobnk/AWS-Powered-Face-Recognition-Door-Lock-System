import cv2

print("Scanning for available cameras...\n")

for i in range(10):
    cam = cv2.VideoCapture(i)
    if cam.isOpened():
        ret, frame = cam.read()
        if ret:
            # Get camera info
            width = cam.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cam.get(cv2.CAP_PROP_FRAME_HEIGHT)
            backend = cam.getBackendName()
            print(f"✅ Camera {i}: {width}x{height} - Backend: {backend}")
        cam.release()
    else:
        break

print("\nTo use your MacBook's built-in camera, update camera_index in your .env file")
