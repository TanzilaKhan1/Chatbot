from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routers import folders, files, chat, health, sessions, debug
from routers.debug import router as debug_router

# Initialize FastAPI app
app = FastAPI(title="Folder File Management API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Folder File Management API"}

# Include routers
app.include_router(folders.router)
app.include_router(files.router)
app.include_router(chat.router)
app.include_router(health.router)
app.include_router(sessions.router)
app.include_router(debug_router)


@app.get("/")
async def root():
    return {"message": "AI Chat PDF API is running"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)