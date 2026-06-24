# MAGS FastAPI Backend

Python FastAPI backend for the MAGS Window aluminium profile management system. Connects to PostgreSQL (Neon) and serves the same API contract as the MAGS-Window Next.js mock routes.

## Setup

```bash
cd "API MAGS"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your DATABASE_URL
```

## Seed database

Exports mock data from MAGS-Window- and loads it into PostgreSQL:

```bash
source venv/bin/activate
python run_seed.py
```

To re-seed without re-exporting JSON:

```bash
python run_seed.py --skip-export
```

## Run API server

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Connect MAGS-Window

1. Start this API on port `8000`
2. In `MAGS-Window-`, set `MAGS_API_URL=http://127.0.0.1:8000` in `.env.local`
3. Run `npm run dev` in MAGS-Window-

Next.js `/api/*` routes proxy to this backend automatically.

## ImageKit uploads

Set these in `.env`:

```env
IMAGEKIT_PUBLIC_KEY=public_...
IMAGEKIT_PRIVATE_KEY=private_...
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/abm2tsfhg
IMAGEKIT_UPLOAD_FOLDER=/mags/profiles
```

Endpoints:

- `POST /api/uploads/image` — server-side upload (used by profile image picker)
- `GET /api/uploads/auth` — client upload auth parameters

Profile images upload to ImageKit when adding or editing profiles in MAGS-Window.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/profiles` | Profile master list |
| GET | `/api/challans` | Challan records |
| GET | `/api/vendors` | Vendor list |
| GET | `/api/stock` | Stock inward + ledger |
| GET | `/api/consumption` | Consumption records |
| GET | `/api/powder-coating` | Powder coating batches |
| GET | `/api/scrap` | Scrap records |
| GET | `/api/dashboard?range=` | Dashboard KPIs and charts |
| GET | `/api/reports` | Report analytics |
| GET | `/api/users` | User list |
| GET | `/api/series` | Series names |
