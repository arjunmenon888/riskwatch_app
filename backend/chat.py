# backend/chat.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from apscheduler.schedulers.background import BackgroundScheduler
from io import BytesIO
from datetime import datetime, timedelta
import uuid
from typing import Dict, List

import models, schemas, auth, database

router = APIRouter(tags=["Chat"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: uuid.UUID):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: uuid.UUID):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)

    async def broadcast_to_room(self, room_id: uuid.UUID, message: dict, db: Session):
        room = db.query(models.ChatRoom).filter(models.ChatRoom.id == room_id).first()
        if room:
            for participant in room.participants:
                if participant.id in self.active_connections:
                    await self.send_personal_message(message, participant.id)

manager = ConnectionManager()

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user = None
    db = database.SessionLocal()
    try:
        user = auth.get_user_from_token(token, db)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        await manager.connect(user.id, websocket)
        
        try:
            while True:
                data = await websocket.receive_json()
                room_id = data.get('room_id')
                content = data.get('content')
                
                if not room_id or not content:
                    continue

                new_message = models.ChatMessage(
                    room_id=room_id, sender_id=user.id, content=content
                )
                db.add(new_message)
                db.commit()
                db.refresh(new_message)

                message_data = schemas.ChatMessagePublic.model_validate(new_message).model_dump()
                await manager.broadcast_to_room(uuid.UUID(room_id), message_data, db)
        except WebSocketDisconnect:
            print(f"Client {user.id} disconnected.")
        except Exception as e:
            print(f"WebSocket processing error for user {user.id}: {e}")
    finally:
        if user:
            manager.disconnect(user.id)
        db.close()

# --- Chat Room Utilities ---

def construct_chat_room_public(room: models.ChatRoom) -> schemas.ChatRoomPublic:
    participants_data = []
    for p in room.participants:
        participants_data.append(schemas.UserPublic(
            id=p.id, name=p.name, email=p.email, phone=p.phone, role=p.role,
            company=p.company, designation=p.designation, profile_complete=p.profile_complete,
            created_at=p.created_at, has_photo=(p.photo is not None)
        ))

    messages_data = [schemas.ChatMessagePublic.model_validate(m) for m in room.messages]

    return schemas.ChatRoomPublic(
        id=room.id, name=room.name,
        participants=participants_data,
        messages=messages_data
    )

class CreateRoomRequest(schemas.BaseModel):
    recipient_email: str

@router.post("/chat/rooms", response_model=schemas.ChatRoomPublic)
def create_or_get_chat_room(
    request: CreateRoomRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if request.recipient_email == current_user.email:
        raise HTTPException(status_code=400, detail="Cannot start a chat with yourself")

    recipient = db.query(models.User).filter(models.User.email == request.recipient_email).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="User not found")

    existing_room = db.query(models.ChatRoom).filter(
        models.ChatRoom.participants.contains(current_user),
        models.ChatRoom.participants.contains(recipient)
    ).first()

    if existing_room:
        return construct_chat_room_public(existing_room)

    new_room = models.ChatRoom(name=f"{current_user.name} & {recipient.name}")
    new_room.participants.append(current_user)
    new_room.participants.append(recipient)
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return construct_chat_room_public(new_room)

@router.get("/chat/rooms", response_model=List[schemas.ChatRoomPublic])
def get_user_chat_rooms(
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(auth.get_current_user)
):
    user_rooms = db.query(models.ChatRoom).filter(
        models.ChatRoom.participants.contains(current_user)
    ).options(
        selectinload(models.ChatRoom.participants)
    ).order_by(models.ChatRoom.created_at.desc()).all()

    return [construct_chat_room_public(room) for room in user_rooms]

@router.get("/chat/users/search")
def search_users(
    query: str,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not query.strip():
        return []

    search_filter = and_(
        models.User.email.ilike(f"%{query}%"),
        models.User.id != current_user.id
    )

    if current_user.role != 'admin':
        search_filter = and_(search_filter, models.User.role != 'admin')

    users = db.query(models.User).filter(search_filter).limit(10).all()

    return [
        {"id": user.id, "email": user.email, "name": user.name, "has_photo": user.photo is not None}
        for user in users
    ]

# --- File Upload & Auto Delete ---

@router.post("/chat/upload")
async def upload_file(
    room_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        room_uuid = uuid.UUID(room_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid room_id")

    content = await file.read()
    attachment = models.ChatAttachment(
        filename=file.filename,
        content_type=file.content_type,
        data=content,
        sender_id=current_user.id,
        room_id=room_uuid,
    )
    db.add(attachment)
    db.commit()
    return {"id": str(attachment.id), "filename": file.filename}

@router.get("/chat/file/{file_id}")
def get_file(file_id: uuid.UUID, db: Session = Depends(database.get_db)):
    file = db.query(models.ChatAttachment).filter(models.ChatAttachment.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return StreamingResponse(BytesIO(file.data), media_type=file.content_type, headers={
        "Content-Disposition": f"inline; filename={file.filename}"
    })

def delete_old_attachments():
    db = database.SessionLocal()
    cutoff = datetime.utcnow() - timedelta(days=10)
    db.query(models.ChatAttachment).filter(models.ChatAttachment.uploaded_at < cutoff).delete()
    db.commit()
    db.close()

@router.on_event("startup")
def start_cleanup_job():
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_old_attachments, "interval", days=1)
    scheduler.start()
