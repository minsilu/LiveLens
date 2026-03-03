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


## Backend Development Workflow

### 1. Set Up Your Local Database
Our production PostgreSQL database is hidden securely behind an AWS VPC firewall. **You cannot easily connect to it locally.** Therefore, you must develop against a local SQLite database.
1. `pip install Beckend/api/requirement.txt`
2. Create a `.env` file in the `Backend/` directory (this file is gitignored so your settings stay local).
3. Inside `.env`, add this exact line: `DATABASE_URL=sqlite:///./dev.db`
4. Within 1 second, your local `dev.db` is populated and ready for frontend and backend component development!
If you need to access the real database, follow the instructions in the    [Access to Cloud Database](#access-to-cloud-database) section.

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


### 4. Pushing Your Code

We have an automated Continuous Integration & Continuous Deployment (CI/CD) pipeline integrated directly with GitHub. 

**Your Git Workflow:**
1. Commit your code: `git commit -m "feat: <your feature descriptions>"`
2. Push your current branch: `git push origin feat/<your-feature-name>`
3. Open a Pull Request (PR) to the `main` branch on GitHub.
4. Once approved, **Merge to `main`**.
5. search App Runner in AWS Console and check our domain name, then open it in your browser at `https://<your-domain-name>/docs` to test your new feature.

Once merged, **AWS App Runner will automatically detect the change**, pull the code, execute the build step (which installs packages from `requirements.txt`), and gracefully roll out your changes in roughly 3 minutes with zero downtime. 

**Summary:**
Code -> Test Locally -> Push Branch -> Merge PR -> Auto Deploy to Live.

---

## Frontend Development & Deployment Workflow

Our React frontend is deployed using **AWS Amplify**, which provides a fully managed CI/CD pipeline directly connected to our GitHub repository.

### 1. Set Up Your Local Environment
The frontend's template is built with Vite + React and lives in the `frontend/` directory.

1. Open your terminal and navigate to the frontend folder: `cd frontend`
2. Install dependencies: `npm install`
3. Create a `.env` file in the `frontend/` directory (ignored by git).
4. Inside `.env`, add this line to connect to your local backend:
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   ```
   *(Note: Never hardcode `http://localhost:8000` in your React components. Always use `import.meta.env.VITE_API_BASE_URL`.)*

### 2. Boot the Local Dev Server
1. From the `frontend/` directory, run: `npm run dev`
2. Open your browser to the local URL provided in the terminal (usually `http://localhost:5173`).
3. Ensure your local backend is also running simultaneously to test full-stack features.

### 3. Develop Your Feature
1. **Branch Out:** Use the same feature branch convention as the backend (`git checkout -b feat/<your-feature-name>`).
2. **Write Code:** Build React components, hook up APIs, and test locally in the browser.

### 4. Pushing Your Code (CI/CD)
Just like the backend, frontend deployment is fully automated via AWS Amplify.

**Your Git Workflow:**
1. Commit your frontend changes: `git commit -m "feat: <your feature description>"`
2. Push your branch: `git push origin feat/<your-feature-name>`
3. Open a Pull Request (PR) to the `main` branch.
4. Once approved, **Merge to `main`**.

**AWS Amplify Auto-Deployment:**
Once your code is merged into `main`, AWS Amplify will automatically:
1. Detect the change in the repository.
2. Pull the latest code.
3. Execute the build step (`npm run build`).
4. Deploy the statically generated files to AWS CloudFront (CDN).


You can monitor the deployment progress in the AWS Amplify Console. Once finished, your changes will be live globally on our Amplify domain. You can search App Amplify in AWS Console and check our domain name, then open it in your browser at `https://<your-domain-name>/docs` to see your new feature.

**Summary:**
Write Components -> Test with Local Backend -> Push Branch -> Merge PR -> Auto Deploy statically to CDN.

---

## Access to Cloud Database

This guide provides the necessary steps to connect to our PostgreSQL RDS instance from your local machine.

### 1. Prerequisites
Before attempting to connect, ensure you have the following installed:

1. PostgreSQL Client: psql (CLI) or a GUI like pgAdmin / DBeaver.
2. AWS VPN/SSO (Optional): If your organization requires SSO, ensure you are logged in via aws sso login.

### 2. Connection Credentials
Use the following details to configure your connection:

- Host (Endpoint): database-1.c36wyoowwijy.us-east-2.rds.amazonaws.com
- Port: 5432
- Database Name: postgres
- Username: postgres
- Password: 12345678 (Contact Minsi for the master password)

Inside `.env`, just set your DATABASE_URL=postgresql://postgres:12345678@database-1.c36wyoowwijy.us-east-2.rds.amazonaws.com:5432/postgres

Then you can test the api which will query the data through cloud database.

### 4. How to Connect the database directly (not just through api)
On Windows (PowerShell)
First, set your environment variable, then run the connection command:

```PowerShell
$env:RDSHOST="database-1.c36wyoowwijy.us-east-2.rds.amazonaws.com
# Connect using psql
psql -h $env:RDSHOST -U postgres -d postgres
# enter your pwd
```
On macOS / Linux
```Bash
export RDSHOST="database-1.c36wyoowwijy.us-east-2.rds.amazonaws.com"
psql -h $RDSHOST -U postgres -d postgres
# enter your pwd
```
### 5. Troubleshooting
- Connection Timeout: Usually means your IP is not whitelisted in the Security Group or "Public Access" is set to No.
- SSL Errors: If the server requires SSL, append sslmode=require to your connection string.
- Authentication Failed: Double-check the master password and ensure there are no trailing spaces in your username.
