from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pymongo.collection import Collection
from typing import List, Optional
from datetime import datetime
from src.backend.database import announcements_collection
from src.backend.routers.auth import get_current_user

router = APIRouter()

def announcement_dict(announcement):
    return {
        "id": str(announcement.get("_id", "")),
        "title": announcement.get("title", ""),
        "message": announcement.get("message", ""),
        "start_date": announcement.get("start_date"),
        "expiration_date": announcement.get("expiration_date"),
        "created_by": announcement.get("created_by"),
        "created_at": announcement.get("created_at"),
    }

@router.get("/announcements", response_model=List[dict])
def get_announcements():
    now = datetime.utcnow().isoformat()
    announcements = list(announcements_collection.find({
        "$or": [
            {"start_date": None},
            {"start_date": {"$lte": now}}
        ],
        "expiration_date": {"$gte": now}
    }))
    return [announcement_dict(a) for a in announcements]

@router.get("/announcements/manage", response_model=List[dict])
def get_all_announcements(current_user=Depends(get_current_user)):
    return [announcement_dict(a) for a in announcements_collection.find()]

@router.post("/announcements", status_code=201)
def create_announcement(announcement: dict, current_user=Depends(get_current_user)):
    if not announcement.get("expiration_date"):
        raise HTTPException(status_code=400, detail="Expiration date is required.")
    announcement["created_by"] = current_user["username"]
    announcement["created_at"] = datetime.utcnow().isoformat()
    result = announcements_collection.insert_one(announcement)
    return {"id": str(result.inserted_id)}

@router.put("/announcements/{announcement_id}")
def update_announcement(announcement_id: str, announcement: dict, current_user=Depends(get_current_user)):
    result = announcements_collection.update_one({"_id": announcement_id}, {"$set": announcement})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    return {"status": "updated"}

@router.delete("/announcements/{announcement_id}")
def delete_announcement(announcement_id: str, current_user=Depends(get_current_user)):
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    return {"status": "deleted"}
