from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

new_hash = pwd_context.hash("password123")
print(f"🔑 Hash nou generat: {new_hash}")
