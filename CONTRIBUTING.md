# LiveLens Contribution Guide

Welcome to the LiveLens team! This document outlines how we collaborate on the FastAPI backend, test our features natively, and safely deploy to the AWS cloud.

## 🏭 Architecture Overview

We use a modern Serverless Architecture deployed using AWS App Runner and CDK.
- Backend Framework: FastAPI (Python)
- Database: PostgreSQL with PostGIS (Private AWS RDS instance)
- Deployment & CI/CD: AWS App Runner connected to our GitHub repository.
- Infrastructure as Code: AWS CDK (Managed by the DevOps lead)

### Separation of Concerns
- Infrastructure (CDK): Files in `Backend/backend/`, `Backend/app.py`. Do not modify these unless you are updating cloud infrastructure.
- Business Logic (FastAPI): All files in the `Backend/api/` directory. **THIS IS WHERE YOU WILL WORK.**

---

## Development Workflow

### 1. Connecting to the Local Database

Our production PostgreSQL database is hidden securely behind an AWS VPC firewall. **You cannot easily connect to it locally.**

### 🛑 DO NOT Test Against the Production Database
- **Security**: You risk destroying real user data or mock templates.
- **Speed**: Remote connections have severe network latency which destroys unit test performance.
- **Network Limits**: The VPC firewall will block your connection anyway.

### ✅ The Solution: Local SQLite (Memory/File DB)
When developing features or running tests locally, we dynamically override the `DATABASE_URL` to point to a local SQLite database. 

1. Create a `.env` file in the `Backend/` directory (it is gitignored).
2. Inside `.env`, add: `DATABASE_URL=sqlite:///./dev.db`
3. Run the server locally: `uvicorn api.main:app --reload`

---

### 2. Developing New Features

**Step 1: Create a feature branch**
Always start by branching off from `main`:
`git checkout -b feat/<your-feature-name>`

**Step 2: Write modular code**
When developing a new feature, create one or more files in the `Backend/api/routes/` directory (e.g., `auth.py`) to store your business logic. Do not dump all logic into `main.py`.

**Step 3: Update dependencies**
If your feature requires new incoming Python libraries, add them to `Backend/api/requirements.txt`.

**Step 4: Mount the feature**
We use modular routing (`app.include_router`). When you finish developing a feature route, import it and add a line to `Backend/api/main.py`:

```python
from .routes import auth

# Mount the logic developed in the file `Backend/api/routes/auth.py`
app.include_router(auth.router, prefix="/auth", tags=["auth"])
```

---

### 3. 🧪 Unit Testing with Pytest

Before pushing any feature (especially authentication), you must write and pass unit tests. We use `pytest` and FastAPI's `TestClient` to test endpoints without spinning up a real server.

1. Ensure `pytest`, `httpx`, and `pytest-asyncio` are installed in your local virtual environment.
2. Write tests inside the `Backend/tests/` folder (e.g., `Backend/tests/test_auth.py`).
3. Run `pytest Backend/tests/` locally.

*If your tests fail, do not push your code.*

---

### 4. Pushing Your Code

We have an automated Continuous Integration & Continuous Deployment (CI/CD) pipeline integrated directly with GitHub. 

**Your Git Workflow:**
1. Commit your code: `git commit -m "feat: <your feature descriptions>"`
2. Push your current branch: `git push origin feat/<your-feature-name>`
3. Open a Pull Request (PR) to the `main` branch on GitHub.
4. Once approved, **Merge to `main`**.

Once merged, **AWS App Runner will automatically detect the change**, pull the code, execute the build step (which installs packages from `requirements.txt`), and gracefully roll out your changes in roughly 3 minutes with zero downtime. 

**Summary:**
Code -> Test Locally -> Push Branch -> Merge PR -> Auto Deploy to Live.
