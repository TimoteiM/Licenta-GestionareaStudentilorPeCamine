from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Student, StudentCazat, Camera, Camin, CerereCazare, User, IstoricCazari
from app.database import SessionLocal
from app.security import get_current_user
from app.schemas import StudentResponse, CazareResponse
from app.routers.notificari import send_email
router = APIRouter(prefix="/studenti", tags=["Studenti"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/me/", response_model=StudentResponse)
def get_me(current_user: Student = Depends(get_current_user)):
    """
    Returnează datele utilizatorului autentificat.
    """
    return {
        "email": current_user.email,
        "role": current_user.role
    }

@router.get("/situatie_cazare/", response_model=CazareResponse)
def get_situatie_cazare(current_user: Student = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returnează detalii despre cazarea studentului și statusul plății.
    """
    student = db.query(Student).filter(Student.email == current_user.email).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    cazare = db.query(StudentCazat).filter(StudentCazat.student_id == student.id).first()
    if not cazare:
        return {"message": "Studentul nu este cazat în niciun cămin"}

    camera = db.query(Camera).filter(Camera.id == cazare.camera_id).first()
    camin = db.query(Camin).filter(Camin.id == cazare.camin_id).first()

    return {
        "student": {
            "nume": student.nume,
            "prenume": student.prenume,
            "email": student.email,
            "telefon": student.telefon
        },
        "cazare": {
            "camin": camin.nume if camin else "N/A",
            "camera": camera.numar_camera if camera else "N/A",
            "taxa_lunara": cazare.taxa_lunara,
            "status_plata": cazare.status_plata
        }
    }

from datetime import datetime
from app.models import IstoricCazari  # Importăm modelul istoric

@router.post("/cazare_automata/")
def cazare_automata(
    current_user: User = Depends(get_current_user),  # User autenticat
    db: Session = Depends(get_db)
):
    """
    Endpoint protejat care permite unui student să solicite cazare automată.
    - Verifică dacă studentul e deja cazat.
    - Îl repartizează automat într-o cameră disponibilă.
    - Salvează în istoricul cazărilor.
    - Trimite un email studentului cu detaliile cazării.
    """
    # 🔎 **Căutăm studentul în baza de date**
    student = db.query(Student).filter(Student.email == current_user.email).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Studentul nu există în baza de date!")

    # 🔍 **Verificăm dacă studentul este deja cazat**
    cazare_existenta = db.query(StudentCazat).filter(StudentCazat.student_id == student.id).first()
    if cazare_existenta:
        raise HTTPException(status_code=400, detail="Studentul este deja cazat!")

    # 🔎 **Obținem camerele disponibile**
    camere_disponibile = db.query(Camera).filter(Camera.locuri_disponibile > 0).all()
    if not camere_disponibile:
        raise HTTPException(status_code=400, detail="Nu sunt locuri disponibile în cămine.")

    # 🏠 **Alegem prima cameră disponibilă**
    for camera in camere_disponibile:
        if camera.locuri_disponibile > 0:
            # Determinăm taxa lunară în funcție de cămin
            taxa_lunara = 250 if camera.camin_id == 1 else 200 if camera.camin_id == 2 else 150

            # Creăm înregistrarea în tabela StudentCazat
            cazare = StudentCazat(
                student_id=student.id,
                camin_id=camera.camin_id,
                camera_id=camera.id,
                taxa_lunara=taxa_lunara,
                status_plata="neplatit"
            )
            db.add(cazare)

            # 📜 **Salvăm în istoricul cazărilor**
            istoric_cazare = IstoricCazari(
                student_id=student.id,
                camin_id=camera.camin_id,
                camera_id=camera.id,
                taxa_lunara=taxa_lunara,  # ✅ Adăugăm taxa lunară
                status_plata="neplatit",  # ✅ Adăugăm statusul plății
                data_cazarii=datetime.utcnow()
            )
            db.add(istoric_cazare)

            # Reducem locurile disponibile în cameră
            camera.locuri_disponibile -= 1  
            db.commit()

            # 📩 **Trimitem email cu detalii despre cazare**
            camin = db.query(Camin).filter(Camin.id == camera.camin_id).first()
            subject = "Confirmare cazare în căminul USV"
            body = f"""
            Salut {student.nume} {student.prenume},

            Ai fost repartizat automat în căminul {camin.nume} în camera {camera.numar_camera}.
            
            Detalii cazare:
            - Camin: {camin.nume}
            - Camera: {camera.numar_camera}
            - Taxa lunară: {cazare.taxa_lunara} RON
            - Status plată: {cazare.status_plata}

            Te rugăm să confirmi această cazare și să achiți taxa cât mai curând.

            Mulțumim,
            Administrația Căminelor USV
            """
            send_email(subject, body, student.email)

            return {
                "message": "Cazare realizată cu succes! Detaliile au fost trimise pe email.",
                "camin": camin.nume,
                "camera": camera.numar_camera,
                "taxa_lunara": cazare.taxa_lunara
            }

    # ❌ **Dacă nu există camere disponibile**
    raise HTTPException(status_code=400, detail="Nu a fost posibilă repartizarea studentului.")





