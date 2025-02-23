from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Student, Camin, Camera
import random

session = SessionLocal()

# Liste de nume și prenume
nume_lista = ["Popescu", "Ionescu", "Georgescu", "Dumitru", "Stoica", "Marinescu", "Vasilescu", "Dobre", "Stan", "Munteanu", "Lungu", "Grigorescu"]
prenume_lista = ["Andrei", "Maria", "Elena", "Alexandru", "Cristina", "Mihai", "Gabriel", "Florin", "Daniela", "Ioana", "Robert", "Bianca"]

# Liste de facultăți și specializări
facultati = [
    ("Facultatea de Informatica", ["Informatica Aplicata", "Tehnologii Web", "Inteligenta Artificiala"]),
    ("Facultatea de Inginerie", ["Inginerie Electrica", "Mecatronica", "Automatica"]),
    ("Facultatea de Medicina", ["Medicina Generala", "Asistenta Medicala", "Farmacie"]),
    ("Facultatea de Economie", ["Finante si Banci", "Marketing", "Management"])
]

# Generăm 100 de studenți
for i in range(40):
    nume = random.choice(nume_lista)
    prenume = random.choice(prenume_lista)
    email = f"{prenume.lower()}.{nume.lower()}{i}@usv.ro"
    telefon = f"+40{random.randint(700000000, 799999999)}"
    facultate, specializari = random.choice(facultati)
    specializare = random.choice(specializari)
    an_studiu = random.randint(1, 3)
    grupa = f"3{an_studiu}{random.randint(1, 3)}{random.choice(['a', 'b', 'c'])}"
    medie_anuala = round(random.uniform(6, 10), 2)

    student = Student(
        nume=nume, prenume=prenume, email=email, telefon=telefon,
        facultate=facultate, specializare=specializare,
        an_studiu=an_studiu, grupa=grupa, medie_anuala=medie_anuala
    )
    session.add(student)

# Generăm cămine
camine = [
    Camin(nume="Camin A", adresa="Str. Universitatii 1", capacitate_totala=100),
    Camin(nume="Camin B", adresa="Str. Universitatii 2", capacitate_totala=120),
    Camin(nume="Camin C", adresa="Str. Universitatii 3", capacitate_totala=80),
]
session.add_all(camine)
session.commit()

# Generăm camere pentru fiecare cămin
for camin in session.query(Camin).all():
    for i in range(1, camin.capacitate_totala // 2 + 1):
        camera = Camera(camin_id=camin.id, numar_camera=f"{random.randint(100, 500)}", locuri_disponibile=random.randint(1, 4))
        session.add(camera)

session.commit()
session.close()
print("✅ Date generate cu succes!")
