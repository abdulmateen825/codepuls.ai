@'
from fastapi import FastAPI

app = FastAPI(title="CodePulse AI Engine")

@app.get("/health")
def health():
    return {"status": "ok"}
'@ | Set-Content app/main.py