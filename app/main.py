from fastapi import FastAPI 
# from config import settings 

app = FastAPI(title = "LLM Inference Gateway") 

@app.get("/") 
async def root(): 
    return {"message":"Hello, World!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}