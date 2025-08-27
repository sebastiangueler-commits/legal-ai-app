from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import uvicorn

from config import settings
from models.database import create_tables
from routers import auth, analysis, search, documents, cases, data_sync

# Create FastAPI app
app = FastAPI(
    title="Legal AI Assistant",
    description="Intelligent legal document analysis and generation system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
app.include_router(cases.router, prefix="/api/v1")
app.include_router(data_sync.router, prefix="/api/v1")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Legal AI Assistant",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic information."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Legal AI Assistant</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .endpoint { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { font-weight: bold; color: #e74c3c; }
            .url { font-family: monospace; color: #2980b9; }
            .description { color: #7f8c8d; margin-top: 5px; }
            .docs-link { text-align: center; margin-top: 30px; }
            .docs-link a { background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Legal AI Assistant</h1>
            <p>Welcome to the Legal AI Assistant API. This system provides intelligent analysis of legal documents, case outcome prediction, and automated document generation.</p>
            
            <h2>📚 Available Endpoints</h2>
            
            <div class="endpoint">
                <div class="method">GET</div>
                <div class="url">/health</div>
                <div class="description">Health check endpoint</div>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div>
                <div class="url">/api/v1/auth/register</div>
                <div class="description">User registration</div>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div>
                <div class="url">/api/v1/auth/token</div>
                <div class="description">User authentication</div>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div>
                <div class="url">/api/v1/analysis/predict</div>
                <div class="description">Predict case outcome using AI</div>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div>
                <div class="url">/api/v1/search/query</div>
                <div class="description">Search legal documents</div>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div>
                <div class="url">/api/v1/documents/generate</div>
                <div class="description">Generate legal documents</div>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div>
                <div class="url">/api/v1/cases/</div>
                <div class="description">Create legal cases</div>
            </div>
            
            <div class="endpoint">
                <div class="method">POST</div>
                <div class="url">/api/v1/data-sync/sync-legal-documents</div>
                <div class="description">Sync legal documents from Google Drive</div>
            </div>
            
            <div class="docs-link">
                <a href="/docs">📖 View Full API Documentation</a>
            </div>
            
            <h2>🚀 Getting Started</h2>
            <ol>
                <li>Register a new user account</li>
                <li>Authenticate to get an access token</li>
                <li>Sync your legal documents from Google Drive</li>
                <li>Start analyzing cases and generating documents</li>
            </ol>
            
            <h2>🔧 Features</h2>
            <ul>
                <li><strong>AI-Powered Analysis:</strong> Predict case outcomes using machine learning</li>
                <li><strong>Smart Search:</strong> Find similar legal cases using vector similarity</li>
                <li><strong>Document Generation:</strong> Create legal documents from templates</li>
                <li><strong>Case Management:</strong> Organize and track legal cases</li>
                <li><strong>Google Drive Integration:</strong> Sync documents and templates</li>
            </ul>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("🚀 Starting Legal AI Assistant...")
    
    try:
        # Create database tables
        create_tables()
        print("✅ Database tables created/verified")
        
        # Create necessary directories
        os.makedirs("ml_models", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        print("✅ Directories created")
        
        print("🎉 Legal AI Assistant started successfully!")
        
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        raise e

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    print("🛑 Shutting down Legal AI Assistant...")

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "path": str(request.url.path)
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "path": str(request.url.path)
    }

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )