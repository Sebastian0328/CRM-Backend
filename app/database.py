from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# ⚠ Si cambiaste usuario/contraseña, cámbialo aquí:
DB_USER = "crm_user" # USUARIO DE LA BASE DE DATOS 
DB_PASSWORD = "crmPassword123!" # CONTRASEÑA DE LA BBDD
DB_HOST = "localhost" #~HOST 
DB_NAME = "crm_db" #NOMBRE BASE DE DATOS 

DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"  # CREAMOS EL CONECTOR PARA LLAMAR LA BBDD
)

engine = create_engine(
    DATABASE_URL,
    echo=True,          # Muestra SQL en consola (útil para depurar)
    pool_pre_ping=True  # Evita conexiones muertas
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency para FastAPI: abre/cierra sesión con la DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
