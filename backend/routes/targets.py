from fastapi import APIRouter, HTTPException
import os
from backend.config import LOCATIONS_DIR, DATA_FILE, load_data, save_data

router = APIRouter()

# [GET] targets
@router.get("/targets")
async def get_targets():
    return [
        {"id": 1, "name": "Target A", "lat": 37.7749, "lng": -122.4194},
        {"id": 2, "name": "Target B", "lat": 37.7849, "lng": -122.4294},
        {"id": 3, "name": "Target C", "lat": 37.7949, "lng": -122.4394}
    ]