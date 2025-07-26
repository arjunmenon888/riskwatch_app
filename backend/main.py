# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import uuid

# Import local modules
import models, schemas, auth, database, posts, chat

database.Base.metadata.create_all(bind=database.engine) 

app = FastAPI(title="RiskWatch API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --- AUTHENTICATION ROUTES (UPDATED) ---
def login_logic(user_credentials: schemas.UserLogin, db: Session):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user or not auth.verify_password(user_credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = auth.create_access_token(data={"sub": str(user.id), "role": user.role})
    
    # Explicitly construct the UserPublic response to ensure lazy-loading is triggered for the photo.
    user_data = schemas.UserPublic(
        id=user.id, name=user.name, email=user.email, phone=user.phone, role=user.role,
        company=user.company, designation=user.designation, profile_complete=user.profile_complete,
        created_at=user.created_at, has_photo=(user.photo is not None)
    )
    return {"access_token": access_token, "token_type": "bearer", "user": user_data}

@app.post("/login", response_model=schemas.LoginResponse)
def login_for_access_token(user_credentials: schemas.UserLogin, db: Session = Depends(database.get_db)):
    return login_logic(user_credentials, db)

# --- PROFILE ROUTES (UPDATED) ---
@app.get("/users/me", response_model=schemas.UserPublic)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    # Explicitly construct the response to ensure lazy-loading is triggered for the photo.
    return schemas.UserPublic(
        id=current_user.id, name=current_user.name, email=current_user.email, phone=current_user.phone, role=current_user.role,
        company=current_user.company, designation=current_user.designation, profile_complete=current_user.profile_complete,
        created_at=current_user.created_at, has_photo=(current_user.photo is not None)
    )

@app.put("/users/me", response_model=schemas.UserPublic)
def update_profile(
    profile_data: schemas.ProfileUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    if not current_user.profile_complete:
        current_user.profile_complete = True
    
    db.commit()
    db.refresh(current_user)
    
    # After updating, construct the response explicitly
    return schemas.UserPublic(
        id=current_user.id, name=current_user.name, email=current_user.email, phone=current_user.phone, role=current_user.role,
        company=current_user.company, designation=current_user.designation, profile_complete=current_user.profile_complete,
        created_at=current_user.created_at, has_photo=(current_user.photo is not None)
    )

@app.post("/users/me/photo")
async def upload_photo(file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    contents = await file.read()
    current_user.photo = contents
    db.commit()
    return {"message": "Photo uploaded successfully"}

@app.get("/users/{user_id}/photo")
def get_user_photo(user_id: uuid.UUID, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return StreamingResponse(BytesIO(user.photo), media_type="image/png")

# --- Include Routers from other files ---
app.include_router(posts.router)
app.include_router(chat.router)