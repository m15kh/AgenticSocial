from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from scripts.src.utils.queue_manager import add_to_queue, get_queue, get_pending_requests
from scripts.src.config.loader import load_config

# Create FastAPI app
app = FastAPI(
    title="Social Media Bot - Queued Mode",
    description="Queue unlimited requests, process all daily",
    version="1.0.0"
)

config = load_config()


class PredictRequest(BaseModel):
    """Request model for URL processing"""
    url: str
    platforms: Optional[Dict[str, bool]] = None


class EnhanceRequest(BaseModel):
    """Request model for text enhancement"""
    text: str
    platforms: Optional[Dict[str, bool]] = None
    image_path: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with API info"""
    pending_count = len(get_pending_requests())
    scheduled_time = config.get('scheduler', {}).get('time', '23:00')
    
    return {
        "service": "Social Media Bot - Queued Mode",
        "version": "1.0.0",
        "description": f"Unlimited queue, ALL processed daily at {scheduled_time}",
        "queue_size": pending_count,
        "scheduled_time": scheduled_time,
        "mode": "Process ALL at scheduled time",
        "endpoints": {
            "POST /predict": "Add URL to queue",
            "POST /enhance": "Add text enhancement to queue",
            "GET /queue": "View current queue",
            "GET /queue/status": "Get queue status",
            "POST /process/all": "Process all requests now"
        }
    }


@app.post("/predict")
async def predict(request: PredictRequest):
    """Add URL processing request to queue"""
    
    request_data = {
        "url": request.url,
        "platforms": request.platforms or {}
    }
    
    result = add_to_queue(request_data)
    return result


@app.post("/enhance")
async def enhance(request: EnhanceRequest):
    """Add text enhancement request to queue"""
    
    request_data = {
        "text": request.text,
        "platforms": request.platforms or {},
        "image_path": request.image_path
    }
    
    result = add_to_queue(request_data)
    return result


@app.get("/queue")
async def view_queue():
    """View current queue"""
    queue = get_queue()
    scheduled_time = config.get('scheduler', {}).get('time', '23:00')
    
    return {
        "queue_size": len(queue),
        "items": queue,
        "scheduled_time": scheduled_time,
        "mode": "All requests will be processed at scheduled time"
    }


@app.get("/queue/status")
async def queue_status():
    """Get queue status"""
    queue = get_queue()
    pending = get_pending_requests()
    scheduled_time = config.get('scheduler', {}).get('time', '23:00')
    
    return {
        "total": len(queue),
        "pending": len(pending),
        "next_processing": scheduled_time,
        "mode": "process_all"
    }


@app.post("/process/all")
async def trigger_process_all():
    """Trigger processing of all requests immediately"""
    from scripts.src.scheduler.processor import process_all_queue
    result = process_all_queue()
    return result


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "queued_unlimited",
        "scheduled_time": config.get('scheduler', {}).get('time', '23:00')
    }


if __name__ == '__main__':
    import uvicorn
    
    scheduled_time = config.get('scheduler', {}).get('time', '23:00')
    
    print("=" * 60)
    print("🚀 Starting Social Media Bot Server (QUEUED MODE)")
    print("=" * 60)
    print()
    print("📝 UNLIMITED queue - add as many requests as you want")
    print(f"⏰ ALL requests processed daily at {scheduled_time}")
    print()
    print("Endpoints:")
    print("  POST /predict       - Add URL to queue")
    print("  POST /enhance       - Add text enhancement to queue")
    print("  GET  /queue         - View current queue")
    print("  GET  /queue/status  - Get queue status")
    print("  POST /process/all   - Process all NOW")
    print("  GET  /health        - Health check")
    print()
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")