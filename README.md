### REQUIREMENTS
Firstly, download the VOSK model you want to use on this website:
```url
https://alphacephei.com/vosk/models
```
Then, go ahead and unzip the downloaded .zip file into the ```models``` folder.
After that, you need to set the ```MODEL_DIR``` variable in ```api/speech_recog_api.py``` to ```BASE_DIR / "models" / "$YOUR_EXTRACTED_MODEL_FOLDER_NAME"```

If you want support for proper punctuation, consider also downloading the punctuation model on the same website:
```url
https://alphacephei.com/vosk/models
```
Then, go ahead and unzip the download .zip file into the ```models``` folder as well.
After that, you need to set the ```PUNCT_MODEL_DIR``` variable in ```api/speech_recog_api.py``` to ```BASE_DIR / "models" / "$YOUR_EXTRACTED_PUNCT_MODEL_FOLDER_NAME"```

You also want to set the ```LANG``` variable in ```api/speech_recog_api.py``` to the downloaded language for the punctuation model. If your main model language doesent support punctuation, then go ahead and disable punctuation. You will see how to do that in the next step.

If you dont want puncation eneabled, set the ```ENABLE_PUNCT``` variable in ```api/speech_recog_api.py``` to ```False```

### Installing npm packages

Now, you can got ahead and install all the required dependiencies, by running:
```bash
npm i
```

### FOR AMD GPU USERS:
remove the lines containing ```torch``` and ```torchvision``` from ```requirements.txt```
Then, go ahead and install the amd versions using this command:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/rocm6.4
```

If you get an error, that ```/opt/amdgpu/share/libdrm/amdgpu.ids``` cannot be found:
```bash
sudo mkdir -p /opt/amdgpu/share/libdrm
```
```bash
sudo ln -s /usr/share/libdrm/amdgpu.ids /opt/amdgpu/share/libdrm/amdgpu.ids
```

### Installing python packages

Now go ahead and run this command
```bash
pip install -r requirements.txt
```

To run the app, paste this command into your terminal:
```bash
npm run start
```

### Potential Errors
If this line throws an error in the ```recasepunc.py``` file, located in your punctuation model directory:
```python
self.model.load_state_dict(loaded['model_state_dict'])
```
Change it to this:
```python
self.model.load_state_dict(loaded['model_state_dict'], strict=False)
```

