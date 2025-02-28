from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
import os
import uvicorn
import requests
import base64
import openai

app = FastAPI()

# Set up MongoDB connection using cloud MongoDB URL from MONGO_URL environment variable
mongo_uri = os.environ.get("MONGO_URL", "mongodb+srv://24bcs12662:kZ3FZIKhcawZBoRl@cluster0.uoz03.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(mongo_uri)
db = client["usersDB"]
users_collection = db["users"]

# Mount static files for frontend (adjust the path to your user folder)
#app.mount("/static", StaticFiles(directory="/home/user/frontend"), name="static")

# File upload endpoint
@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")
    file_location = f"/path/to/save/{file.filename}"
    with open(file_location, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    return JSONResponse(content={"message": "File uploaded successfully"})

# Translation helper
def translation_func(api_key, user_id, input_lang, output_lang, text):
    url_config = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    headers_config = {
        "Content-Type": "application/json",
        "ulcaApiKey": api_key,
        "userID": user_id
    }
    payload_config = {
        "pipelineTasks": [{
            "taskType": "translation",
            "config": {
                "language": {
                    "sourceLanguage": input_lang,
                    "targetLanguage": output_lang
                }
            }
        }],
        "pipelineRequestConfig": {
            "pipelineId": "64392f96daac500b55c543cd"
        }
    }
    response = requests.post(url_config, json=payload_config, headers=headers_config)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error in config: " + response.text)
    response_data = response.json()
    compute_url = response_data['pipelineInferenceAPIEndPoint']['callbackUrl']
    header_name = response_data['pipelineInferenceAPIEndPoint']['inferenceApiKey']['name']
    header_value = response_data['pipelineInferenceAPIEndPoint']['inferenceApiKey']['value']
    payload_serviceID = response_data['pipelineResponseConfig'][0]['config'][0]['serviceId']
    payload_modelId = response_data['pipelineResponseConfig'][0]['config'][0]['modelId']
    headers_compute = { header_name: header_value }
    payload_compute = {
        "pipelineTasks": [{
            "taskType": "translation",
            "config": {
                "language": {"sourceLanguage": input_lang, "targetLanguage": output_lang},
                "serviceId": payload_serviceID,
                "modelId": payload_modelId
            }
        }],
        "inputData": {
            "input": [{"source": text}]
        }
    }
    response_compute = requests.post(compute_url, json=payload_compute, headers=headers_compute)
    if response_compute.status_code != 200:
        raise HTTPException(status_code=response_compute.status_code, detail="Error in compute: " + response_compute.text)
    translated_text = response_compute.json()
    output_text = translated_text['pipelineResponse'][0]['output'][0]['target']
    return output_text

# TTS helper
def tts_func(api_key, user_id, input_lang, gender, text):
    url_config = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    headers_config = {
        "Content-Type": "application/json",
        "ulcaApiKey": api_key,
        "userID": user_id
    }
    payload_config = {
        "pipelineTasks": [{
            "taskType": "tts",
            "config": {"language": {"sourceLanguage": input_lang}}
        }],
        "pipelineRequestConfig": {"pipelineId": "64392f96daac500b55c543cd"}
    }
    response = requests.post(url_config, json=payload_config, headers=headers_config)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error in TTS config: " + response.text)
    response_data = response.json()
    compute_url = response_data['pipelineInferenceAPIEndPoint']['callbackUrl']
    header_name = response_data['pipelineInferenceAPIEndPoint']['inferenceApiKey']['name']
    header_value = response_data['pipelineInferenceAPIEndPoint']['inferenceApiKey']['value']
    payload_serviceID = response_data['pipelineResponseConfig'][0]['config'][0]['serviceId']
    headers_compute = { header_name: header_value }
    payload_compute = {
        "pipelineTasks": [{
            "taskType": "tts",
            "config": {
                "language": {"sourceLanguage": input_lang},
                "serviceId": payload_serviceID,
                "gender": gender
            }
        }],
        "inputData": {
            "input": [{"source": text}]
        }
    }
    response_compute = requests.post(compute_url, json=payload_compute, headers=headers_compute)
    if response_compute.status_code != 200:
        raise HTTPException(status_code=response_compute.status_code, detail="Error in TTS compute: " + response_compute.text)
    response_data = response_compute.json()
    base64_data = response_data['pipelineResponse'][0]['audio'][0]['audioContent']
    return base64_data

# ASR helper
def asr_func(api_key, user_id, input_lang, base64_input, audio_format, sampling_rate):
    url_config = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    headers_config = {
        "Content-Type": "application/json",
        "ulcaApiKey": api_key,
        "userID": user_id
    }
    payload_config = {
        "pipelineTasks": [{
            "taskType": "asr",
            "config": {"language": {"sourceLanguage": input_lang}}
        }],
        "pipelineRequestConfig": {"pipelineId": "64392f96daac500b55c543cd"}
    }
    response = requests.post(url_config, json=payload_config, headers=headers_config)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error in ASR config: " + response.text)
    response_data = response.json()
    compute_url = response_data['pipelineInferenceAPIEndPoint']['callbackUrl']
    header_name = response_data['pipelineInferenceAPIEndPoint']['inferenceApiKey']['name']
    header_value = response_data['pipelineInferenceAPIEndPoint']['inferenceApiKey']['value']
    payload_serviceID = response_data['pipelineResponseConfig'][0]['config'][0]['serviceId']
    headers_compute = { header_name: header_value }
    payload_compute = {
        "pipelineTasks": [{
            "taskType": "asr",
            "config": {
                "language": {"sourceLanguage": input_lang},
                "serviceId": payload_serviceID,
                "audioFormat": audio_format,
                "samplingRate": sampling_rate
            }
        }],
        "inputData": {
            "input": [{}],
            "audio": [{"audioContent": base64_input}]
        }
    }
    response_compute = requests.post(compute_url, json=payload_compute, headers=headers_compute)
    if response_compute.status_code != 200:
        raise HTTPException(status_code=response_compute.status_code, detail="Error in ASR compute: " + response_compute.text)
    asr_data = response_compute.json()
    asr_output = asr_data['pipelineResponse'][0]['output'][0]['source']
    return asr_output

# Set up OpenAI API key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Function to generate crime report using OpenAI
def generate_crime_report(transcription):
    prompt = f"Create a detailed crime report based on the following transcription: {transcription}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500
    )
    report = response.choices[0].text.strip()
    return report

# Translation API endpoint
@app.post("/translation")
def translation_endpoint(payload: dict):
    try:
        api_key    = payload["api_key"]
        user_id    = payload["user_id"]
        input_lang = payload["input_lang"]
        output_lang= payload["output_lang"]
        text       = payload["text"]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {str(e)}")
    result = translation_func(api_key, user_id, input_lang, output_lang, text)
    return {"translated_text": result}

# TTS API endpoint
@app.post("/tts")
def tts_endpoint(payload: dict):
    try:
        api_key    = payload["api_key"]
        user_id    = payload["user_id"]
        input_lang = payload["input_lang"]
        gender     = payload["gender"]
        text       = payload["text"]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {str(e)}")
    audio_base64 = tts_func(api_key, user_id, input_lang, gender, text)
    return {"audio_base64": audio_base64}

# ASR API endpoint
@app.post("/asr")
def asr_endpoint(payload: dict):
    try:
        api_key       = payload["api_key"]
        user_id       = payload["user_id"]
        input_lang    = payload["input_lang"]
        audio_format  = payload["audio_format"]
        sampling_rate = payload["sampling_rate"]
        base64_input  = payload["base64_input"]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {str(e)}")
    transcription = asr_func(api_key, user_id, input_lang, base64_input, audio_format, sampling_rate)
    return {"transcription": transcription}

# Endpoint to handle crime report generation
@app.post("/generate_report")
async def generate_report(payload: dict):
    try:
        api_key       = payload["api_key"]
        user_id       = payload["user_id"]
        input_lang    = payload["input_lang"]
        audio_format  = payload["audio_format"]
        sampling_rate = payload["sampling_rate"]
        base64_input  = payload["base64_input"]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {str(e)}")
    
    # Transcribe the audio
    transcription = asr_func(api_key, user_id, input_lang, base64_input, audio_format, sampling_rate)
    
    # Generate the crime report
    report = generate_crime_report(transcription)
    
    return {"report": report}

# Authentication endpoints
@app.post("/register")
def register(payload: dict):
    try:
        username = payload["username"]
        password = payload["password"]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {str(e)}")
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="User already exists")
    users_collection.insert_one({"username": username, "password": password})
    return {"message": "Registration successful"}

@app.post("/login")
def login(payload: dict):
    try:
        username = payload["username"]
        password = payload["password"]
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing field: {str(e)}")
    user = users_collection.find_one({"username": username, "password": password})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Login successful"}

# Health status endpoints
@app.get("/status")
def status():
    return {"message": "API is running"}

@app.get("/")
def home():
    return {"message": "Welcome to the API with Translation, TTS, and ASR"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3100))
    uvicorn.run(app, host="0.0.0.0", port=port)
