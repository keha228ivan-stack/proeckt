from collections import defaultdict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .auth import create_access_token, get_current_user, hash_password, require_role, verify_password
from .database import Base, engine, get_db
from .models import Course, CourseAssignment, Progress, User
from .schemas import CourseOut, Token, UserCreate, UserOut

Base.metadata.create_all(bind=engine)

app = FastAPI(title="HR Local API")


@app.post("/auth/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")
    user = User(
        name=payload.name,
        email=payload.email,
        department=payload.department,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return Token(access_token=create_access_token(user.email))


@app.post("/manager/assign/{user_id}/{course_id}")
def assign_course(
    user_id: int,
    course_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("manager")),
):
    existing = db.query(CourseAssignment).filter_by(user_id=user_id, course_id=course_id).first()
    if existing:
        return {"status": "already_assigned"}
    assignment = CourseAssignment(user_id=user_id, course_id=course_id, status="in-progress")
    db.add(assignment)
    db.commit()
    return {"status": "assigned"}


@app.get("/employee_courses/{user_id}")
def employee_courses(user_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("manager"))):
    total = db.query(CourseAssignment).filter_by(user_id=user_id).count()
    return {"user_id": user_id, "assigned_courses": total}


@app.get("/my_courses", response_model=list[CourseOut])
def my_courses(current: User = Depends(require_role("employee")), db: Session = Depends(get_db)):
    rows = db.query(Course).join(CourseAssignment).filter(CourseAssignment.user_id == current.id).all()
    return rows


@app.get("/my_courses/{course_id}/progress")
def my_course_progress(course_id: int, current: User = Depends(require_role("employee")), db: Session = Depends(get_db)):
    progress = db.query(Progress).filter_by(course_id=course_id, user_id=current.id).first()
    if not progress:
        return {"completion_percentage": 0}
    return {"completion_percentage": progress.completion_percentage}


@app.get("/my_courses/{course_id}/test")
def my_course_test(course_id: int, current: User = Depends(require_role("employee")), db: Session = Depends(get_db)):
    progress = db.query(Progress).filter_by(course_id=course_id, user_id=current.id).first()
    if not progress or progress.completion_percentage < 100:
        raise HTTPException(status_code=403, detail="Test is available only after course completion")
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course or not course.tests:
        raise HTTPException(status_code=404, detail="Test not found")
    return {"questions": course.tests[0].questions}


@app.get("/stats")
def stats(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    users_count = db.query(User).count()
    courses_count = db.query(Course).count()
    assignments_count = db.query(CourseAssignment).count()
    return {"employees_total": users_count, "courses_total": courses_count, "assignments_total": assignments_count}


@app.get("/stats/{department}")
def stats_by_department(department: str, _: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    users = db.query(User).filter_by(department=department).all()
    user_ids = [u.id for u in users]
    assignments = db.query(CourseAssignment).all()
    assigned_by_dep = sum(1 for a in assignments if a.user_id in user_ids)
    return {"department": department, "employees": len(users), "assigned_courses": assigned_by_dep}


@app.get("/course_library", response_model=list[CourseOut])
def course_library(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Course).all()
