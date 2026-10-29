# AI Recruiter

An AI-powered recruitment system built with FastAPI and Vapi to support candidate screening, date-of-birth verification, and interview scheduling.

## Features

- AI-powered candidate greeting and screening
- Candidate verification
- Interview scheduling assistant
- Eligibility checking tools
- FastAPI backend
- Database integration using SQLAlchemy

## Tech Stack

- Python
- FastAPI
- Vapi
- SQLAlchemy
- Pydantic
- SQLite
- Uvicorn

## Project Structure

```text
ai-recruiter/
├── app/
│   ├── assistants/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── tools/
│   ├── config.py
│   ├── database.py
│   └── main.py
├── tests/
├── requirements.txt
└── .gitignore
```

## Setup

1. Clone the repository.
2. Create and activate a Python virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure the required environment variables in a `.env` file.
5. Start the application using the project's FastAPI entry point.

## Security

Keep API keys and secrets in environment variables. Do not commit `.env`, virtual environments, or local database files.

## Status

This project is under development.
