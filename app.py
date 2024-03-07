from flask import Flask, request, jsonify
from firebase_admin import storage, credentials, firestore
import firebase_admin
import io
from PIL import Image, ImageDraw, ImageFont  # Import Image module from PIL package
import face_recognition
import pickle


app = Flask(__name__)

# Firebase Service Account credentials
firebase_credentials = {
    "type": "service_account",
    "project_id": "attendencetracker-ca4cd",
    "private_key_id": "dec6910e58689df1ffdbdc4ddfd4bea0460522d8",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCmQgKP1VF5kba0\nSluFS4Gn7e/B5JH9Lzf+P7lQAI7bIXy/PEpYwFSFyvQOmpKQ6NCfkqHoJ/iktO5M\n5gqpSctcfJojzZBH1tKe18S7i3nUQtXn1KS0Ygj4ZAI/Xq0PpUw7lGzcQDfadEeq\nVriJc/TeP0Ov/pBJnNnW1FWiixLLOHAiqsy1f3pHWJAyKYHGaA2IOz8BVYEERscA\nIVQhmYUoSy8AOgTGUL6o0y4hchYcjxmMLDC86uVbYAvwQrPL8eYOcedAo+QSEpFE\nR1Apv3MOZVDqdCA74vwLhDd4TnUvv8Qd5LIk6HDrEASHbI7t8mPBm5OfQxEPq4iO\nMtdg3b6tAgMBAAECggEAMBj1o8W7MdfJSuQeEPRUmI/ZpjapU10nLjsiMbZPna5U\n6AAZpA5UBXa+30CxeRGZVSi3BTIXGRMsw3tjhzENj36Omx/7hwTrXr+eLwF9J76E\nInLeiT65SJ6qFcoed+HCqZPZYGiFoAG2v90husYch3U28EHNXTZuwNshwQnJ0JdW\nXxN93/xnkAYoG0uIV6MLPg70U8+h88acWNNdWKQrGIU1s9gsBHBb4PqBaGZM0Jch\njs1TeLNpNcJ2AgX6aj+TnNgcu5qjZ1b3efFr4H12erCnxix+QsTTqDB2BfsmT9gB\nAuKQJP2/Kq0iKrQ1rkWSfUbER1tgZSWHmLclg7P9EwKBgQDPBQmkQcJD9lUDa2Wf\n2Hw9XYJd6OGweZg2vFvD9qQ/1YFv2tQk2E1D3yDlliFfYra1jn4OKQRYdqXOHQB+\nLm+p4piNN1MWFhtiMf0hLw0foVVzUgzp48lKi4J0xwZb9Znler9Bv59M8JLu/YAD\ndBz3/ZvR5GJZC/16oyASkO4yUwKBgQDNmBJdBHtVPqyv0OPf8TXlZDFZjd7RbyLR\nb2we2SjywpBphPvNHNCXX/JY7Il37ykWCQ0FG7XA77kToVcXgiqV7hQ29D1y4Gwa\nrVw37r/C4UvPbvzM2/3DtvJilS5AOOvz6y5PTOUctVvSq4UR+yE/TdXkQQ50e0I9\nmww0GEgq/wKBgG9lVY/WdrNdXNePNcrykb/vjlP8GV19wKNLbdGf6TgUKidHSDpf\nTgxEh44i3+hU1N4TQ89Y0ObNSWEEiBxd3mY68T2j1Iig8rE/FueBSv2HMdTxBNPi\nZ5E+Sr+NzOU03k/2Ye3+L7kWBuqk6/pvw5rKE8u4qhcidY5FMt/qrtHTAoGAJiWR\nQrESMT7vy692mJao6WctwPAR58o3K6UA6rhgYKq5INsL3YL7MRscXGOHHjnB5dTI\nFaqOjr3sGThWcIY2YJtMJOYsgKQjas+/zKD/86jZ6CMvxNMMwsOvNZt4eXIWVavN\na+lYmXsNDonEpxFxmc1XYoKvq+0y3TtniEL5IQECgYEAlPqBQ11Sctim2B8eRmgC\nknDf6deMDEccQTNsjn3pMjN4vEeLAJIBpEvLTqAkunHn1sGZHLW6dycJXcgEUPPM\n9uvONiX5GV38KL2LPnNhxwKkKtv4xdoj/TE9D9NoxpM/43xZGQz4vdLuaAW1qTdA\ng66T1XZglgVJS5Ku7yq10r0=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-rxtz9@attendencetracker-ca4cd.iam.gserviceaccount.com",
    "client_id": "116628847401113754753",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-rxtz9%40attendencetracker-ca4cd.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
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
    app.run(debug=True)
