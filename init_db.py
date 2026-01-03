from database import SessionLocal, engine, Base
from models import Subject

def insert_subject(db):
    subjects = [
        {"subject_id": 4, "subject_name": "Maths"},
        {"subject_id": 5, "subject_name": "English"},
        {"subject_id": 6, "subject_name": "Science"},
    ]

    for sub in subjects:
        exists = db.query(Subject).filter(
            Subject.subject_id == sub["subject_id"]
        ).first()
        if not exists:
            db.add(Subject(**sub))
    db.commit()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    insert_subject(db)
    db.close()
    print("DB initialized successfully")
