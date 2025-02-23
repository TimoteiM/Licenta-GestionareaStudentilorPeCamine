from pydantic import BaseModel

class StudentResponse(BaseModel):
    email: str
    role: str

class CazareResponse(BaseModel):
    student: dict
    cazare: dict
    
class UserRegister(BaseModel):
    email: str
    password: str
    role: str = "student"
    nume: str
    prenume: str
    telefon: str
    facultate: str
    specializare: str
    an_studiu: int
    grupa: str
    medie_anuala: float