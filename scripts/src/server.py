import sys
from pathlib import Path

# Add the project root directory to Python's path
project_root = Path(__file__).parents[3]
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

from config.loader import load_config
from utils.logger import setup_logger, log_success, log_info
from api.social_api import SocialSummarizerAPI, EnhancementAPI

logger = setup_logger('Server')

# Create FastAPI app
app = FastAPI(title="AgenticSocial API")

# Initialize APIs
config = load_config()
social_api = SocialSummarizerAPI()
enhance_api = EnhancementAPI()

# Setup APIs (call setup method)
social_api.setup(device=None)
enhance_api.setup(device=None)


@app.post("/predict")
async def predict(request: Request):
    """URL summarization and posting endpoint"""
    try:
        data = await request.json()
        
        # Decode request
        url = social_api.decode_request(data)
        
        # Process
        result = social_api.predict(url)
        
        # Encode response
        response = social_api.encode_response(result)
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error in /predict: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )


@app.post("/enhance")
async def enhance(request: Request):
    """Text enhancement endpoint"""
    try:
        data = await request.json()
        
        # Decode request
        text = enhance_api.decode_request(data)
        
        # Process
        result = enhance_api.predict(text)
        
        # Encode response
        response = enhance_api.encode_response(result)
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error in /enhance: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "AgenticSocial API",
        "endpoints": {
            "/predict": "POST - Summarize URL and post to Telegram",
            "/enhance": "POST - Enhance text with AI",
            "/health": "GET - Health check",
            "/docs": "GET - API documentation"
        }
    }


def main():
    """Start the server"""
    log_success(logger, f"Starting server on {config['server']['host']}:{config['server']['port']}")
    log_info(logger, "Endpoints:")
    log_info(logger, "  POST /predict - URL processing")
    log_info(logger, "  POST /enhance - Text enhancement")
    log_info(logger, "  GET  /docs - API documentation")
    
    uvicorn.run(
        app,
        host=config['server']['host'],
        port=config['server']['port'],
        log_level="info"
    )


if __name__ == "__main__":
    main()