import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

QUEUE_FILE = "/home/ubuntu7/m15kh/own/AgenticSocial/data/request_queue.json"
MAX_QUEUE_SIZE = 5


def ensure_queue_file():
    """Ensure queue file and directory exist"""
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    if not os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'w') as f:
            json.dump([], f)


def load_queue() -> List[Dict]:
    """Load queue from file"""
    ensure_queue_file()
    try:
        with open(QUEUE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading queue: {e}")
        return []


def save_queue(queue: List[Dict]):
    """Save queue to file"""
    ensure_queue_file()
    try:
        with open(QUEUE_FILE, 'w') as f:
            json.dump(queue, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving queue: {e}")


def add_to_queue(request_data: Dict) -> Dict:
    """
    Add a request to the queue
    
    Returns:
        Dict with status and position in queue
    """
    queue = load_queue()
    
    # Check queue size
    if len(queue) >= MAX_QUEUE_SIZE:
        return {
            "status": "rejected",
            "message": f"Queue is full (max {MAX_QUEUE_SIZE} requests). Please try again later.",
            "queue_size": len(queue)
        }
    
    # Add request with metadata
    queue_item = {
        "id": len(queue) + 1,
        "data": request_data,
        "added_at": datetime.now().isoformat(),
        "status": "pending"
    }
    
    queue.append(queue_item)
    save_queue(queue)
    
    logger.info(f"Added request to queue. Position: {len(queue)}/{MAX_QUEUE_SIZE}")
    
    return {
        "status": "queued",
        "message": f"Request added to queue. Position: {len(queue)}/{MAX_QUEUE_SIZE}. Will be processed at 23:00.",
        "position": len(queue),
        "queue_size": len(queue),
        "scheduled_time": "23:00"
    }


def get_queue() -> List[Dict]:
    """Get all items in queue"""
    return load_queue()


def get_pending_requests() -> List[Dict]:
    """Get only pending requests"""
    queue = load_queue()
    return [item for item in queue if item.get("status") == "pending"]


def clear_queue():
    """Clear all items from queue"""
    save_queue([])
    logger.info("Queue cleared")


def mark_as_processed(request_id: int):
    """Mark a request as processed"""
    queue = load_queue()
    for item in queue:
        if item.get("id") == request_id:
            item["status"] = "processed"
            item["processed_at"] = datetime.now().isoformat()
    save_queue(queue)


def remove_processed():
    """Remove all processed items from queue"""
    queue = load_queue()
    queue = [item for item in queue if item.get("status") != "processed"]
    save_queue(queue)
    logger.info("Removed processed items from queue")