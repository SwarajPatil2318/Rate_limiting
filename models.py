from sqlalchemy import Column, Integer, String,ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

class Subject(Base):
    __tablename__ = "subjects"
    subject_id = Column(Integer,primary_key=True,index=True)
    subject_name = Column(String(100), nullable=False)

class Courseregistration(Base):
    __tablename__ = "course_registration"

    id = Column(Integer,primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id"), nullable=False)