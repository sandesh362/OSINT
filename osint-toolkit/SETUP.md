# Setup

Use Python 3.11+ and Node.js 20+.

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

`SHODAN_API_KEY` is required only for live network reconnaissance. XposedOrNot breach checks need no API key; all tests run with no configured keys.

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest -q
cd ..\frontend
npm run build
```

The test configuration blocks real TCP connections; provider interactions must be mocked.
