from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Camin, Camera

router = APIRouter(prefix="/camine", tags=["camine"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_camine(db: Session = Depends(get_db)):
    return db.query(Camin).all()

@router.get("/camere/")
def get_camere(db: Session = Depends(get_db)):
    return db.query(Camera).all()

@router.get("/disponibilitate/")
def get_camere_disponibile(db: Session = Depends(get_db)):
    """
    Returnează lista căminelor, camerelor și locurilor disponibile.
    Acest endpoint este public și poate fi accesat fără autentificare.
    """
    camine = db.query(Camin).all()
    camere = db.query(Camera).all()

    rezultat = []
    for camin in camine:
        camere_camin = [
            {
                "numar_camera": camera.numar_camera,
                "locuri_disponibile": camera.locuri_disponibile
            }
            for camera in camere if camera.camin_id == camin.id
        ]

        rezultat.append({
            "camin": camin.nume,
            "adresa": camin.adresa,
            "total_camere": len(camere_camin),
            "camere": camere_camin
        })

    return rezultat
