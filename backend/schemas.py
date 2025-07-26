# backend/schemas.py
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional, List, Any
from pydantic_core import core_schema
import uuid
from datetime import datetime
import base64

# --- Custom PhotoURL Type ---
# This helper class teaches Pydantic how to convert raw image bytes into a displayable Data URL.
class PhotoUrl(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        def validate_from_bytes(value: bytes) -> str:
            if not isinstance(value, bytes):
                raise ValueError(f"Expected bytes, received {type(value)}")
            b64_photo = base64.b64encode(value).decode("utf-8")
            return f"data:image/png;base64,{b64_photo}"

        from_bytes_schema = core_schema.chain_schema(
            [
                core_schema.bytes_schema(),
                core_schema.no_info_plain_validator_function(validate_from_bytes),
            ]
        )
        return core_schema.json_or_python_schema(
            json_schema=from_bytes_schema,
            python_schema=core_schema.union_schema(
                [from_bytes_schema, core_schema.str_schema()]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: x
            ),
        )

# --- User Schemas ---
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str

class UserPublic(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    phone: Optional[str]
    role: str
    company: Optional[str]
    designation: Optional[str]
    profile_complete: bool
    created_at: datetime
    has_photo: bool # Simple boolean field provided by the API endpoint

    model_config = ConfigDict(from_attributes=True)

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None

# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic

# --- POST SCHEMAS ---
class PostOwner(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    has_photo: bool # Simple boolean field provided by the API endpoint
        
    model_config = ConfigDict(from_attributes=True)

class PostPublic(BaseModel):
    id: uuid.UUID
    title: str
    summary: str
    description: str
    contact_info: str
    is_hidden: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    owner: PostOwner
    photo_url: PhotoUrl = Field(validation_alias='photo') # Gets data from the model's 'photo' attribute
    
    model_config = ConfigDict(from_attributes=True)
    
class PostCreate(BaseModel):
    title: str
    description: str
    summary: str
    contact_info: str

class PostUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
    contact_info: Optional[str] = None

# --- CHAT SCHEMAS ---
class ChatMessagePublic(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatRoomPublic(BaseModel):
    id: uuid.UUID
    name: Optional[str] = None
    participants: List[UserPublic]
    messages: List[ChatMessagePublic]
    model_config = ConfigDict(from_attributes=True)