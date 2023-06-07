import datetime
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import os
import numpy as np
from tensorflow.keras.preprocessing.image import load_img, img_to_array
from tensorflow.keras.models import load_model
import tensorflow.keras as keras
from google.cloud import storage


app = Flask(__name__)
app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])
app.config['UPLOAD_FOLDER'] = 'static/upload/'
model = load_model('model.h5')

def upload_file_to_bucket(bucket_name, local_file_path, destination_blob_name):
    # Instantiates a client
    storage_client = storage.Client()

    # Gets the bucket
    bucket = storage_client.get_bucket(bucket_name)

    # Uploads a local file to the bucket
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(local_file_path)

    print(f"File {local_file_path} uploaded to {bucket_name}/{destination_blob_name}.")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

@app.route("/")
def root():
    return jsonify({
        "status": {
            "code": 200,
            "message": "Success fetching the API!"
        }
    }), 200

@app.route("/predict", methods=["POST"])
def predict():
    if request.method == "POST":
        image = request.files["image"]
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            
            image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            
            img_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            
            
            img = load_img(img_path, target_size=(224,224)) # Resize the image to the size expected by the model
            img = img_to_array(img)
            img = np.expand_dims(img, axis=0) # Add an extra dimension to match the input shape of the model
            model = keras.models.load_model('model.h5')
            class_names = ['bopeng', 'jerawat pasir', 'cystic', 'papula', 'pustula']
            class_ids = ['bopeng','jpasir','jcystic', 'jpapula', 'jpustula']
            class_bgs = ['#96B9CD', '#F1AEB7', '#F2A2AB', '#F5BBAF', '#C2DADC']
            prediction = model.predict(img)
            highest_prob_indices = np.argsort(prediction[0])[::-1][:3]  # Get the indices of the three highest probabilities
            predicted_classes = [class_names[i] for i in highest_prob_indices]
            percentages = prediction[0][highest_prob_indices] * 100
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            bucket_name = 'scancare-db'
            local_file_path = "static/upload/"+filename
            destination_blob_name = "upload/" + timestamp + filename

            upload_file_to_bucket(bucket_name, local_file_path, destination_blob_name)

            result = []

            for i in range(3):
                class_name = predicted_classes[i]
                percentage = percentages[i]
                class_bg = class_bgs[class_names.index(class_name)]
                class_id = class_ids[class_names.index(class_name)]
                
                result.append({
                    "id": class_id,
                    "name": f"{class_name.title()}",
                    "percentage": f"{percentage:.0f}%",
                    "bg_color": class_bg,
                })

            return jsonify(result), 200




        else:
            return jsonify({
                "status": {
                    "code": 400,    
                    "message": "Please upload an image!"
                }
            }), 400
    else:
        return jsonify({
            "status": {
                "code": 403,
                "message": "USE POST!"
            }
        }), 403

@app.errorhandler(400)
def bad_request(error):
    return {
        "status": {
            "code": 400,
            "message": "Client side error!"
        }
    }, 400


@app.errorhandler(404)
def not_found(error):
    return {
        "status": {
            "code": 404,
            "message": "URL Not Found!"
        }
    }, 404


@app.errorhandler(405)
def method_not_allowed(error):
    return {
        "status": {
            "code": 405,
            "message": "Request method not allowed!"
        }
    }, 405


@app.errorhandler(500)
def internal_server_error(error):
    return {
        "status": {
            "code": 500,
            "message": "Server error!"
        }
    }, 500

if __name__ == "__main__":
    app.run()