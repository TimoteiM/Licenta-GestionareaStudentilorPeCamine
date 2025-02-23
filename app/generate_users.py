from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Student, User
from app.security import get_password_hash

session = SessionLocal()

# Parola implicită pentru toți studenții
default_password = "password123"
hashed_password = get_password_hash(default_password)

# Verificăm dacă există deja utilizatori în baza de date
existing_users = session.query(User).count()
if existing_users > 0:
    print("✅ Utilizatorii există deja în baza de date.")
else:
    studenti = session.query(Student).all()
    
    for student in studenti:
        user = User(
            email=student.email,
            hashed_password=hashed_password,
            role="student"
        )
        session.add(user)

    session.commit()
    print("✅ Toți studenții au fost adăugați ca utilizatori cu parola implicită.")
    
session.close()
