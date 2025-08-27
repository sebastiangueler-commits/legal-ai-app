from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Optional
import os

from config import settings

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    cases = relationship("Case", back_populates="user")
    documents = relationship("Document", back_populates="user")

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    case_type = Column(String)  # civil, criminal, labor, etc.
    status = Column(String)  # active, closed, pending
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="cases")
    documents = relationship("Document", back_populates="case")
    predictions = relationship("Prediction", back_populates="case")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    document_type = Column(String)  # demanda, contestacion, etc.
    content = Column(Text)
    file_path = Column(String, nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case = relationship("Case", back_populates="documents")
    user = relationship("User", back_populates="documents")

class LegalDocument(Base):
    __tablename__ = "legal_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    tribunal = Column(String)
    fecha = Column(DateTime)
    materia = Column(String)
    partes = Column(String)
    expediente = Column(String)
    full_text = Column(Text)
    url = Column(String)
    embedding_vector = Column(Text, nullable=True)  # JSON string of embedding
    created_at = Column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    predicted_outcome = Column(String)
    confidence_score = Column(Float)
    similar_cases = Column(Text)  # JSON string of similar cases
    explanation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    case = relationship("Case", back_populates="predictions")

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    document_type = Column(String)
    content = Column(Text)
    structure = Column(Text)  # JSON string of document structure
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)