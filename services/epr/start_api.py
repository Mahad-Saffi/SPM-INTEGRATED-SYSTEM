"""
Start the FastAPI server
"""
import uvicorn
from api.main import app

if __name__ == "__main__":
    print("Starting ScoreSquad Performance API on http://localhost:8003")
    print("API Documentation: http://localhost:8003/docs")
    uvicorn.run(app, host="0.0.0.0", port=8003)

