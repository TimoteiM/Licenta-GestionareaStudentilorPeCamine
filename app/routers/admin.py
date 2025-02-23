from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Student, StudentCazat, Camera, Camin, CerereCazare, User, IstoricCazari
from app.database import SessionLocal
from app.security import get_admin_user
from app.schemas import CazareResponse
from app.routers.notificari import send_email
import schedule
import time
from sqlalchemy.sql import func
import csv
import pandas as pd
from io import StringIO
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/admin", tags=["Admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/studenti_cazati/", response_model=list[CazareResponse])
def get_all_cazati(db: Session = Depends(get_db), admin: str = Depends(get_admin_user)):
    """
    Returnează lista tuturor studenților cazați (admin only).
    """
    studenti_cazati = db.query(StudentCazat).all()
    rezultat = []
    
    for cazare in studenti_cazati:
        student = db.query(Student).filter(Student.id == cazare.student_id).first()
        camin = db.query(Camin).filter(Camin.id == cazare.camin_id).first()
        camera = db.query(Camera).filter(Camera.id == cazare.camera_id).first()

        rezultat.append({
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
        })

    return rezultat

@router.put("/actualizare_plata/{student_id}/")
def actualizare_plata(student_id: int, status_plata: str, db: Session = Depends(get_db), admin: str = Depends(get_admin_user)):
    cazare = db.query(StudentCazat).filter(StudentCazat.student_id == student_id).first()
    
    if not cazare:
        raise HTTPException(status_code=404, detail="Studentul nu este cazat.")

    if status_plata not in ["platit", "neplatit"]:
        raise HTTPException(status_code=400, detail="Status invalid. Folosește 'platit' sau 'neplatit'.")

    cazare.status_plata = status_plata
    db.commit()

    # 📩 Trimitere email studentului
    student = db.query(Student).filter(Student.id == student_id).first()
    subject = "Actualizare plată cămin"
    body = f"Salut {student.nume},\n\nStatusul plății pentru cazarea ta este acum: {status_plata.upper()}."
    send_email(subject, body, student.email)

    return {"message": f"Statusul plății pentru studentul {student_id} a fost actualizat la '{status_plata}'."}


@router.delete("/sterge_cazare/{student_id}/")
def sterge_cazare(student_id: int, db: Session = Depends(get_db), admin: str = Depends(get_admin_user)):
    cazare = db.query(StudentCazat).filter(StudentCazat.student_id == student_id).first()

    if not cazare:
        raise HTTPException(status_code=404, detail="Studentul nu este cazat.")

    student = db.query(Student).filter(Student.id == student_id).first()

    db.delete(cazare)
    db.commit()

    # 📩 Trimitere email studentului
    subject = "Eliminare din cămin"
    body = f"Salut {student.nume},\n\nTe informăm că ai fost eliminat din cămin. Pentru detalii, contactează administrația."
    send_email(subject, body, student.email)

    return {"message": f"Cazarea studentului {student_id} a fost ștearsă."}

@router.get("/admin/cereri_cazare/", dependencies=[Depends(get_admin_user)])
def get_cereri_cazare(db: Session = Depends(get_db)):
    """
    Adminul poate vedea toate cererile de cazare.
    """
    return db.query(CerereCazare).all()

@router.put("/admin/aprobare_cazare/{cerere_id}/", dependencies=[Depends(get_admin_user)])
def aproba_cazare(cerere_id: int, db: Session = Depends(get_db)):
    """
    Adminul poate aproba o cerere de cazare și să adauge studentul în cămin.
    """
    cerere = db.query(CerereCazare).filter(CerereCazare.id == cerere_id).first()

    if not cerere:
        raise HTTPException(status_code=404, detail="Cererea nu există.")

    student = db.query(Student).filter(Student.id == cerere.student_id).first()
    camera = db.query(Camera).filter(Camera.camin_id == cerere.camin_preferat, Camera.locuri_disponibile > 0).first()

    if not camera:
        raise HTTPException(status_code=400, detail="Nu sunt locuri disponibile.")

    # Cazare student
    cazare = StudentCazat(
        student_id=student.id,
        camin_id=cerere.camin_preferat,
        camera_id=camera.id,
        taxa_lunara=250,
        status_plata="neplatit"
    )
    db.add(cazare)
    db.delete(cerere)
    db.commit()

    return {"message": f"Studentul {student.nume} a fost cazat!"}

from datetime import datetime
from app.models import IstoricCazari  # Importăm modelul istoric

@router.put("/mutare_student/{student_id}/", dependencies=[Depends(get_admin_user)])
def mutare_student(
    student_id: int,
    nou_camin_id: int,
    nou_camera_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint care permite mutarea unui student într-un alt cămin sau o altă cameră.
    🚨 Doar adminul poate accesa acest endpoint!
    """
    # 🔍 **Verificăm dacă studentul este cazat**
    cazare = db.query(StudentCazat).filter(StudentCazat.student_id == student_id).first()
    if not cazare:
        raise HTTPException(status_code=404, detail="Studentul nu este cazat!")

    # 🔍 **Verificăm dacă noua cameră are locuri disponibile**
    noua_camera = db.query(Camera).filter(Camera.id == nou_camera_id, Camera.camin_id == nou_camin_id).first()
    if not noua_camera:
        raise HTTPException(status_code=404, detail="Camera selectată nu există!")

    if noua_camera.locuri_disponibile <= 0:
        raise HTTPException(status_code=400, detail="Noua cameră nu are locuri disponibile!")

    # 🔄 **Actualizăm cazarea**
    vechea_camera = db.query(Camera).filter(Camera.id == cazare.camera_id).first()
    
    if vechea_camera:
        vechea_camera.locuri_disponibile += 1  # Eliberăm locul din camera veche
    
    noua_camera.locuri_disponibile -= 1  # Ocupăm un loc în noua cameră

    # 🔥 **Salvăm mutarea în istoricul cazărilor**
    istoric_mutare = IstoricCazari(
        student_id=student_id,
        camin_id=nou_camin_id,
        camera_id=nou_camera_id,
        taxa_lunara=cazare.taxa_lunara,  # ✅ Setăm taxa lunară
        status_plata=cazare.status_plata,  # ✅ Setăm statusul plății
        data_cazarii=datetime.utcnow()
    )
    db.add(istoric_mutare)

    # 🔄 **Actualizăm înregistrarea din StudentCazat**
    cazare.camin_id = nou_camin_id
    cazare.camera_id = nou_camera_id
    db.commit()

    # 🔎 **Obținem informațiile studentului**
    student = db.query(Student).filter(Student.id == student_id).first()

    # 📩 **Trimitem email cu notificarea mutării**
    camin_nou = db.query(Camin).filter(Camin.id == nou_camin_id).first()
    subject = "Notificare: Mutare în noul cămin"
    body = f"""
    Salut {student.nume} {student.prenume},

    Ai fost mutat în noul cămin {camin_nou.nume}, camera {noua_camera.numar_camera}.

    Detalii mutare:
    - Noul cămin: {camin_nou.nume}
    - Noua cameră: {noua_camera.numar_camera}
    - Taxa lunară: {cazare.taxa_lunara} RON
    - Status plată: {cazare.status_plata}

    Te rugăm să iei legătura cu administrația pentru preluarea noului loc.

    Mulțumim,
    Administrația Căminelor USV
    """
    send_email(subject, body, student.email)

    return {
        "message": "Mutarea studentului a fost realizată cu succes!",
        "noul_camin": camin_nou.nume,
        "noua_camera": noua_camera.numar_camera
    }



@router.delete("/sterge_utilizator/{email}/", dependencies=[Depends(get_admin_user)])
def sterge_utilizator(email: str, db: Session = Depends(get_db)):
    """
    🔐 Permite adminului să șteargă un utilizator și studentul asociat.
    """
    # Căutăm utilizatorul în baza de date
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilizatorul nu a fost găsit!")

    # Căutăm studentul asociat (dacă există)
    student = db.query(Student).filter(Student.email == email).first()
    
    # Ștergem studentul asociat
    if student:
        db.delete(student)

    # Ștergem utilizatorul
    db.delete(user)

    # Salvăm modificările
    db.commit()

    return {"message": f"Utilizatorul {email} și studentul asociat au fost șterși cu succes!"}

@router.get("/dashboard/", dependencies=[Depends(get_admin_user)])
def get_dashboard_admin(db: Session = Depends(get_db)):
    """
    📊 Dashboard pentru Admini - returnează statistici generale despre cămine
    """
    total_locuri = db.query(func.sum(Camin.capacitate_totala)).scalar()
    locuri_ocupate = db.query(func.count(StudentCazat.id)).scalar()
    studenti_neplatiti = db.query(func.count(StudentCazat.id)).filter(StudentCazat.status_plata == "neplatit").scalar()
    studenti_platiti = locuri_ocupate - studenti_neplatiti

    camine = db.query(Camin).all()
    statistici_camine = []
    
    for camin in camine:
        studenti_camin = db.query(func.count(StudentCazat.id)).filter(StudentCazat.camin_id == camin.id).scalar()
        statistici_camine.append({
            "camin": camin.nume,
            "locuri_ocupate": studenti_camin,
            "locuri_disponibile": camin.capacitate_totala - studenti_camin
        })

    return {
        "total_locuri": total_locuri,
        "locuri_ocupate": locuri_ocupate,
        "locuri_disponibile": total_locuri - locuri_ocupate,
        "studenti_platiti": studenti_platiti,
        "studenti_neplatiti": studenti_neplatiti,
        "statistici_camine": statistici_camine
    }



@router.get("/export/{format}/", dependencies=[Depends(get_admin_user)])
def export_data(format: str, db: Session = Depends(get_db)):
    """
    📂 Exportă lista studenților cazați în CSV sau Excel
    """
    studenti_cazati = db.query(Student, StudentCazat).join(StudentCazat).all()

    data = [
        {
            "Nume": student.nume,
            "Prenume": student.prenume,
            "Email": student.email,
            "Camin": db.query(Camin).filter(Camin.id == cazare.camin_id).first().nume,
            "Camera": db.query(Camera).filter(Camera.id == cazare.camera_id).first().numar_camera,
            "Taxa lunară": cazare.taxa_lunara,
            "Status plată": cazare.status_plata
        }
        for student, cazare in studenti_cazati
    ]

    if format == "csv":
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        output.seek(0)
        return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=studenti.csv"})

    elif format == "excel":
        df = pd.DataFrame(data)
        output = StringIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 headers={"Content-Disposition": "attachment; filename=studenti.xlsx"})

    return {"error": "Format invalid. Folosește csv sau excel"}
