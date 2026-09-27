# DebugFlow Frontend

A React + Vite frontend for the DebugFlow debugging assistant.

> **Tagline:** Understand. Fix. Verify.

---

## Prerequisites

- **Node.js 18+** (or Node 20+)
- The **DebugFlow FastAPI backend** must be running on `http://localhost:8000`

---

## Install dependencies

```powershell
cd frontend
npm.cmd install
# or: & "C:\Program Files\nodejs\npm.cmd" install
```

---

## Start the frontend (development)

```powershell
cd frontend
npm.cmd run dev
# or directly with node:
node ".\node_modules\vite\bin\vite.js"
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Build for production

```powershell
cd frontend
npm.cmd run build
# Built files land in frontend/dist/
```

> **Windows note:** If `npm` is not in your PowerShell PATH, use `npm.cmd` or the full path
> `& "C:\Program Files\nodejs\npm.cmd"`. Node.js v24 + npm 11 are confirmed working.

---

## Running frontend + backend together

### Terminal 1 — Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000
```

### Terminal 2 — Frontend

```powershell
cd frontend
npm.cmd run dev
# or: node ".\node_modules\vite\bin\vite.js"
```

Both must be running simultaneously. The frontend talks to `http://localhost:8000`.

---

## How the frontend communicates with FastAPI

All HTTP calls are centralised in [`src/services/api.js`](src/services/api.js).

| UI Action            | Endpoint          | Request body                       |
|----------------------|-------------------|------------------------------------|
| Analyze Bug button   | `POST /analyze`   | `{ code, error }`                  |
| Generate Fix button  | `POST /fix`       | `{ code, analysis }` (root_cause)  |
| Run Tests button     | `POST /run-tests` | `{ test_code, timeout }`           |
| Health check (mount) | `GET  /health`    | —                                  |

CORS is pre-configured in the backend to allow `http://localhost:5173`.

---

## Demo workflow

1. Click **Load Demo** in the Code Input panel to load `demo/buggy_sample.py`.
2. Click **ZeroDivision** (or NameError / IndexError) in the Traceback panel to load the matching error.
3. Click **Analyze Bug** — the root cause analysis appears below.
4. Click **Generate Fix →** — the proposed fix with a unified diff appears.
5. Review the diff and click **Apply Fix to Editor** to copy fixed code back to the editor.
6. Paste or load test code in the Test Runner panel and click **Run Tests**.

---

## Environment variable

To point the frontend at a different backend host, create `frontend/.env.local`:

```
VITE_API_URL=http://localhost:8000
```

---

## Project structure

```
frontend/
├── index.html
├── vite.config.js
├── package.json
├── README.md
└── src/
    ├── main.jsx              # React entry point
    ├── App.jsx               # Root component + state + API orchestration
    ├── components/
    │   ├── Header.jsx        # App header + backend status indicator
    │   ├── WorkflowStatus.jsx# 6-stage progress indicator
    │   ├── CodeInput.jsx     # Python source code textarea
    │   ├── ErrorInput.jsx    # Traceback textarea + Analyze button
    │   ├── AnalysisPanel.jsx # Root cause analysis display
    │   ├── FixPanel.jsx      # Proposed fix, diff viewer, Apply button
    │   └── TestResults.jsx   # Test runner + results display
    ├── services/
    │   ├── api.js            # Centralised fetch helpers
    │   └── demo.js           # Demo code + traceback constants
    └── styles/
        └── App.css           # Dark developer-tool theme
```
