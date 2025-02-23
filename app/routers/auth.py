from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.database import SessionLocal
from app.security import verify_password, get_password_hash, create_access_token
from app.models import User, Student
from datetime import timedelta
from app.routers.notificari import send_email
from app.schemas import UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@router.post("/register/")
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    ✅ Înregistrează un utilizator și îl adaugă și în tabela `studenti`.
    """
    # Verificăm dacă utilizatorul există deja
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email-ul este deja utilizat!")

    # 🔑 Hash-uim parola înainte de salvare
    hashed_password = get_password_hash(user_data.password)

    # 🔹 Adăugăm utilizatorul în tabela `users`
    new_user = User(email=user_data.email, hashed_password=hashed_password, role=user_data.role)
    db.add(new_user)

    # 🔹 Adăugăm utilizatorul și în tabela `studenti`
    if user_data.role == "student":
        new_student = Student(
            email=user_data.email,
            nume=user_data.nume,
            prenume=user_data.prenume,
            telefon=user_data.telefon,
            facultate=user_data.facultate,
            specializare=user_data.specializare,
            an_studiu=user_data.an_studiu,
            grupa=user_data.grupa,
            medie_anuala=user_data.medie_anuala
        )
        db.add(new_student)

    # 🔥 Salvăm modificările
    db.commit()

    return {"message": "Utilizator înregistrat cu succes!"}


@router.post("/token/")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role}, expires_delta=timedelta(minutes=30))
    return {"access_token": access_token, "token_type": "bearer"}


