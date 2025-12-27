from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import companies, contacts, deals, activities, dashboard

app = FastAPI(
    title="CRM API",
    version="0.1.0",
)
origins = [
    "http://localhost:4200",  # Angular dev
    "http://127.0.0.1:4200",
    "http://localhost:5173",  # por si usas Vite algún día
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, etc.
    allow_headers=["*"],            # Authorization, Content-Type, ...
)


app.include_router(companies.router)
app.include_router(contacts.router)
app.include_router(deals.router)
app.include_router(activities.router)
app.include_router(dashboard.router)
@app.get("/")
def read_root():
    return {"message": "CRM API up & running"}
