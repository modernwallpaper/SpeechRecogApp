import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from api.speech_recog_api import VoskRecognizer

app = Flask(__name__)
CORS(app)

recognizer = VoskRecognizer()

devices = recognizer.list_input_devices()
if not devices:
    raise RuntimeError("[[ ! ]] No input devices found")

device_index = None

@app.route("/api/list_devices", methods=['GET'])
def return_device_list():
    return devices

@app.route("/api/use_device", methods=['POST'])
def set_device_id():
    global device_index  # make sure to update global
    data = request.get_json()  # parse JSON body
    if not data or 'device_id' not in data:
        return jsonify({"status": "error", "message": "request must include {'device_id': int}"}), 400
     
    device_index = int(data['device_id'])
    return jsonify({"status": "success", "using_device": device_index})


@app.route("/api/load_model", methods=['GET'])
def loadModel():
    global device_index
    if device_index is None:
        return jsonify({"info": "before loading the model you must first select an input device"})
    recognizer.select_device(device_index)
    recognizer.load_model()
    threading.Thread(target=recognizer.start_listening, daemon=True).start()
    return jsonify({"status": "success"})

@app.route("/api/get_latest_text", methods=['GET'])
def getLatestText():
    return jsonify(recognizer.get_latest_text())

@app.route("/api/get_latest_partial_text", methods=['GET'])
def getLatestPartialText():
    return jsonify(recognizer.get_partial_text())

@app.route("/api/stop_listening", methods=['GET'])
def stopListening():
    recognizer.stop_listening()
    return jsonify({"info": "model stopped"})

if __name__ == '__main__':
    app.run(debug=True)
