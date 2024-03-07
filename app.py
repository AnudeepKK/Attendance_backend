from flask import Flask, request, jsonify
from firebase_admin import storage, credentials, firestore
import firebase_admin
import io
from PIL import Image, ImageDraw, ImageFont  # Import Image module from PIL package
import face_recognition
import pickle
import os
from dotenv import load_dotenv



app = Flask(__name__)
load_dotenv()
# Firebase Service Account credentials
import os

# Firebase Service Account credentials
firebase_credentials = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
    "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN")
}

# Initialize Firebase Admin SDK
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'attendencetracker-ca4cd.appspot.com'  
})



def upload_annotated_image(annotated_image_bytes, subject, section, name):
    try:
        # Get a reference to the Firebase Storage bucket
        bucket = storage.bucket()
        url = f'csv1/{subject}/{section}/{name}'
        
        # Upload the annotated image
        blob = bucket.blob(url)
        blob.upload_from_file(annotated_image_bytes, content_type='image/jpeg')

        # Get the URL of the uploaded image
        annotated_image_url = blob.public_url

        return annotated_image_url

    except Exception as e:
        print(f"Error uploading annotated image: {e}")

def extract_subject_and_section(image_url):
    try:
        # Split the image URL by '/'
        parts = image_url.split('/')

        # Extract subject and section from the URL
        subject = parts[-3]
        section = parts[-2]
        name = parts[-1]

        return subject, section, name

    except Exception as e:
        print(f"Error extracting subject and section from image URL: {e}")
        return None, None


def recognize_faces(image_url):
    try:
        # Load the trained model
        with open("face_recognition_model.pkl", "rb") as f:
            known_faces = pickle.load(f)

        # Download the image from Firebase Storage
        image_data = storage.bucket().blob(image_url).download_as_bytes()

        # Load the image
        unknown_image = face_recognition.load_image_file(io.BytesIO(image_data))

        # Find all face locations and face encodings in the image
        face_locations = face_recognition.face_locations(unknown_image)
        face_encodings = face_recognition.face_encodings(unknown_image, face_locations)

        # List to store names of matching persons
        matching_persons = []

        # Loop through each face found in the image
        for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            # Check if the face matches any known faces
            for person_name, person_face_encodings in known_faces.items():
                matches = face_recognition.compare_faces(person_face_encodings, face_encoding, tolerance=0.5)
                if True in matches:
                    # Add the name to the list if a match is found
                    matching_persons.append(person_name)
                    break

        # Annotate the image with rectangles and labels for recognized faces
        annotated_image = Image.fromarray(unknown_image)
        draw = ImageDraw.Draw(annotated_image)
        font = ImageFont.truetype("arial.ttf", 50)
        for (top, right, bottom, left), person_name in zip(face_locations, matching_persons):
            # Draw a rectangle around the face
            draw.rectangle(((left, top), (right, bottom)), outline=(0, 255, 0), width=2)
            # Draw a label with a name below the face
            draw.text((left, bottom + 10), person_name, fill=(0, 0, 255), font=font)
            draw.text((left + 1, bottom + 11), person_name, fill=(0, 0, 255), font=font)

        # Save the annotated image data as bytes
        annotated_image_bytes = io.BytesIO()
        annotated_image.save(annotated_image_bytes, format='JPEG')
        annotated_image_bytes.seek(0)

        return matching_persons, annotated_image_bytes

    except Exception as e:
        # Log an error if there's an issue with the recognition process
        print(f"Error recognizing faces: {e}")


@app.route('/display_image', methods=['POST'])
def display_image():
    try:
        # Get the image URL from the request data
        image_url = request.json.get('image_url')

        # Recognize faces in the image and get annotated image bytes
        matching_persons, annotated_image_bytes = recognize_faces(image_url)

        # Extract subject, section, and name from the image URL
        subject, section, name = extract_subject_and_section(image_url)

        # Upload the annotated image to Firestore Storage
        annotated_image_url = upload_annotated_image(annotated_image_bytes, subject, section, name)

        return jsonify({'matching_persons': matching_persons, 'annotated_image_url': annotated_image_url})

    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)
