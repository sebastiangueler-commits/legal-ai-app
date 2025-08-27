import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import openai
import anthropic
from config import settings
from services.embeddings import embeddings_service
from services.classifier import classifier_service

class LegalDocumentGenerator:
    def __init__(self):
        self.templates = {}
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize AI clients
        self._initialize_ai_clients()
    
    def _initialize_ai_clients(self):
        """Initialize AI clients for document generation."""
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
            print("OpenAI client initialized")
        
        if settings.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            print("Anthropic client initialized")
        
        if not self.openai_client and not self.anthropic_client:
            print("Warning: No AI clients available. Document generation will be limited.")
    
    def load_templates(self, templates: List[Dict[str, Any]]):
        """Load document templates."""
        for template in templates:
            self.templates[template['name']] = {
                'content': template['content'],
                'document_type': template.get('document_type', ''),
                'structure': self._analyze_template_structure(template['content'])
            }
        
        print(f"Loaded {len(self.templates)} document templates")
    
    def _analyze_template_structure(self, template_content: str) -> Dict[str, Any]:
        """Analyze the structure of a document template."""
        structure = {
            'sections': [],
            'placeholders': [],
            'formatting': {}
        }
        
        # Identify common sections
        section_patterns = {
            'header': r'(?:ENCABEZADO|HEADER|TÍTULO|TITLE)',
            'introduction': r'(?:INTRODUCCIÓN|INTRODUCCION|INTRO)',
            'facts': r'(?:HECHOS|FACTS|ANTECEDENTES)',
            'legal_basis': r'(?:FUNDAMENTOS|LEGAL_BASIS|FUNDAMENTACIÓN)',
            'conclusion': r'(?:CONCLUSIÓN|CONCLUSION|CONCLUSIONES)',
            'signature': r'(?:FIRMA|SIGNATURE|SUSCRITO)'
        }
        
        for section_name, pattern in section_patterns.items():
            if re.search(pattern, template_content, re.IGNORECASE):
                structure['sections'].append(section_name)
        
        # Find placeholders
        placeholder_pattern = r'\{\{([^}]+)\}\}'
        placeholders = re.findall(placeholder_pattern, template_content)
        structure['placeholders'] = list(set(placeholders))
        
        # Detect formatting
        if re.search(r'<[^>]+>', template_content):
            structure['formatting']['html'] = True
        
        return structure
    
    def generate_document(self, template_name: str, case_details: Dict[str, Any], 
                         case_id: int = None) -> Dict[str, Any]:
        """Generate a legal document using a template and case details."""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        
        # Get similar cases for citations
        case_description = case_details.get('description', '')
        similar_cases = classifier_service.get_similar_cases(case_description, k=3)
        
        # Generate document content
        generated_content = self._fill_template(template, case_details, similar_cases)
        
        # Enhance with AI if available
        if self.openai_client or self.anthropic_client:
            enhanced_content = self._enhance_with_ai(generated_content, case_details, similar_cases)
        else:
            enhanced_content = generated_content
        
        return {
            'generated_document': enhanced_content,
            'template_used': template_name,
            'citations': [case['expediente'] for case in similar_cases],
            'similar_cases': similar_cases,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _fill_template(self, template: Dict[str, Any], case_details: Dict[str, Any], 
                      similar_cases: List[Dict[str, Any]]) -> str:
        """Fill template with case details."""
        content = template['content']
        
        # Replace basic placeholders
        replacements = {
            '{{FECHA}}': datetime.now().strftime('%d/%m/%Y'),
            '{{FECHA_ACTUAL}}': datetime.now().strftime('%d de %B de %Y'),
            '{{CASO_NUMERO}}': case_details.get('case_number', ''),
            '{{TITULO_CASO}}': case_details.get('title', ''),
            '{{DESCRIPCION_CASO}}': case_details.get('description', ''),
            '{{TIPO_CASO}}': case_details.get('case_type', ''),
            '{{PARTES}}': case_details.get('parties', ''),
            '{{TRIBUNAL}}': case_details.get('tribunal', ''),
            '{{MATERIA}}': case_details.get('matter', ''),
            '{{ABOGADO}}': case_details.get('lawyer', ''),
            '{{CLIENTE}}': case_details.get('client', '')
        }
        
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))
        
        # Add citations section if similar cases exist
        if similar_cases:
            citations_text = self._format_citations(similar_cases)
            content = content.replace('{{CITACIONES}}', citations_text)
        
        return content
    
    def _format_citations(self, similar_cases: List[Dict[str, Any]]) -> str:
        """Format similar cases as legal citations."""
        citations = []
        
        for case in similar_cases:
            citation = f"{case['tribunal']}, {case['fecha']}, {case['materia']}, {case['partes']}, Expediente {case['expediente']}"
            citations.append(citation)
        
        return "\n".join([f"- {citation}" for citation in citations])
    
    def _enhance_with_ai(self, base_content: str, case_details: Dict[str, Any], 
                         similar_cases: List[Dict[str, Any]]) -> str:
        """Enhance document content using AI."""
        try:
            # Prepare context for AI
            context = f"""
            Tipo de documento: {case_details.get('document_type', '')}
            Descripción del caso: {case_details.get('description', '')}
            Tipo de caso: {case_details.get('case_type', '')}
            
            Casos similares para referencia:
            {json.dumps(similar_cases, indent=2, default=str)}
            
            Documento base:
            {base_content}
            """
            
            # Try OpenAI first, then Anthropic
            if self.openai_client:
                enhanced_content = self._enhance_with_openai(context, case_details)
            elif self.anthropic_client:
                enhanced_content = self._enhance_with_anthropic(context, case_details)
            else:
                enhanced_content = base_content
                
            return enhanced_content
            
        except Exception as e:
            print(f"Error enhancing document with AI: {e}")
            return base_content
    
    def _enhance_with_openai(self, context: str, case_details: Dict[str, Any]) -> str:
        """Enhance document using OpenAI."""
        try:
            prompt = f"""
            Eres un abogado experto. Mejora el siguiente documento legal basándote en el contexto proporcionado.
            
            Contexto:
            {context}
            
            Instrucciones:
            1. Mantén la estructura legal del documento
            2. Mejora la redacción y claridad
            3. Incorpora referencias a los casos similares cuando sea apropiado
            4. Asegúrate de que el documento sea profesional y técnicamente correcto
            5. Mantén el formato original
            
            Documento mejorado:
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un abogado experto especializado en redacción de documentos legales."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error with OpenAI enhancement: {e}")
            return context.split("Documento base:")[-1].strip()
    
    def _enhance_with_anthropic(self, context: str, case_details: Dict[str, Any]) -> str:
        """Enhance document using Anthropic Claude."""
        try:
            prompt = f"""
            Eres un abogado experto. Mejora el siguiente documento legal basándote en el contexto proporcionado.
            
            Contexto:
            {context}
            
            Instrucciones:
            1. Mantén la estructura legal del documento
            2. Mejora la redacción y claridad
            3. Incorpora referencias a los casos similares cuando sea apropiado
            4. Asegúrate de que el documento sea profesional y técnicamente correcto
            5. Mantén el formato original
            
            Documento mejorado:
            """
            
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"Error with Anthropic enhancement: {e}")
            return context.split("Documento base:")[-1].strip()
    
    def generate_summary(self, document_content: str, summary_type: str = "technical") -> str:
        """Generate a summary of a legal document."""
        if not (self.openai_client or self.anthropic_client):
            return self._generate_basic_summary(document_content, summary_type)
        
        try:
            if summary_type == "technical":
                instruction = "Genera un resumen técnico jurídico del documento, destacando los puntos legales más importantes."
            else:  # citizen
                instruction = "Genera un resumen en lenguaje claro y comprensible para un ciudadano común, explicando los puntos principales del caso."
            
            prompt = f"""
            {instruction}
            
            Documento:
            {document_content[:3000]}  # Limit content length
            
            Resumen:
            """
            
            if self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Eres un experto en análisis legal y comunicación jurídica."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            
            elif self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=500,
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text.strip()
                
        except Exception as e:
            print(f"Error generating AI summary: {e}")
            return self._generate_basic_summary(document_content, summary_type)
    
    def _generate_basic_summary(self, document_content: str, summary_type: str) -> str:
        """Generate a basic summary without AI."""
        # Simple text summarization
        sentences = re.split(r'[.!?]+', document_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if summary_type == "technical":
            # Focus on legal terms and structure
            legal_keywords = ['tribunal', 'juez', 'sentencia', 'fallo', 'recurso', 'apelación', 'materia', 'partes']
            relevant_sentences = [s for s in sentences if any(keyword in s.lower() for keyword in legal_keywords)]
        else:
            # Focus on clear, simple sentences
            relevant_sentences = [s for s in sentences if len(s.split()) < 25]
        
        # Take first few relevant sentences
        summary_sentences = relevant_sentences[:5]
        return ". ".join(summary_sentences) + "."
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available document templates."""
        return [
            {
                'name': name,
                'document_type': template['document_type'],
                'structure': template['structure']
            }
            for name, template in self.templates.items()
        ]
    
    def create_custom_template(self, name: str, content: str, document_type: str) -> bool:
        """Create a custom document template."""
        try:
            self.templates[name] = {
                'content': content,
                'document_type': document_type,
                'structure': self._analyze_template_structure(content)
            }
            print(f"Custom template '{name}' created successfully")
            return True
        except Exception as e:
            print(f"Error creating custom template: {e}")
            return False

# Global instance
document_generator = LegalDocumentGenerator()