# backend/posts.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from PIL import Image
from io import BytesIO
import uuid

import models, schemas, auth, database

router = APIRouter(prefix="/posts", tags=["Posts"])
TILE_DIMENSIONS = (400, 300)

def resize_image(image_data: bytes) -> bytes:
    image = Image.open(BytesIO(image_data))
    new_image = Image.new("RGB", TILE_DIMENSIONS, (255, 255, 255))
    image.thumbnail(TILE_DIMENSIONS)
    left = (TILE_DIMENSIONS[0] - image.width) // 2
    top = (TILE_DIMENSIONS[1] - image.height) // 2
    new_image.paste(image, (left, top))
    in_mem_file = BytesIO()
    new_image.save(in_mem_file, format='PNG')
    return in_mem_file.getvalue()

# --- HELPER FUNCTION TO CONSTRUCT THE RESPONSE ---
def construct_post_public(post: models.Post) -> schemas.PostPublic:
    """Helper function to explicitly construct the PostPublic response, ensuring lazy-load."""
    if not post or not post.owner:
        return None

    owner_data = schemas.PostOwner(
        id=post.owner.id,
        name=post.owner.name,
        email=post.owner.email,
        has_photo=(post.owner.photo is not None) # Explicitly access photo
    )
    
    return schemas.PostPublic(
        id=post.id, title=post.title, summary=post.summary, description=post.description,
        contact_info=post.contact_info, is_hidden=post.is_hidden,
        created_at=post.created_at, updated_at=post.updated_at,
        owner=owner_data,
        photo=post.photo # Pass raw photo bytes for PhotoUrl conversion
    )

@router.post("/", response_model=schemas.PostPublic, status_code=status.HTTP_201_CREATED)
async def create_post(
    title: str = Form(...), description: str = Form(...), summary: str = Form(...),
    contact_info: str = Form(...), file: UploadFile = File(...),
    db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)
):
    image_bytes = await file.read()
    resized_image_bytes = resize_image(image_bytes)
    new_post = models.Post(
        title=title, description=description, summary=summary, contact_info=contact_info,
        photo=resized_image_bytes, owner_id=current_user.id
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return construct_post_public(new_post)

@router.get("/", response_model=List[schemas.PostPublic])
def get_all_posts(db: Session = Depends(database.get_db)):
    posts = db.query(models.Post).filter(models.Post.is_hidden == False).order_by(models.Post.created_at.desc()).all()
    return [construct_post_public(post) for post in posts if post]

@router.get("/me", response_model=List[schemas.PostPublic])
def get_my_posts(db: Session = Depends(database.get_db), current_user: models.User = Depends(auth.get_current_user)):
    posts = db.query(models.Post).filter(models.Post.owner_id == current_user.id).order_by(models.Post.created_at.desc()).all()
    return [construct_post_public(post) for post in posts if post]

@router.get("/{post_id}", response_model=schemas.PostPublic)
def get_single_post(post_id: uuid.UUID, db: Session = Depends(database.get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return construct_post_public(post)

@router.put("/{post_id}", response_model=schemas.PostPublic)
def update_post(
    post_id: uuid.UUID, post_update: schemas.PostUpdate, db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()
    if not post or post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    post_query.update(post_update.model_dump(exclude_unset=True), synchronize_session=False)
    db.commit()
    updated_post = post_query.first()
    return construct_post_public(updated_post)

@router.patch("/{post_id}/toggle-visibility", response_model=schemas.PostPublic)
def toggle_post_visibility(
    post_id: uuid.UUID, db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post or post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    post.is_hidden = not post.is_hidden
    db.commit()
    db.refresh(post)
    return construct_post_public(post)

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: uuid.UUID, db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post or post.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(post)
    db.commit()
    return