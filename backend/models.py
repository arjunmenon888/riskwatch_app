import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    LargeBinary,
    DateTime,
    func,
    Text,
    ForeignKey,
    Table
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from database import Base

# This is an "association table" for the many-to-many relationship
# between users and chat rooms. SQLAlchemy uses this to manage the links.
chat_room_participants = Table(
    'chat_room_participants',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('room_id', UUID(as_uuid=True), ForeignKey('chat_rooms.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)
    
    # Profile fields
    company = Column(String, nullable=True)
    designation = Column(String, nullable=True)
    photo = Column(LargeBinary, nullable=True)
    
    # Flags
    force_reset = Column(Boolean, default=False)
    profile_complete = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # --- Relationships ---
    # One-to-Many: A user can have many posts.
    posts = relationship("Post", back_populates="owner", cascade="all, delete-orphan")
    
    # Many-to-Many: A user can be in many chat rooms.
    chat_rooms = relationship(
        "ChatRoom",
        secondary=chat_room_participants,
        back_populates="participants"
    )

class Post(Base):
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    summary = Column(String, nullable=False)
    photo = Column(LargeBinary, nullable=False)
    contact_info = Column(String, nullable=False)
    
    is_hidden = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign key to link to the 'users' table
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Relationship back to the User object
    owner = relationship("User", back_populates="posts")

class ChatRoom(Base):
    __tablename__ = "chat_rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=True) # For potential group chats
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # --- Relationships ---
    # Many-to-Many: A chat room has many participants (users).
    participants = relationship(
        "User",
        secondary=chat_room_participants,
        back_populates="chat_rooms"
    )
    
    # One-to-Many: A chat room has many messages.
    # cascade="all, delete-orphan" means if a room is deleted, its messages are also deleted.
    messages = relationship("ChatMessage", back_populates="room", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Foreign keys to link messages to rooms and senders
    room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # --- Relationships ---
    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("User")

class ChatAttachment(Base):
    __tablename__ = "chat_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    data = Column(LargeBinary, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("chat_rooms.id"), nullable=False)

    sender = relationship("User")
    room = relationship("ChatRoom")
