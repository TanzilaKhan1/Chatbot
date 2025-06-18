from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routers import folders, files, chat, health, sessions

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