from fastapi import APIRouter
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends
from app.database import SessionLocal

from app.models import StudentCazat, Student

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/notificari", tags=["notificari"])

@router.get("/")
def get_notificari():
    return {"message": "Sistem notificări activ"}

SMTP_SERVER = "smtp.gmail.com"  # Gmail SMTP server
SMTP_PORT = 587  # Port for TLS
EMAIL_ADDRESS = "timoteimoscaliucin@gmail.com"  # Your email address
EMAIL_PASSWORD = "mous qbom mkav ipqm"  # App Password (not your regular password)

def send_email(subject: str, body: str, recipient_email: str):
    """
    Trimite un email folosind configurarea SMTP.
    """
    try:
        # Construirea mesajului
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Adăugarea conținutului email-ului
        msg.attach(MIMEText(body, 'plain'))
        
        # Conectarea la serverul SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Activare TLS pentru securitate
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        
        # Trimiterea email-ului
        server.sendmail(EMAIL_ADDRESS, recipient_email, msg.as_string())
        server.quit()
        print(f"✅ Email trimis către {recipient_email}")
    except Exception as e:
        print(f"❌ Eroare la trimiterea email-ului: {e}")


@router.post("/trimite_reminder_plata/")
def trimite_reminder_plata(db: Session = Depends(get_db)):
    """
    Trimite un email studenților care nu au plătit taxa de cămin,
    cu 5 zile înainte de termenul limită (ziua 10 a lunii).
    """
    azi = datetime.today().day  # Obținem ziua curentă

    if azi != 23:  # Verificăm dacă azi este ziua 5 (5 zile înainte de ziua 10)
        return {"message": "Nu este timpul pentru notificări încă."}

    # Selectăm studenții care au statusul "neplatit"
    studenti_neplatitori = db.query(StudentCazat).filter(StudentCazat.status_plata == "neplatit").all()

    if not studenti_neplatitori:
        return {"message": "Toți studenții au plătit, nicio notificare necesară."}

    for cazare in studenti_neplatitori:
        student = db.query(Student).filter(Student.id == cazare.student_id).first()
        
        if student:
            subject = "Reminder: Plata taxei de cămin"
            body = f"""
            Salut {student.nume} {student.prenume},

            Iti reamintim că taxa pentru cămin trebuie achitată până pe **10 ale lunii**.
            În prezent, statusul tău este: **{cazare.status_plata}**.

            Te rugăm să efectuezi plata pentru a evita penalizări.

            Mulțumim,
            Administrația Căminelor USV
            """
            send_email(subject, body, student.email)  # Trimite email

    return {"message": "Notificările de plată au fost trimise cu succes!"}