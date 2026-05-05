from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    department = Column(String, nullable=False)
    role = Column(String, nullable=False)  # employee | manager | admin
    hashed_password = Column(String, nullable=False)

    assignments = relationship("CourseAssignment", back_populates="user", cascade="all, delete-orphan")
    progresses = relationship("Progress", back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)

    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="course", cascade="all, delete-orphan")
    assignments = relationship("CourseAssignment", back_populates="course", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    attachment = Column(String, nullable=True)
    lesson_number = Column(Integer, nullable=False)

    course = relationship("Course", back_populates="lessons")


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    completion_percentage = Column(Float, default=0)
    deadline = Column(Date, nullable=True)

    user = relationship("User", back_populates="progresses")


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    questions = Column(Text, nullable=False)

    course = relationship("Course", back_populates="tests")


class CourseAssignment(Base):
    __tablename__ = "course_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    status = Column(String, nullable=False, default="in-progress")

    user = relationship("User", back_populates="assignments")
    course = relationship("Course", back_populates="assignments")
