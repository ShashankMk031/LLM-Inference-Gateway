from app.main import app

# Vercel looks for a variable named 'app' or 'handler'
# FastAPI app is ASGI, Vercel supports it natively via the Python runtime
