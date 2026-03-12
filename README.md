# NBNE Memorials

Automated order processing and SVG generation for personalised memorial products.

## Architecture

- **Backend:** Python / FastAPI + SQLAlchemy + PostgreSQL
- **Frontend:** Next.js / React + TailwindCSS
- **SVG Engine:** Isolated processor classes, one per product type

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env    # Edit with your DB credentials
alembic upgrade head    # Run migrations
python -m app.seed      # Seed DB from SKULIST data
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Project Structure
```
memorials/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # DB models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── seed.py              # DB seeder
│   │   ├── routers/
│   │   │   ├── orders.py        # Order ingestion + processing
│   │   │   ├── skus.py          # SKU management CRUD
│   │   │   └── processors.py    # SVG generation endpoints
│   │   ├── processors/          # SVG generators (one per type)
│   │   │   ├── registry.py      # Processor lookup
│   │   │   ├── base.py          # Base processor class
│   │   │   └── ...              # Individual processors
│   │   └── ingestion/
│   │       ├── amazon.py        # Amazon order parser
│   │       └── pipeline.py      # Order processing pipeline
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── app/
│   ├── components/
│   └── package.json
├── docker-compose.yml
└── README.md
```
