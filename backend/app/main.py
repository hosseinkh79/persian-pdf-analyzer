from fastapi import FastAPI

app = FastAPI()

@app.get('/')
def test_app():
    return "Hello Hossein"

@app.get("/health")
def health_check():
    return {"status": "ok"}