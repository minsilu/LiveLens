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

### 1. Set Up Your Local Database
Our production PostgreSQL database is hidden securely behind an AWS VPC firewall. **You cannot easily connect to it locally.** Therefore, you must develop against a local SQLite database.
1. `pip install Beckend/api/requirement.txt`
1. Create a `.env` file in the `Backend/` directory (this file is gitignored so your settings stay local).
2. Inside `.env`, add this exact line: `DATABASE_URL=sqlite:///./dev.db`

### 2. Boot the Local Server & Swagger UI
Before you write any code, start your local server to ensure your environment is healthy and your local database initializes.

1. Open your terminal in the `Backend/` folder.
2. Run: `uvicorn api.main:app --reload`
3. Open your browser to the **Swagger UI**: `http://127.0.0.1:8000/docs`

*The Swagger UI is your best friend. It allows you to manually execute and test your APIs (like logging in or generating mock data) by simply clicking buttons in the browser.*

### 3. Develop Your Feature
Now that your server is running and hot-reloading:

**Step 1. Branch Out**
`git checkout -b feat/<your-feature-name>`

**Step 2. Write Modular Code**
Create your new route files in `Backend/api/routes/` (e.g., `tickets.py`). Do not dump all logic into `main.py`.

**Step 3. Update Dependencies**
If you need new packages, add them to `Backend/api/requirements.txt`.

**Step 4. Mount Your Router**
Register your new file in `Backend/api/main.py`:
```python
from .routes import tickets
app.include_router(tickets.router, prefix="/tickets", tags=["tickets"])
```
*Because the server is running with `--reload`, your new API will instantly appear on your Swagger UI page.*

### 4. 🧪 Write & Run Unit Tests (Pytest)
Manual testing in Swagger is great for development, but **before you push your code to the cloud, you must pass automated unit tests.**

1. Write tests in the `Backend/tests/` folder (e.g., `Backend/tests/test_tickets.py`).
2. Run your tests in the terminal: `pytest Backend/tests/`
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
