from fastapi import FastAPI
from app.config.config import settings

app = FastAPI()

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}