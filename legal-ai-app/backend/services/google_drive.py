import os
import json
import tempfile
from typing import List, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import fitz  # PyMuPDF
from config import settings

class GoogleDriveService:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        self.creds = None
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API."""
        if os.path.exists(settings.google_drive_credentials_file):
            self.creds = Credentials.from_authorized_user_file(
                settings.google_drive_credentials_file, self.SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets(
                    'client_secrets.json', self.SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(settings.google_drive_credentials_file, 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def download_file(self, file_id: str) -> bytes:
        """Download a file from Google Drive by ID."""
        try:
            request = self.service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            return file.getvalue()
        except Exception as e:
            print(f"Error downloading file {file_id}: {e}")
            return None
    
    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from Google Drive."""
        try:
            file = self.service.files().get(fileId=file_id).execute()
            return file
        except Exception as e:
            print(f"Error getting file info for {file_id}: {e}")
            return None
    
    def list_files_in_folder(self, folder_id: str) -> List[Dict[str, Any]]:
        """List all files in a Google Drive folder."""
        try:
            results = self.service.files().list(
                q=f"'{folder_id}' in parents",
                pageSize=1000,
                fields="nextPageToken, files(id, name, mimeType, size)"
            ).execute()
            
            return results.get('files', [])
        except Exception as e:
            print(f"Error listing files in folder {folder_id}: {e}")
            return []
    
    def download_legal_documents(self, file_id: str) -> List[Dict[str, Any]]:
        """Download and parse the legal documents JSON file."""
        print(f"Downloading legal documents from file ID: {file_id}")
        
        # Download the file
        file_content = self.download_file(file_id)
        if not file_content:
            print("Failed to download legal documents file")
            return []
        
        try:
            # Parse JSON content
            documents = json.loads(file_content.decode('utf-8'))
            print(f"Successfully loaded {len(documents)} legal documents")
            return documents
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error processing legal documents: {e}")
            return []
    
    def download_templates(self, folder_id: str) -> List[Dict[str, Any]]:
        """Download and parse PDF templates from the templates folder."""
        print(f"Downloading templates from folder ID: {folder_id}")
        
        templates = []
        files = self.list_files_in_folder(folder_id)
        
        for file in files:
            if file['mimeType'] == 'application/pdf':
                print(f"Processing template: {file['name']}")
                
                # Download PDF content
                pdf_content = self.download_file(file['id'])
                if pdf_content:
                    try:
                        # Extract text from PDF
                        pdf_text = self._extract_pdf_text(pdf_content)
                        
                        template = {
                            'name': file['name'].replace('.pdf', ''),
                            'content': pdf_text,
                            'file_id': file['id'],
                            'size': file.get('size', 0)
                        }
                        
                        templates.append(template)
                        print(f"Successfully processed template: {template['name']}")
                        
                    except Exception as e:
                        print(f"Error processing template {file['name']}: {e}")
                        continue
        
        print(f"Successfully processed {len(templates)} templates")
        return templates
    
    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text content from PDF bytes."""
        try:
            # Open PDF from bytes
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
            text = ""
            
            # Extract text from all pages
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                text += page.get_text()
            
            pdf_document.close()
            return text.strip()
            
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def get_document_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get document information from a Google Drive URL."""
        try:
            # Extract file ID from Google Drive URL
            if 'drive.google.com' in url:
                if '/file/d/' in url:
                    file_id = url.split('/file/d/')[1].split('/')[0]
                elif 'id=' in url:
                    file_id = url.split('id=')[1].split('&')[0]
                else:
                    print(f"Could not extract file ID from URL: {url}")
                    return None
                
                file_info = self.get_file_info(file_id)
                if file_info:
                    return {
                        'id': file_id,
                        'name': file_info.get('name', ''),
                        'mimeType': file_info.get('mimeType', ''),
                        'size': file_info.get('size', 0),
                        'url': url
                    }
            
            return None
            
        except Exception as e:
            print(f"Error getting document from URL {url}: {e}")
            return None

# Global instance
google_drive_service = GoogleDriveService()