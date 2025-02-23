from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

from datetime import datetime

class Student(Base):
    __tablename__ = "studenti"

    id = Column(Integer, primary_key=True, index=True)
    nume = Column(String, nullable=False)
    prenume = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    telefon = Column(String, nullable=False)
    facultate = Column(String, nullable=False)
    specializare = Column(String, nullable=False)
    an_studiu = Column(Integer, nullable=False)
    grupa = Column(String, nullable=False)
    medie_anuala = Column(Float, nullable=False)

class Camin(Base):
    __tablename__ = "camine"

    id = Column(Integer, primary_key=True, index=True)
    nume = Column(String, nullable=False)
    adresa = Column(String, nullable=False)
    capacitate_totala = Column(Integer, nullable=False)

class Camera(Base):
    __tablename__ = "camere"

    id = Column(Integer, primary_key=True, index=True)
    camin_id = Column(Integer, ForeignKey("camine.id"))
    numar_camera = Column(String, nullable=False)
    locuri_disponibile = Column(Integer, nullable=False)

class StudentCazat(Base):
    __tablename__ = "studenti_cazati"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("studenti.id"))
    camin_id = Column(Integer, ForeignKey("camine.id"))
    camera_id = Column(Integer, ForeignKey("camere.id"))
    taxa_lunara = Column(Float, nullable=False, default=0)
    status_plata_enum = Enum("neplatit", "platit", "intarziat", name="status_plata_enum")
    status_plata = Column(status_plata_enum, default="neplatit")
    data_cazare = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum("student", "admin", name="role_enum"), default="student")
    is_active = Column(Boolean, default=True)

class IstoricCazari(Base):
    __tablename__ = "istoric_cazari"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("studenti.id"))
    camin_id = Column(Integer, ForeignKey("camine.id"))
    camera_id = Column(Integer, ForeignKey("camere.id"))
    taxa_lunara = Column(Integer, nullable=False)
    status_plata = Column(String, nullable=False)
    data_cazarii = Column(DateTime, default=datetime.utcnow)

class CerereCazare(Base):
    __tablename__ = "cereri_cazare"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("studenti.id"))
    camin_preferat = Column(Integer, ForeignKey("camine.id"), nullable=True)
    data_cerere = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="in asteptare")
