# DebugFlow

> A structured debugging workflow that helps developers reproduce, analyze, fix, and verify Python failures.

**DebugFlow** is an end-to-end debugging assistant built for the **IBM Bob 2.0 Hackathon**. It transforms a Python failure from a raw traceback into a structured workflow:

**Input → Analyze → Root Cause → Fix → Test → Verified**

The project combines a React frontend with a FastAPI backend and a Python-based debugging engine to make debugging more systematic, explainable, and beginner-friendly.

---

## Problem

Debugging often involves jumping between multiple tools and manually performing repetitive steps:

- Reading and interpreting tracebacks
- Finding the responsible function and line
- Understanding the root cause
- Creating a possible fix
- Applying changes carefully
- Running tests again
- Verifying that the fix did not introduce another failure

This process can be especially difficult for beginners and students.

---

## Solution

DebugFlow provides a guided debugging workflow that brings these steps together in one interface.

A developer can provide:

- Python source code
- A traceback or error message

DebugFlow then:

1. Parses the traceback
2. Identifies the affected file, function, and line
3. Analyzes the source using Python AST analysis
4. Determines a likely root cause
5. Generates a candidate fix when a supported pattern is detected
6. Shows the proposed change as a diff
7. Keeps the original source unchanged until the user explicitly approves the fix
8. Runs the test suite
9. Reports the final result

---

## Core Workflow

```text
┌─────────────┐
│    Input    │
│ Code + Error│
└──────┬──────┘
       ↓
┌─────────────┐
│   Analyze   │
│  Traceback  │
└──────┬──────┘
       ↓
┌─────────────┐
│  Root Cause │
│ AST + Rules │
└──────┬──────┘
       ↓
┌─────────────┐
│     Fix     │
│ Candidate + │
│    Diff     │
└──────┬──────┘
       ↓
┌─────────────┐
│    Test     │
│   Pytest    │
└──────┬──────┘
       ↓
┌─────────────┐
│  Verified   │
│ Pass / Fail │
└─────────────┘ 
 ```

---

## Key Features
Traceback Analysis

Extracts structured information from Python tracebacks, including:

Exception type
Error message
File
Line number
Function
Source context

## AST-Based Source Analysis

Uses Python's built-in ast module to inspect:

- Functions
- Imports
- Statements
- Enclosing functions
- Relevant source snippets

---

## Root Cause Detection

Uses structured error-pattern analysis to identify likely causes and provide a confidence score.
---

## Candidate Fix Generation

Generates fixes for supported error patterns and presents them as a unified diff.

The original source is not automatically modified.
---

## Human Approval Gate

A proposed fix must be explicitly approved before it is applied.
---
## Automated Test Execution

Runs the project's tests and reports:

- Passed tests
- Failed tests
- Return code
- Execution output
- Overall status
---
## Guided Developer Interface

The React interface presents debugging as a progressive workflow instead of a collection of disconnected tools.
---
## Architecture
                ┌───────────────────────┐
                │    React Frontend     │
                │                       │
                │ Code Input            │
                │ Traceback Input       │
                │ Analysis              │
                │ Fix Diff              │
                │ Test Results          │
                └───────────┬───────────┘
                            │ REST / JSON
                            ↓
                ┌───────────────────────┐
                │    FastAPI Backend    │
                │                       │
                │ /analyze              │
                │ /fix                  │
                │ /run-tests            │
                │ /report               │
                └───────────┬───────────┘
                            ↓
                ┌───────────────────────┐
                │ Debugging Engine      │
                │                       │
                │ Traceback Parser      │
                │ AST Analyzer           │
                │ Root Cause Engine      │
                │ Fix Generator          │
                │ Sandbox Runner         │
                └───────────────────────┘

---
## Tech Stack
| Layer                   | Technology       |
| ----------------------- | ---------------- |
| Frontend                | React 18         |
| Build Tool              | Vite             |
| Styling                 | CSS              |
| Backend                 | Python + FastAPI |
| Server                  | Uvicorn          |
| Code Analysis           | Python `ast`     |
| Test Execution          | Pytest           |
| API                     | REST / JSON      |
| Version Control         | Git + GitHub     |
| Development Environment | IBM Bob IDE      |
---

## Project Structure
DebugFlow/
│
├── backend/
│   ├── engine/
│   │   ├── ast_analyzer.py
│   │   ├── fix_generator.py
│   │   ├── root_cause.py
│   │   ├── sandbox_runner.py
│   │   └── traceback_parser.py
│   │
│   ├── routers/
│   │   ├── analyze.py
│   │   ├── fix.py
│   │   ├── report.py
│   │   └── run_tests.py
│   │
│   ├── tests/
│   │   ├── test_engine.py
│   │   └── test_main.py
│   │
│   ├── main.py
│   └── requirements.txt
│
├── demo/
│   ├── buggy_sample.py
│   └── test_sample.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── styles/
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   └── vite.config.js
│
├── bob-task1_session_export.json
├── bob_task2_session_export.json
├── bob-task3_session_export.json
├── bob-task4_session_export.json
├── bob-task5_session_export.json
├── bob-task6_session_export.json
├── bob-task7_session_export.json
│
├── debugflow-task-4-integration-test-report.html
├── .env.example
├── .gitignore
└── README.md
## Getting Started
### Prerequisites

Make sure you have:

- Python 3.11+
- Node.js 18+
- npm
- Git
### 1. Clone the Repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd DebugFlow
### 2. Set Up the Backend

- Create a virtual environment:

python -m venv .venv

- Activate it on Windows:

.venv\Scripts\Activate.ps1

- Install dependencies:

pip install -r backend/requirements.txt

- Start the backend:

uvicorn backend.main:app --reload

- The API will be available at:

http://127.0.0.1:8000

- Health check:

http://127.0.0.1:8000/health
### 3. Start the Frontend

- Open another terminal:

cd frontend
npm install
npm run dev

- Open the local URL shown by Vite, typically:

http://localhost:5173
---
## Demo Workflow

DebugFlow includes deliberately buggy Python examples for demonstrating the debugging workflow.

Supported demo scenarios include:

- ZeroDivisionError
- NameError
- IndexError

A typical demonstration is:

Load Demo
    ↓
Analyze Bug
    ↓
Review Root Cause
    ↓
Generate Fix
    ↓
Review Diff
    ↓
Apply Fix
    ↓
Run Tests
    ↓
Verified
---

## Testing

The backend contains automated unit and integration tests covering:

- Traceback parsing
- AST analysis
- Root cause detection
- Fix generation
- Test execution
- API endpoints

Current verification:

Backend tests:       55 / 55 passed
Frontend build:      Successful
Demo scenarios:      Verified

The frontend production build is generated using:

npm run build
---
## Security Considerations

DebugFlow was designed with controlled debugging actions in mind.

Current safeguards include:

- No eval() or exec() for user input
- shell=False for subprocess execution
- Temporary files used for test execution
- Temporary execution files cleaned up after runs
- Proposed fixes are not silently applied
- Explicit user approval is required before applying a fix
- No secrets or API keys are committed to the repository

DebugFlow is currently a local prototype and should not be considered a production-grade arbitrary-code execution sandbox.
---
## Current Limitations

The current prototype intentionally keeps the implementation focused.

- Automatic fix generation currently supports a limited set of error patterns.
- Test execution currently uses the local Python environment.
- Full container-level isolation is not implemented.
- Persistent session storage is not currently enabled.
- The debugging engine is primarily rule-based rather than LLM-powered.

---
## Future Improvements

Potential future development includes:

- LLM-assisted root cause analysis
- More automatic fix patterns
- Docker/container-based execution isolation
- Git diff integration
- Persistent debugging sessions
- Multi-language debugging support
- Richer test and regression analysis
- MCP-based developer tooling
- IDE integrations
---
## IBM Bob 2.0 Hackathon

DebugFlow was developed as a submission for the IBM Bob 2.0 Hackathon.

IBM Bob was used throughout the development workflow for:

- Project planning
- Architecture design
- Backend implementation
- Frontend implementation
- Integration testing
- Debugging
- UI refinement
- Final verification

Bob task-session exports are included in the repository as development evidence.
---
## Development Tasks
| Task   | Focus                       |
| ------ | --------------------------- |
| Task 1 | Requirements & Architecture |
| Task 2 | Backend Debugging Engine    |
| Task 3 | React Frontend              |
| Task 4 | End-to-End Integration      |
| Task 5 | UI Polish                   |
| Task 6 | Demo / IndexError QA Fix    |
| Task 7 | Final UI Redesign           |
---
## Hackathon Highlights

DebugFlow demonstrates an end-to-end debugging workflow rather than only generating an explanation.

The core idea is:

Don't just explain the error. Guide the developer from failure to verified fix.
---

## License

This project was created as a hackathon prototype.

Add an appropriate open-source license if you decide to distribute the project publicly.
---
