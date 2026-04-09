import datetime 
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
import json
import random
import sys
import os

# ✅ NEW GEMINI SDK
from google import genai

# ✅ CORRECT API KEY NAME
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))



# Add current directory to path to allow absolute imports when running as a script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from ml.inference import Predictor
except ImportError:
    # Fallback for different execution contexts
    from .ml.inference import Predictor

app = FastAPI(title="NeuroShield API", description="AI Backend for Seizure Prediction")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML
predictor = Predictor()

# Load Medical Terms
base_dir = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(base_dir, "medical_terms.json"), "r") as f:
        medical_terms = json.load(f)
except FileNotFoundError:
    print("WARNING: medical_terms.json not found")
    medical_terms = {}
except json.JSONDecodeError:
    print("WARNING: medical_terms.json is not valid JSON")
    medical_terms = {}

# Models
class ChatRequest(BaseModel):
    query: str
    context: Optional[str] = None # Detailed context from the current report

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str # 'admin' or 'user'

@app.post("/login")
async def login(request: LoginRequest):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if request.username == "admin" and request.password == "admin123" and request.role == "admin":
        print(f"[AUTH] Admin login successful: {request.username} at {current_time}")
        return {
            "status": "success", 
            "user": {
                "name": "Administrator", 
                "role": "admin",
                "loginTime": current_time
            }
        }
    elif request.username == "user" and request.password == "user123" and request.role == "user":
        print(f"[AUTH] User login successful: {request.username} at {current_time}")
        return {
            "status": "success", 
            "user": {
                "name": "EEG Technician", 
                "role": "user",
                "loginTime": current_time
            }
        }
    else:
        print(f"[AUTH] Login FAILED: {request.username} (Role: {request.role}) at {current_time}")
        raise HTTPException(status_code=401, detail="Invalid credentials for the selected role.")

@app.post("/analyze/csv")
async def analyze_csv(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")
    
    try:
        # Read with no header initially to check content
        df = pd.read_csv(file.file, header=None)
        
        # Robust signal extraction:
        # 1. Check if it's wide format (many columns) or long format (many rows, few columns)
        
        # Read a few rows to determine format
        file.file.seek(0)
        df_peek = pd.read_csv(file.file, nrows=5)
        
        if df_peek.shape[1] >= 178:
            # Wide format (Original/Synthetic)
            file.file.seek(0)
            df = pd.read_csv(file.file)
            # Find first numeric row and take first 178 numeric columns
            signal_data = df.select_dtypes(include=[np.number]).iloc[0].values[:178].astype(float)
        else:
            # Long format (Raw recordings: time, channel_1)
            file.file.seek(0)
            df = pd.read_csv(file.file)
            
            # Find a column that looks like signal (usually the second column or named channel_*)
            signal_col = None
            for col in df.columns:
                if 'channel' in col.lower() or 'signal' in col.lower() or 'val' in col.lower():
                    signal_col = col
                    break
            
            if signal_col is None:
                # Fallback: find first numeric column that isn't 'time' or 'id'
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if 'time' not in col.lower() and 'id' not in col.lower():
                        signal_col = col
                        break
            
            if signal_col is None and not df.select_dtypes(include=[np.number]).empty:
                 signal_col = df.select_dtypes(include=[np.number]).columns[0]

            if signal_col:
                signal_data = df[signal_col].values[:178].astype(float)
            else:
                raise HTTPException(status_code=400, detail="Could not find numeric signal column in CSV.")

        if len(signal_data) < 178:
             raise HTTPException(status_code=400, detail=f"Insufficient data points. Need 178, found {len(signal_data)}")
             
        prediction = predictor.predict_csv(signal_data)
        
        print(f"[ANALYSIS] CSV Processed: {file.filename}")
        print(f" > Result: {prediction.get('label')} (Risk: {prediction.get('risk_score'):.2f}%)")
        
        return {
            "filename": file.filename,
            "prediction": prediction,
            "raw_signal": signal_data.tolist(),
            "message": "Analysis complete."
        }
            
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing CSV: {str(e)}")

@app.post("/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    try:
        contents = await file.read()
        prediction = predictor.predict_image(contents)
        
        print(f"[ANALYSIS] Image Processed: {file.filename}")
        print(f" > Result: {prediction.get('label')} (Risk: {prediction.get('risk_score'):.2f}%)")
        
        return {
            "filename": file.filename,
            "prediction": prediction,
            "raw_signal": prediction.get("raw_signal", []),
            "message": "Image Analysis complete."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/health")
async def health_check():
    lstm_status = "Online" if predictor.lstm_model else "Offline"
    rf_status = "Online" if predictor.rf_model else "Offline"
    cnn_status = "Online" if predictor.cnn_model else "Offline"
    
    # Get absolute paths for diagnostics
    base_dir = os.path.dirname(os.path.abspath(__file__))
    rf_path = os.path.join(base_dir, "ml", "models", "rf_model.pkl")
    
    return {
        "status": "Running",
        "models": {
            "lstm": lstm_status,
            "random_forest": rf_status,
            "cnn": cnn_status
        },
        "diagnostics": {
            "cwd": os.getcwd(),
            "base_dir": base_dir,
            "rf_model_expected_path": rf_path,
            "rf_model_exists": os.path.exists(rf_path)
        }
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    query = request.query.lower()
    response = ""
    
    greetings = ["Hello!", "Greetings.", "Hi there!", "Welcome back.", "Hello. I'm ready to assist."]
    support_phrases = ["I'm here to help you understand this data.", "Let me look into that for you.", "Great question.", "I'm analyzing the clinical patterns now."]
    
    # Greeting
    if any(greet in query for greet in ["hello", "hi", "hey", "good morning", "good evening"]):
        response += f"{random.choice(greetings)} I am the NeuroShield AI Assistant. {random.choice(support_phrases)}\n\n"

    # Medical terms
    found_terms = []
    for term, definition in medical_terms.items():
        if term in query:
            found_terms.append(f"**{term.capitalize()}**: {definition}")
            
    if found_terms:
        response += "From the medical terms in your query:\n" + "\n\n".join(found_terms) + "\n\n"
            
    # Context analysis
    if any(word in query for word in ["risk", "status", "result", "report", "analyze", "explain"]):
        if request.context:
            try:
                ctx = json.loads(request.context)
                
                label = ctx.get('label', 'Unknown')
                risk = ctx.get('risk_score', 0)

                response += f"Report shows **{label}** with risk **{risk:.1f}%**.\n\n"
            except:
                response += f"Report: {request.context}\n\n"
        else:
            response += "Please upload EEG data for analysis.\n\n"
    
    # 🔥 SINGLE GEMINI CALL
    try:
        print("🔥 Gemini called")

        prompt = f"""
        You are a medical AI assistant.

        User Query:
        {request.query}

        Current Response:
        {response}

        Provide:
        - Clear explanation
        - Remedies if needed
        """

        ai_response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )

        if ai_response.text:
            response = ai_response.text

    except Exception as e:
        print("❌ Gemini Error:", e)
        response += "\n\n(AI unavailable, basic response shown)"

    print(f"[CHAT] {query}")
    print("API KEY:", os.getenv("GEMINI_API_KEY"))
    return {"answer": response.strip()}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)