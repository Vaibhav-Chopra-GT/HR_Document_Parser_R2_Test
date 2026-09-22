# Talently - Resume Parser & Document Collection System

A full-stack AI-powered system for HR teams to:
1. Upload and parse resumes automatically
2. Extract candidate information with confidence scores
3. Send personalized document requests via email
4. Collect PAN & Aadhaar documents securely through a candidate portal

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  Flask Backend  │────▶│  OpenAI/Claude  │
│   (Vite + TS)   │◀────│   (REST API)    │◀────│   (LangChain)   │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │   SQLite DB     │
                        │  + File Store   │
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenAI or Anthropic API key (optional for mock mode)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the server
python run.py
```

Server runs at: http://localhost:5000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

App runs at: http://localhost:5173

## ⚙️ Configuration

Edit `backend/.env`:

```bash
# AI Provider - "openai", "claude", or "mock" (for testing without API)
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
# OR
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...

# Email (optional - works without it, just logs instead of sending)
RESEND_API_KEY=re_...
```

## 📋 Features

### Resume Parsing
- Upload PDF or DOCX resumes
- AI extracts: Name, Email, Phone, Company, Designation, Skills
- Confidence scores for each field (0-100%)

### Document Collection
- AI generates personalized document request emails
- Secure candidate portal with unique tokens
- PAN and Aadhaar validation (format + checksum)

### HR Dashboard
- View all candidates with status
- Search and filter
- Download submitted documents
- Audit trail for compliance

## 🔌 API Endpoints

### Candidates (HR)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/candidates/upload` | Upload resume |
| GET | `/api/candidates` | List candidates |
| GET | `/api/candidates/<id>` | Get candidate details |
| POST | `/api/candidates/<id>/request-documents` | Send document request |
| GET | `/api/candidates/<id>/audit-log` | Get audit trail |

### Portal (Candidates)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/portal/<token>` | Validate submission link |
| POST | `/api/portal/<token>/submit` | Upload documents |

## 🔐 Security Features

- PAN format validation (AAAAA9999A)
- Aadhaar Verhoeff checksum validation
- Secure file storage with UUID naming
- Token-based candidate portal access
- Audit logging for all actions

## 📁 Project Structure

```
traqcheck_test/
├── backend/
│   ├── app/
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # AI, email, validation
│   │   ├── utils/          # File handling, logging
│   │   └── models.py       # Database models
│   ├── uploads/            # Stored files
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── pages/          # Dashboard, Detail, Portal
│   │   ├── components/     # Reusable UI
│   │   └── api/            # API client
│   └── package.json
└── README.md
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask, SQLAlchemy |
| AI | OpenAI / Claude (configurable) |
| Email | Resend |
| Frontend | React, TypeScript, Vite |
| Styling | Tailwind CSS |

## 📝 License

MIT
