### REQUIREMENTS
Firstly, download the VOSK model you want to use on this website:
```url
https://alphacephei.com/vosk/models
```
Then, go ahead and unzip the downloaded .zip file into the ```models``` folder
After that, you need to set the ```model_path: str``` variable in ```api/speech_recog_api.py``` to ```"models/$YOUR_EXTRACTED_MODEL_FOLDER_NAME"```

Now, you can got ahead and install all the required dependiencies, by running:

```bash
pip install -r requirements.txt
```

```bash
npm i
```

To run the app, paste this command into your terminal:
```bash
npm run start
```
