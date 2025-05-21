from fastapi import FastAPI

app: FastAPI = FastAPI()

@app.get("/")
def get_root():
    return {"Backend is running"}