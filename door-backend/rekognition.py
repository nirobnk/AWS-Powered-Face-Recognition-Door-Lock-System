import boto3
import os
from dotenv import load_dotenv

load_dotenv()

client = boto3.client(
    'rekognition',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)


def search_face(image_bytes, threshold=85):
    """
    Searches for a matching face in the Rekognition collection.
    Returns: (matched: bool, name: str|None, confidence: float)
    """
    try:
        response = client.search_faces_by_image(
            CollectionId=os.getenv('COLLECTION_ID'),
            Image={'Bytes': image_bytes},
            FaceMatchThreshold=threshold,
            MaxFaces=1
        )
        
        # Check if face was detected
        detected_faces = response.get('SearchedFaceConfidence')
        if detected_faces:
            print(f"[Rekognition] Face detected with {detected_faces}% confidence")
        
        matches = response.get('FaceMatches', [])
        if matches:
            name = matches[0]['Face']['ExternalImageId']
            confidence = matches[0]['Similarity']
            print(f"[Rekognition] ✓ Match found: {name} ({confidence:.1f}%)")
            return True, name, round(confidence, 1)
        
        print(f"[Rekognition] ✗ No match found (threshold: {threshold}%)")
        return False, None, 0.0

    except client.exceptions.InvalidParameterException as e:
        # No face detected in the photo
        print(f"[Rekognition] No face detected in image: {e}")
        return False, None, 0.0

    except Exception as e:
        print(f"[Rekognition] Error: {e}")
        return False, None, 0.0