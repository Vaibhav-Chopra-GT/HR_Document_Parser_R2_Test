# TraqCheck - Resume Parser & Document Collection System

## 📋 Project Overview

A full-stack AI-powered system for HR teams to:
1. Upload and parse resumes automatically
2. Extract candidate information with confidence scores
3. Send personalized document requests via email
4. Collect PAN & Aadhaar documents securely through a candidate portal

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              HR DASHBOARD                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Upload    │  │  Candidate  │  │   Profile   │  │  Document   │        │
│  │   Resume    │  │    Table    │  │    View     │  │   Viewer    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FLASK BACKEND API                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Resume Parser   │  │    AI Agent      │  │   Email Service  │          │
│  │  (Claude API)    │  │   (LangChain)    │  │    (Resend)      │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  Document        │  │   Audit Logger   │  │  Token Generator │          │
│  │  Validator       │  │                  │  │  (Secure Links)  │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │  SQLite DB  │ │ File Store  │ │ Audit Logs  │
            │  (encrypted │ │ (encrypted) │ │   (JSON)    │
            │   fields)   │ │             │ │             │
            └─────────────┘ └─────────────┘ └─────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         CANDIDATE PORTAL                                     │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │   Secure Link → Verify Token → Upload PAN/Aadhaar → Confirm     │        │
│  └─────────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
traqcheck_test/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Flask app factory
│   │   ├── config.py                # Configuration (env-based)
│   │   ├── models.py                # SQLAlchemy models
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── candidates.py        # HR-facing endpoints
│   │   │   └── portal.py            # Candidate portal endpoints
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── resume_parser.py     # PDF/DOCX parsing + Claude extraction
│   │   │   ├── ai_agent.py          # LangChain agent for personalized messages
│   │   │   ├── email_service.py     # Resend email automation
│   │   │   ├── document_validator.py # PAN/Aadhaar validation
│   │   │   └── audit_logger.py      # Compliance audit trail
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_handler.py      # Secure file operations
│   │       ├── encryption.py        # Field-level encryption
│   │       └── token_generator.py   # Secure link tokens
│   ├── uploads/                     # Encrypted file storage
│   │   ├── resumes/
│   │   └── documents/
│   ├── logs/                        # Audit logs
│   ├── tests/
│   │   ├── test_resume_parser.py
│   │   ├── test_validators.py
│   │   └── test_api.py
│   ├── requirements.txt
│   ├── run.py
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                  # Reusable UI components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Table.tsx
│   │   │   │   ├── Badge.tsx
│   │   │   │   └── Progress.tsx
│   │   │   ├── ResumeUploader.tsx   # Drag-drop with progress
│   │   │   ├── CandidateTable.tsx   # Dashboard table
│   │   │   ├── CandidateProfile.tsx # Profile with confidence scores
│   │   │   ├── DocumentSection.tsx  # View submitted docs
│   │   │   ├── ConfidenceBar.tsx    # Visual confidence indicator
│   │   │   └── AuditLog.tsx         # Activity timeline
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx        # Main HR dashboard
│   │   │   ├── CandidateDetail.tsx  # Individual candidate view
│   │   │   └── portal/
│   │   │       └── SubmitDocuments.tsx  # Candidate submission page
│   │   ├── api/
│   │   │   └── client.ts            # Axios API client
│   │   ├── hooks/
│   │   │   ├── useCandidates.ts
│   │   │   └── useUpload.ts
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── plan.md                          # This file
├── README.md                        # Setup & usage instructions
├── .gitignore
└── docker-compose.yml               # Optional containerization
```

---

## 📊 Database Schema

```sql
-- Candidates table
CREATE TABLE candidates (
    id TEXT PRIMARY KEY,                    -- UUID
    
    -- Extracted Information (encrypted at rest)
    name TEXT,
    email TEXT,
    phone TEXT,
    company TEXT,
    designation TEXT,
    skills TEXT,                            -- JSON array
    raw_resume_text TEXT,                   -- For re-processing if needed
    
    -- Confidence Scores (0.0 - 1.0)
    name_confidence REAL,
    email_confidence REAL,
    phone_confidence REAL,
    company_confidence REAL,
    designation_confidence REAL,
    skills_confidence REAL,
    overall_confidence REAL,                -- Weighted average
    
    -- File References (paths, not actual files)
    resume_filename TEXT,
    resume_original_name TEXT,
    pan_filename TEXT,
    pan_original_name TEXT,
    aadhaar_filename TEXT,
    aadhaar_original_name TEXT,
    
    -- Document Validation
    pan_number_hash TEXT,                   -- Hashed PAN for dedup check
    pan_validated BOOLEAN DEFAULT FALSE,
    aadhaar_validated BOOLEAN DEFAULT FALSE,
    
    -- Status Tracking
    extraction_status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    extraction_error TEXT,                     -- Error message if failed
    document_status TEXT DEFAULT 'pending',    -- pending, requested, partial, completed
    
    -- Secure Portal Access
    submission_token TEXT UNIQUE,           -- For candidate portal link
    token_expires_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    documents_requested_at TIMESTAMP,
    documents_submitted_at TIMESTAMP
);

-- Audit Log table (immutable append-only)
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT,
    action TEXT NOT NULL,                   -- upload, extract, request_docs, submit_docs, view, etc.
    actor TEXT,                             -- 'system', 'hr', 'candidate'
    actor_ip TEXT,
    details TEXT,                           -- JSON with action-specific details
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);

-- Email Log table
CREATE TABLE email_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    email_type TEXT NOT NULL,               -- document_request, reminder, confirmation
    recipient_email TEXT NOT NULL,
    subject TEXT,
    body_preview TEXT,                      -- First 200 chars
    status TEXT DEFAULT 'pending',          -- pending, sent, delivered, failed, bounced
    resend_message_id TEXT,                 -- From Resend API
    sent_at TIMESTAMP,
    error_message TEXT,
    
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);

-- Indexes for performance
CREATE INDEX idx_candidates_email ON candidates(email);
CREATE INDEX idx_candidates_status ON candidates(extraction_status, document_status);
CREATE INDEX idx_candidates_token ON candidates(submission_token);
CREATE INDEX idx_audit_candidate ON audit_logs(candidate_id);
CREATE INDEX idx_audit_created ON audit_logs(created_at);
```

---

## 🔌 API Endpoints

### HR Dashboard Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/candidates/upload` | Upload resume (PDF/DOCX), triggers extraction |
| `GET` | `/api/candidates` | List all candidates with pagination & filters |
| `GET` | `/api/candidates/<id>` | Get candidate profile with all extracted data |
| `POST` | `/api/candidates/<id>/request-documents` | Generate & send document request email |
| `GET` | `/api/candidates/<id>/audit-log` | Get audit trail for candidate |
| `DELETE` | `/api/candidates/<id>` | Soft delete candidate (GDPR compliance) |

### Candidate Portal Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/portal/<token>` | Validate token, return candidate info (name only) |
| `POST` | `/api/portal/<token>/submit` | Upload PAN and/or Aadhaar documents |
| `GET` | `/api/portal/<token>/status` | Check submission status |

### Internal/Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/candidates/<id>/reprocess` | Re-run extraction on existing resume |

---

## 🤖 AI Components (Provider-Agnostic)

### AI Service Abstraction

The system supports **both OpenAI and Claude** via a unified interface. Switch providers with a single environment variable.

```python
# .env configuration
AI_PROVIDER=openai          # or "claude"
OPENAI_API_KEY=sk-...       # if using OpenAI
ANTHROPIC_API_KEY=sk-ant-... # if using Claude
```

### AI Service Factory

```python
# services/ai_service.py
from abc import ABC, abstractmethod
import os

class AIService(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def extract_resume_data(self, text: str) -> dict:
        pass
    
    @abstractmethod
    async def generate_document_request(self, candidate_data: dict) -> str:
        pass


class OpenAIService(AIService):
    """OpenAI GPT-4 implementation"""
    
    def __init__(self):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.model = "gpt-4o"  # or "gpt-4o-mini" for cost savings
    
    async def extract_resume_data(self, text: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Resume text:\n{text}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    
    async def generate_document_request(self, candidate_data: dict) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": DOCUMENT_REQUEST_SYSTEM_PROMPT},
                {"role": "user", "content": format_candidate_prompt(candidate_data)}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content


class ClaudeService(AIService):
    """Anthropic Claude implementation"""
    
    def __init__(self):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
        self.model = "claude-sonnet-4-20250514"  # or "claude-haiku-4-5-20251001" for cost savings
    
    async def extract_resume_data(self, text: str) -> dict:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {"role": "user", "content": f"{EXTRACTION_SYSTEM_PROMPT}\n\nResume text:\n{text}"}
            ]
        )
        # Parse JSON from response
        return json.loads(response.content[0].text)
    
    async def generate_document_request(self, candidate_data: dict) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=DOCUMENT_REQUEST_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": format_candidate_prompt(candidate_data)}
            ]
        )
        return response.content[0].text


def get_ai_service() -> AIService:
    """Factory function to get configured AI service"""
    provider = os.environ.get('AI_PROVIDER', 'openai').lower()
    
    if provider == 'claude':
        return ClaudeService()
    elif provider == 'openai':
        return OpenAIService()
    else:
        raise ValueError(f"Unknown AI provider: {provider}")
```

### Shared Prompts (Work with Both Providers)

```python
# services/prompts.py

EXTRACTION_SYSTEM_PROMPT = """You are an expert HR data extraction system. 
Extract candidate information from resumes with high accuracy.

For each field, provide:
1. The extracted value (or null if not found)
2. A confidence score (0.0-1.0) based on clarity and pattern matching

Return a JSON object with this exact structure:
{
    "name": {"value": "...", "confidence": 0.0},
    "email": {"value": "...", "confidence": 0.0},
    "phone": {"value": "...", "confidence": 0.0},
    "company": {"value": "...", "confidence": 0.0},
    "designation": {"value": "...", "confidence": 0.0},
    "skills": {"value": ["skill1", "skill2"], "confidence": 0.0}
}

Confidence guidelines:
- 0.9-1.0: Clearly stated, unambiguous, matches expected format
- 0.7-0.9: Present but slightly ambiguous or informal format  
- 0.5-0.7: Inferred from context, not explicitly stated
- 0.0-0.5: Guessed or very uncertain
- null value: Not found at all

Extract the MOST RECENT company and designation. For skills, extract technical 
and professional skills mentioned anywhere in the resume."""


DOCUMENT_REQUEST_SYSTEM_PROMPT = """You are a professional HR communication assistant for TraqCheck.

Write personalized emails requesting identity documents (PAN and Aadhaar) from candidates.

Your emails should be:
- Professional yet warm and welcoming
- Personalized using the candidate's name, company, and role
- Clear about what documents are needed (PAN card, Aadhaar card)
- Include the provided secure submission link
- Mention data security and privacy assurance
- Concise (under 200 words)

Format your response as:
Subject: [subject line]
---
[email body]"""


def format_candidate_prompt(candidate_data: dict) -> str:
    return f"""Write a document request email for this candidate:

Name: {candidate_data['name']}
Company: {candidate_data['company']}
Designation: {candidate_data['designation']}
Submission Link: {candidate_data['submission_link']}

Request both PAN card and Aadhaar card for employment verification."""
```

### LangChain Integration (Also Provider-Agnostic)

```python
# services/ai_agent.py
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableSequence
import os

def get_langchain_llm():
    """Get LangChain LLM based on configured provider"""
    provider = os.environ.get('AI_PROVIDER', 'openai').lower()
    
    if provider == 'claude':
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.environ.get('ANTHROPIC_API_KEY')
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o",
            api_key=os.environ.get('OPENAI_API_KEY')
        )

# Create the agent chain
prompt = ChatPromptTemplate.from_messages([
    ("system", DOCUMENT_REQUEST_SYSTEM_PROMPT),
    ("human", "{input}")
])

def create_document_request_chain():
    llm = get_langchain_llm()
    return prompt | llm
```

### Cost Comparison

| Provider | Model | Input (1K tokens) | Output (1K tokens) | Best For |
|----------|-------|-------------------|--------------------| ---------|
| OpenAI | gpt-4o | $2.50 | $10.00 | High accuracy |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 | Cost-effective |
| Claude | claude-sonnet-4-20250514 | $3.00 | $15.00 | Structured extraction |
| Claude | claude-haiku-4-5-20251001 | $0.80 | $4.00 | Fast & cheap |

**Recommendation:** Start with `gpt-4o-mini` or `claude-haiku-4-5-20251001` for development, switch to larger models for production if needed.
```

**Example Output:**
```
Subject: Document Submission Required - TraqCheck Verification

Dear Rahul,

Congratulations on your journey with Infosys as a Senior Software Engineer! 

As part of our standard verification process, we kindly request you to submit the following identity documents:

📋 Documents Required:
1. PAN Card (front side)
2. Aadhaar Card (front and back)

🔒 Secure Submission:
Please use this secure, personalized link to upload your documents:
https://traqcheck.app/submit/abc123xyz

This link is valid for 7 days and can only be used once.

Your documents are encrypted and handled in compliance with data protection regulations. 
They will only be used for verification purposes.

If you have any questions, please don't hesitate to reach out.

Best regards,
TraqCheck Verification Team
```

---

## 📧 Email Automation (Resend)

### Why Resend?
- Modern API, easy to integrate
- Free tier: 3,000 emails/month
- Good deliverability
- Webhook support for delivery tracking

### Integration:
```python
# services/email_service.py
import resend
from app.config import Config

resend.api_key = Config.RESEND_API_KEY

async def send_document_request(candidate, message_content):
    """Send document request email via Resend"""
    
    subject, body = message_content.split('---', 1)
    
    response = resend.Emails.send({
        "from": "TraqCheck <verify@traqcheck.app>",
        "to": candidate.email,
        "subject": subject.strip(),
        "html": format_html_email(body.strip()),
        "tags": [
            {"name": "type", "value": "document_request"},
            {"name": "candidate_id", "value": candidate.id}
        ]
    })
    
    # Log to database
    log_email(candidate.id, "document_request", response)
    
    return response
```

### Email Templates:
1. **Document Request** - Initial request with secure link
2. **Reminder** - Follow-up after 3 days if not submitted
3. **Confirmation** - Thank you after successful submission

---

## 🔐 Security & Compliance

### 1. Data Encryption

**At Rest:**
```python
# utils/encryption.py
from cryptography.fernet import Fernet
import os

class FieldEncryption:
    def __init__(self):
        key = os.environ.get('ENCRYPTION_KEY')
        self.cipher = Fernet(key)
    
    def encrypt(self, value: str) -> str:
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted: str) -> str:
        return self.cipher.decrypt(encrypted.encode()).decode()

# Encrypt sensitive fields before storing
# - PAN number (if extracted)
# - Aadhaar number (if extracted)
# - Phone number
# - Document file contents
```

**In Transit:**
- HTTPS everywhere (enforced by deployment platform)
- Secure file upload with signed URLs

### 2. PAN & Aadhaar Validation

```python
# services/document_validator.py
import re

class PANValidator:
    """
    PAN Format: AAAAA9999A
    - First 5: Letters (A-Z)
    - Next 4: Digits (0-9)
    - Last 1: Letter (A-Z)
    - 4th character indicates holder type:
      C=Company, P=Person, H=HUF, F=Firm, A=AOP, T=Trust, etc.
    """
    PATTERN = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
    
    @staticmethod
    def validate(pan: str) -> dict:
        pan = pan.upper().strip()
        
        if not re.match(PANValidator.PATTERN, pan):
            return {"valid": False, "error": "Invalid PAN format"}
        
        # 4th character check
        holder_types = {'C': 'Company', 'P': 'Person', 'H': 'HUF', 
                       'F': 'Firm', 'A': 'AOP', 'T': 'Trust'}
        holder_type = holder_types.get(pan[3], 'Other')
        
        return {
            "valid": True,
            "pan": pan,
            "holder_type": holder_type
        }


class AadhaarValidator:
    """
    Aadhaar Format: 12 digits with Verhoeff checksum
    """
    
    # Verhoeff tables
    MULTIPLICATION_TABLE = [
        [0,1,2,3,4,5,6,7,8,9],
        [1,2,3,4,0,6,7,8,9,5],
        [2,3,4,0,1,7,8,9,5,6],
        [3,4,0,1,2,8,9,5,6,7],
        [4,0,1,2,3,9,5,6,7,8],
        [5,9,8,7,6,0,4,3,2,1],
        [6,5,9,8,7,1,0,4,3,2],
        [7,6,5,9,8,2,1,0,4,3],
        [8,7,6,5,9,3,2,1,0,4],
        [9,8,7,6,5,4,3,2,1,0]
    ]
    
    PERMUTATION_TABLE = [
        [0,1,2,3,4,5,6,7,8,9],
        [1,5,7,6,2,8,3,0,9,4],
        [5,8,0,3,7,9,6,1,4,2],
        [8,9,1,6,0,4,3,5,2,7],
        [9,4,5,3,1,2,6,8,7,0],
        [4,2,8,6,5,7,3,9,0,1],
        [2,7,9,3,8,0,6,4,1,5],
        [7,0,4,6,9,1,3,2,5,8]
    ]
    
    @staticmethod
    def validate(aadhaar: str) -> dict:
        # Remove spaces and hyphens
        aadhaar = re.sub(r'[\s-]', '', aadhaar)
        
        if not re.match(r'^\d{12}$', aadhaar):
            return {"valid": False, "error": "Aadhaar must be 12 digits"}
        
        # Verhoeff checksum validation
        if not AadhaarValidator._verhoeff_check(aadhaar):
            return {"valid": False, "error": "Invalid Aadhaar checksum"}
        
        # Mask for display (show only last 4)
        masked = f"XXXX-XXXX-{aadhaar[-4:]}"
        
        return {
            "valid": True,
            "masked": masked
        }
    
    @staticmethod
    def _verhoeff_check(num: str) -> bool:
        c = 0
        for i, digit in enumerate(reversed(num)):
            c = AadhaarValidator.MULTIPLICATION_TABLE[c][
                AadhaarValidator.PERMUTATION_TABLE[i % 8][int(digit)]
            ]
        return c == 0
```

### 3. Secure Token Generation

```python
# utils/token_generator.py
import secrets
import hashlib
from datetime import datetime, timedelta

def generate_submission_token() -> tuple[str, datetime]:
    """Generate a secure, time-limited token for candidate portal"""
    token = secrets.token_urlsafe(32)  # 256-bit token
    expires_at = datetime.utcnow() + timedelta(days=7)
    return token, expires_at

def verify_token(token: str, stored_token: str, expires_at: datetime) -> bool:
    """Verify token validity"""
    if datetime.utcnow() > expires_at:
        return False
    return secrets.compare_digest(token, stored_token)
```

### 4. Audit Logging

```python
# services/audit_logger.py
from datetime import datetime
from app.models import AuditLog, db

class AuditLogger:
    @staticmethod
    def log(candidate_id: str, action: str, actor: str, 
            details: dict = None, ip_address: str = None):
        """Create immutable audit log entry"""
        
        log_entry = AuditLog(
            candidate_id=candidate_id,
            action=action,
            actor=actor,
            actor_ip=ip_address,
            details=json.dumps(details) if details else None,
            created_at=datetime.utcnow()
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return log_entry

# Usage examples:
# AuditLogger.log(candidate.id, "resume_uploaded", "hr", {"filename": "resume.pdf"})
# AuditLogger.log(candidate.id, "extraction_completed", "system", {"confidence": 0.92})
# AuditLogger.log(candidate.id, "document_request_sent", "hr", {"email": "...@..."})
# AuditLogger.log(candidate.id, "documents_submitted", "candidate", {"pan": True, "aadhaar": True})
```

### 5. File Storage Security

```python
# utils/file_handler.py
import os
import uuid
import hashlib
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {
    'resume': {'pdf', 'docx'},
    'document': {'pdf', 'png', 'jpg', 'jpeg'}
}

MAX_FILE_SIZES = {
    'resume': 10 * 1024 * 1024,    # 10 MB
    'document': 5 * 1024 * 1024     # 5 MB
}

def save_file_securely(file, file_type: str, candidate_id: str) -> dict:
    """Save file with secure naming and validation"""
    
    # Validate extension
    original_name = secure_filename(file.filename)
    ext = original_name.rsplit('.', 1)[-1].lower()
    
    if ext not in ALLOWED_EXTENSIONS[file_type]:
        raise ValueError(f"Invalid file type: {ext}")
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset
    
    if size > MAX_FILE_SIZES[file_type]:
        raise ValueError(f"File too large: {size} bytes")
    
    # Generate secure filename (UUID-based, no original name exposed)
    secure_name = f"{candidate_id}_{uuid.uuid4().hex}.{ext}"
    
    # Determine storage path
    if file_type == 'resume':
        path = os.path.join('uploads', 'resumes', secure_name)
    else:
        path = os.path.join('uploads', 'documents', secure_name)
    
    # Save file
    os.makedirs(os.path.dirname(path), exist_ok=True)
    file.save(path)
    
    # Calculate hash for integrity check
    with open(path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    return {
        "filename": secure_name,
        "original_name": original_name,
        "path": path,
        "size": size,
        "hash": file_hash
    }
```

---

## 🎨 Frontend Components

### 1. Dashboard Page
- Search bar (by name, email, company)
- Filter by status (extraction_status, document_status)
- Sortable table columns
- Pagination
- Quick actions (view, request docs)

### 2. Resume Uploader
```tsx
// Features:
- Drag and drop zone
- File type validation (PDF/DOCX only)
- Size limit display
- Upload progress bar
- Success/error toast notifications
- Multiple file queue support
```

### 3. Candidate Profile
```tsx
// Sections:
1. Header: Name, status badges
2. Extracted Data:
   - Each field with confidence bar
   - Color coding: Green (>80%), Yellow (60-80%), Red (<60%)
3. Actions:
   - "Request Documents" button (disabled if already sent)
   - "Re-process Resume" button (if extraction failed)
4. Documents:
   - Submission status
   - View submitted PAN/Aadhaar (thumbnails)
   - Download links (HR only)
5. Activity Timeline:
   - Audit log entries
   - Email status
```

### 4. Candidate Portal (Public)
```tsx
// Simple, secure submission page:
1. Token validation
2. Welcome message (candidate name only)
3. Upload zones for:
   - PAN Card (required)
   - Aadhaar Card (required)
4. Format guidelines
5. Submit button
6. Confirmation page
```

---

## 🔄 User Flows

### Flow 1: HR Uploads Resume
```
1. HR drags resume to upload zone
2. Frontend shows upload progress
3. Backend saves file, starts extraction
4. Claude API extracts information
5. Results saved with confidence scores
6. Dashboard updates with new candidate
7. Audit log: "resume_uploaded", "extraction_completed"
```

### Flow 2: Request Documents
```
1. HR clicks "Request Documents" on candidate profile
2. Backend generates secure token
3. LangChain agent creates personalized message
4. Resend sends email with secure link
5. Email status tracked via webhooks
6. Audit log: "document_request_sent"
```

### Flow 3: Candidate Submits Documents
```
1. Candidate clicks link in email
2. Portal validates token (not expired, not used)
3. Candidate sees simple upload interface
4. Uploads PAN and Aadhaar images
5. Backend validates:
   - File type/size
   - PAN format (if text visible via OCR - optional)
   - Aadhaar checksum (if text visible via OCR - optional)
6. Files saved securely
7. Candidate sees confirmation
8. HR notified (dashboard update)
9. Audit log: "documents_submitted"
```

---

## 🛠️ Tech Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Backend Framework | Flask | Lightweight, fast development |
| Database | SQLite (dev) / PostgreSQL (prod) | Simple locally, scalable in prod |
| ORM | SQLAlchemy | Pythonic, handles both DBs |
| AI - Extraction | OpenAI / Claude (configurable) | Supports both, switch via env var |
| AI - Agent | LangChain (provider-agnostic) | Works with OpenAI or Claude |
| Email | Resend | Modern API, free tier, webhooks |
| File Parsing | pdfplumber + python-docx | Reliable text extraction |
| Frontend | React + TypeScript | Type safety, component model |
| Styling | Tailwind CSS | Rapid UI development |
| Build Tool | Vite | Fast dev server, optimized builds |
| HTTP Client | Axios | Clean API, interceptors |
| File Upload | react-dropzone | Best DnD experience |
| State | React Query | Server state management |
| Routing | React Router | Standard routing |
| Deployment - Backend | Render | Free tier, easy Python deploy |
| Deployment - Frontend | Vercel | Free, automatic deploys |

---

## 📦 Dependencies

### Backend (requirements.txt)
```
# Core
flask==3.0.0
flask-cors==4.0.0
flask-sqlalchemy==3.1.1
python-dotenv==1.0.0
gunicorn==21.2.0

# Database
sqlalchemy==2.0.23

# File Parsing
pdfplumber==0.10.3
python-docx==1.1.0

# AI (both providers supported - use what you have)
openai==1.12.0
anthropic==0.18.0
langchain==0.1.0
langchain-openai==0.0.5
langchain-anthropic==0.1.0

# Email
resend==0.7.0

# Security
cryptography==41.0.7
python-jose==3.3.0

# Utilities
uuid==1.30
Pillow==10.1.0  # For image validation
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.2",
    "react-dropzone": "^14.2.3",
    "date-fns": "^3.0.6",
    "lucide-react": "^0.303.0",
    "react-hot-toast": "^2.4.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## 🚀 Implementation Phases

### Phase 1: Project Setup (1 hour)
- [ ] Initialize Flask backend structure
- [ ] Initialize React frontend with Vite
- [ ] Set up database models
- [ ] Configure environment variables
- [ ] Set up CORS

### Phase 2: Resume Upload & Parsing (3 hours)
- [ ] Implement file upload endpoint
- [ ] Add PDF text extraction (pdfplumber)
- [ ] Add DOCX text extraction (python-docx)
- [ ] Integrate Claude API for extraction
- [ ] Implement confidence scoring
- [ ] Create audit logging

### Phase 3: Candidate Management (2 hours)
- [ ] List candidates endpoint with filters
- [ ] Get candidate details endpoint
- [ ] Implement secure file storage
- [ ] Add field encryption

### Phase 4: AI Agent & Email (2 hours)
- [ ] Set up LangChain with Claude
- [ ] Create document request agent
- [ ] Integrate Resend for emails
- [ ] Generate secure submission tokens
- [ ] Implement email logging

### Phase 5: Candidate Portal (2 hours)
- [ ] Create portal routes
- [ ] Token validation
- [ ] Document upload endpoint
- [ ] PAN/Aadhaar validation
- [ ] Submission confirmation

### Phase 6: Frontend - Dashboard (2 hours)
- [ ] Set up React project structure
- [ ] Create reusable UI components
- [ ] Build dashboard layout
- [ ] Implement candidate table
- [ ] Add search and filters

### Phase 7: Frontend - Upload & Profile (2 hours)
- [ ] Build drag-drop uploader
- [ ] Create candidate profile page
- [ ] Implement confidence score display
- [ ] Add document request button
- [ ] Show audit timeline

### Phase 8: Frontend - Candidate Portal (1 hour)
- [ ] Build public submission page
- [ ] Add document upload UI
- [ ] Create confirmation page

### Phase 9: Testing & Polish (1 hour)
- [ ] Test all API endpoints
- [ ] Test email delivery
- [ ] Test document validation
- [ ] Fix edge cases
- [ ] Add error handling

### Phase 10: Deployment (1 hour)
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] Configure environment variables
- [ ] Test production deployment
- [ ] Set up custom domain (optional)

### Phase 11: Documentation & Video (1 hour)
- [ ] Write comprehensive README
- [ ] Record Loom video (≤5 min)
- [ ] Create GitHub repo

---

## ⏱️ Total Estimated Time: 18-20 hours

---

## 🎬 Loom Video Outline (5 min)

1. **Architecture Overview** (1 min)
   - Show system diagram
   - Explain tech stack choices
   - Mention security features

2. **Demo: Upload Resume** (1.5 min)
   - Show drag-drop upload
   - Watch extraction happen
   - Highlight confidence scores

3. **Demo: Request Documents** (1 min)
   - Click request button
   - Show generated email
   - Explain personalization

4. **Demo: Candidate Portal** (1 min)
   - Open submission link
   - Upload sample documents
   - Show validation

5. **Wrap Up** (0.5 min)
   - Show audit trail
   - Mention deployment
   - Thank interviewer

---

## ✅ Acceptance Criteria

### Must Have
- [x] Resume upload accepts PDF and DOCX
- [x] AI extracts: name, email, phone, company, designation, skills
- [x] Confidence scores displayed for each field
- [x] Document request generates personalized email
- [x] Email actually sends via Resend
- [x] Candidate can submit documents via secure link
- [x] Submitted documents visible in HR dashboard
- [x] Audit trail for all actions
- [x] Duplicate detection (by email/phone) with option to create anyway

### Should Have
- [x] PAN format validation
- [x] Aadhaar checksum validation
- [ ] Field-level encryption for sensitive data
- [ ] Email delivery tracking
- [x] Search and filter on dashboard
- [x] Prompt injection protection (guardrails)
- [x] Output validation for AI responses

### Nice to Have
- [ ] OCR on uploaded documents to extract PAN/Aadhaar numbers
- [ ] Reminder emails after 3 days
- [ ] Bulk resume upload
- [ ] Export candidate data (CSV)
- [ ] Dark mode

---

## ⚙️ Environment Variables (.env)

```bash
# ===================
# AI Provider Config
# ===================
AI_PROVIDER=openai                    # "openai" or "claude"

# OpenAI (if AI_PROVIDER=openai)
OPENAI_API_KEY=sk-...

# Anthropic Claude (if AI_PROVIDER=claude)  
ANTHROPIC_API_KEY=sk-ant-...

# ===================
# Email (Resend)
# ===================
RESEND_API_KEY=re_...
EMAIL_FROM=TraqCheck <verify@yourdomain.com>

# ===================
# Security
# ===================
SECRET_KEY=your-flask-secret-key-here
ENCRYPTION_KEY=your-fernet-key-here   # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# ===================
# Database
# ===================
DATABASE_URL=sqlite:///traqcheck.db   # or postgresql://... for production

# ===================
# App Config
# ===================
FLASK_ENV=development
FRONTEND_URL=http://localhost:5173    # For CORS and email links
BACKEND_URL=http://localhost:5000
```

---

## 🔗 Reference Links

- [OpenAI API Docs](https://platform.openai.com/docs/api-reference)
- [Claude API Docs](https://docs.anthropic.com/claude/reference/getting-started-with-the-api)
- [LangChain Docs](https://python.langchain.com/docs/get_started/introduction)
- [Resend Docs](https://resend.com/docs)
- [Flask Docs](https://flask.palletsprojects.com/)
- [React Query Docs](https://tanstack.com/query/latest)
- [Tailwind CSS](https://tailwindcss.com/docs)

---

## 📝 Notes

- Keep API keys in `.env`, never commit them
- Use UUID for candidate IDs (not auto-increment) for security
- Mask Aadhaar numbers in logs/display (show only last 4)
- Set reasonable rate limits on upload endpoints
- Consider GDPR: implement data deletion endpoint
