from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import base64
import asyncio

# Add the emergentintegrations import
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class ImageAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    image_base64: str
    analysis: str
    objects_detected: List[str] = []
    text_found: str = ""
    emotions: List[str] = []
    scene_description: str = ""
    confidence: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ImageAnalysisCreate(BaseModel):
    filename: str
    image_base64: str

class ImageAnalysisResponse(BaseModel):
    id: str
    filename: str
    image_base64: str
    analysis: str
    objects_detected: List[str]
    text_found: str
    emotions: List[str]
    scene_description: str
    confidence: str
    timestamp: datetime

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "AI Image Recognition API is running!"}

@api_router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisCreate):
    try:
        # Get the API key from environment
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="AI service not configured")
        
        # Create a new LlmChat instance for this analysis
        session_id = str(uuid.uuid4())
        chat = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message="""You are an expert image analysis AI. Analyze images comprehensively and provide detailed information in a structured format.

For each image, provide:
1. Overall description of the image
2. List of objects/items you can identify (comma-separated)
3. Any text you can read in the image
4. Emotions or mood conveyed (if people are present)
5. Scene type and context
6. Your confidence level in the analysis

Format your response as:
DESCRIPTION: [detailed description]
OBJECTS: [object1, object2, object3, ...]
TEXT: [any text found or "None detected"]
EMOTIONS: [emotion1, emotion2, ...] 
SCENE: [scene description]
CONFIDENCE: [High/Medium/Low]"""
        ).with_model("openai", "gpt-4o")
        
        # Create image content from base64
        image_content = ImageContent(image_base64=request.image_base64)
        
        # Create user message with image
        user_message = UserMessage(
            text="Please analyze this image comprehensively according to the format specified in your system message.",
            file_contents=[image_content]
        )
        
        # Get AI analysis
        analysis = await chat.send_message(user_message)
        
        # Parse the analysis response
        objects_detected = []
        text_found = ""
        emotions = []
        scene_description = ""
        confidence = ""
        
        # Simple parsing of the structured response
        lines = analysis.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('OBJECTS:'):
                objects_list = line.replace('OBJECTS:', '').strip()
                if objects_list and objects_list != "None detected":
                    objects_detected = [obj.strip() for obj in objects_list.split(',') if obj.strip()]
            elif line.startswith('TEXT:'):
                text_found = line.replace('TEXT:', '').strip()
            elif line.startswith('EMOTIONS:'):
                emotions_list = line.replace('EMOTIONS:', '').strip()
                if emotions_list and emotions_list != "None detected":
                    emotions = [emotion.strip() for emotion in emotions_list.split(',') if emotion.strip()]
            elif line.startswith('SCENE:'):
                scene_description = line.replace('SCENE:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                confidence = line.replace('CONFIDENCE:', '').strip()
        
        # Create analysis result
        analysis_result = ImageAnalysisResult(
            filename=request.filename,
            image_base64=request.image_base64,
            analysis=analysis,
            objects_detected=objects_detected,
            text_found=text_found,
            emotions=emotions,
            scene_description=scene_description,
            confidence=confidence
        )
        
        # Store in database
        await db.image_analyses.insert_one(analysis_result.dict())
        
        return ImageAnalysisResponse(**analysis_result.dict())
        
    except Exception as e:
        logging.error(f"Error analyzing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze image: {str(e)}")

@api_router.get("/analysis-history", response_model=List[ImageAnalysisResponse])
async def get_analysis_history():
    try:
        # Get recent analyses (limit to 50 for performance)
        analyses = await db.image_analyses.find().sort("timestamp", -1).limit(50).to_list(50)
        return [ImageAnalysisResponse(**analysis) for analysis in analyses]
    except Exception as e:
        logging.error(f"Error fetching analysis history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analysis history")

@api_router.get("/analysis/{analysis_id}", response_model=ImageAnalysisResponse)
async def get_analysis(analysis_id: str):
    try:
        analysis = await db.image_analyses.find_one({"id": analysis_id})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return ImageAnalysisResponse(**analysis)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analysis")

@api_router.delete("/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str):
    try:
        result = await db.image_analyses.delete_one({"id": analysis_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return {"message": "Analysis deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete analysis")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()