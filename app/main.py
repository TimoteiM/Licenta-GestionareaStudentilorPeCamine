from fastapi import FastAPI
from app.routers import auth, studenti, camine, admin, notificari
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuth2 as OAuth2Model
from fastapi.security import OAuth2PasswordBearer
app = FastAPI(
    title="Gestionare Camine USV",
    description="API pentru gestionarea studenților în cămine",
    version="1.0",
    openapi_tags=[{"name": "auth", "description": "Endpoints pentru autentificare"}],
    openapi_components={
        "securitySchemes": {
            "OAuth2PasswordBearer": OAuth2Model(
                flows=OAuthFlowsModel(password={"tokenUrl": "auth/token"})  # <-- Asigură-te că e "auth/token"
            )
        }
    }
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Înregistrăm rutele din fiecare fișier
app.include_router(auth.router)
app.include_router(studenti.router)
app.include_router(camine.router)
app.include_router(admin.router)
app.include_router(notificari.router)

@app.get("/")
def read_root():
    return {"message": "API Gestionare Camine - Universitatea USV"}
