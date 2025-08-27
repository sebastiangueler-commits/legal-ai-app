#!/usr/bin/env python3
"""
Data synchronization script for Legal AI Assistant.
This script syncs legal documents and templates from Google Drive.
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.google_drive import google_drive_service
from services.embeddings import embeddings_service
from services.classifier import classifier_service
from services.document_generator import document_generator
from config import settings

# Google Drive IDs from your links
LEGAL_DOCUMENTS_FILE_ID = "1yNAwckn4rPnlpSgmW-xyB10WL4CcgRvE"  # From your JSON link
TEMPLATES_FOLDER_ID = "1hzAIv5AJWGI8Q76M4IjI0k4ZFXw8UBeu"      # From your templates folder

async def sync_legal_documents():
    """Sync legal documents from Google Drive."""
    print("📚 Syncing legal documents from Google Drive...")
    
    try:
        # Download legal documents
        documents = google_drive_service.download_legal_documents(LEGAL_DOCUMENTS_FILE_ID)
        
        if not documents:
            print("❌ No documents found or error downloading")
            return False
        
        print(f"✅ Downloaded {len(documents)} legal documents")
        
        # Update embeddings index
        print("🔍 Updating embeddings index...")
        embeddings_service.update_index(documents)
        
        print("✅ Legal documents synced successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing legal documents: {e}")
        return False

async def sync_templates():
    """Sync document templates from Google Drive."""
    print("📋 Syncing document templates from Google Drive...")
    
    try:
        # Download templates
        templates = google_drive_service.download_templates(TEMPLATES_FOLDER_ID)
        
        if not templates:
            print("❌ No templates found or error downloading")
            return False
        
        print(f"✅ Downloaded {len(templates)} templates")
        
        # Load templates into document generator
        document_generator.load_templates(templates)
        
        print("✅ Templates synced successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing templates: {e}")
        return False

async def train_ml_models():
    """Train the ML models with synced data."""
    print("🤖 Training ML models...")
    
    try:
        if not embeddings_service.documents:
            print("❌ No documents available for training")
            return False
        
        # Train classifier
        success = classifier_service.train_classifier(embeddings_service.documents)
        
        if success:
            print("✅ ML models trained successfully")
            return True
        else:
            print("❌ Failed to train ML models")
            return False
            
    except Exception as e:
        print(f"❌ Error training ML models: {e}")
        return False

async def show_system_status():
    """Show the current system status."""
    print("\n📊 System Status:")
    print(f"   Legal documents indexed: {len(embeddings_service.documents) if embeddings_service.documents else 0}")
    print(f"   Search index available: {'✅' if embeddings_service.faiss_index else '❌'}")
    print(f"   Templates loaded: {len(document_generator.templates)}")
    print(f"   Classifier trained: {'✅' if classifier_service.is_trained else '❌'}")
    print(f"   Google Drive service: {'✅' if google_drive_service.service else '❌'}")

async def main():
    """Main synchronization function."""
    print("=" * 60)
    print("🤖 Legal AI Assistant - Data Synchronization")
    print("=" * 60)
    
    # Check Google Drive authentication
    if not google_drive_service.service:
        print("❌ Google Drive service not available. Please check your credentials.")
        return
    
    print("✅ Google Drive service authenticated")
    
    # Sync legal documents
    docs_synced = await sync_legal_documents()
    
    # Sync templates
    templates_synced = await sync_templates()
    
    # Train models if documents are available
    models_trained = False
    if docs_synced:
        models_trained = await train_ml_models()
    
    # Show final status
    await show_system_status()
    
    print("\n" + "=" * 60)
    if docs_synced and templates_synced:
        print("🎉 Data synchronization completed successfully!")
        if models_trained:
            print("🤖 ML models are ready for use!")
        else:
            print("⚠️  ML models training failed or not completed")
    else:
        print("⚠️  Data synchronization completed with some issues")
        if not docs_synced:
            print("   - Legal documents sync failed")
        if not templates_synced:
            print("   - Templates sync failed")
    
    print("\n🚀 You can now start the application with:")
    print("   uvicorn main:app --reload")
    print("=" * 60)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())