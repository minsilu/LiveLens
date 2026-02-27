# LiveLens Contribution Guide

Welcome to the LiveLens team! This document outlines how we collaborate on the FastAPI backend and how your code gets deployed automatically to AWS.

## Architecture Overview

We use a modern Serverless Architecture deployed using AWS CDK.
- **Backend Framework**: FastAPI (Python)
- **Database**: PostgreSQL with PostGIS (Private AWS RDS instance)
- **Deployment & CI/CD**: AWS App Runner connected to our GitHub repository.
- **Infrastructure as Code**: AWS CDK (Managed by the DevOps lead)

### Separation of Concerns
- **Infrastructure (CDK)**: All files in the `Backend/backend/` directory, `Backend/app.py`, and `Backend/cdk.json`. Do not modify these unless you are updating cloud infrastructure.
- **Business Logic (FastAPI)**: All files in the `Backend/api/` directory. **This is where backend developers will work.**

---

## 🛠️ Where to Write Your Code

If you are tasked with building business logic (e.g., User Login, Venue Search, Reviews), you will focus **exclusively** on the `Backend/api/` folder.

### 1. `Backend/api/main.py`
This is our FastAPI entry point. For simpler features, you can add your `router` endpoints directly here. However, as the app grows, we will split routes into separate files (e.g., `Backend/api/routes/users.py`, `Backend/api/routes/venues.py`) and include them in `main.py`.

### 2. `Backend/api/requirements.txt`
If your new feature requires a third-party Python library (like `passlib` for password hashing or `PyJWT` for auth tokens), you must add the library name to this file. Our AWS CI/CD pipeline uses this file to install your dependencies during the Docker build process.

### 3. Database Connection (`engine`)
We use `sqlalchemy` to connect to our PostgreSQL database. The connection `engine` is already initialized in `Backend/api/main.py`.
- **Do not hardcode database credentials.** The cloud environment automatically injects the secure `DATABASE_URL` environment variable.
- You can import the `engine` object from `Backend/api/main.py` or use it directly in your route handlers to execute SQL queries or ORM commands.

---

## 💻 Local Testing & Mocking Data

Because our PostgreSQL database is private and hidden beautifully behind an AWS VPC firewall, **you cannot connect your local DBeaver/DataGrip directly to the production database.**

### How to test your code:

**Option A - Test via API Endpoints (The Serverless Way):**
1. Write a temporary "Mock Endpoint" in `Backend/api/main.py` (e.g., `POST /dev/mock-venues`).
2. Push your changes to GitHub (see CI/CD below).
3. Open our live, interactive Swagger API documentation at:  
   `https://mufceq7fkv.us-east-2.awsapprunner.com/docs`
4. Use the Swagger UI to execute your Mock endpoint to safely bypass the firewall and inject data into the cloud DB.

**Option B - Test with Local SQLite/Postgres:**
If you prefer not to wait for cloud deployments, you can configure your local `.env` file with a local SQLite or Postgres database URL. Replace `DATABASE_URL` with your local connection string when running `uvicorn api.main:app --reload` locally from the `Backend` directory.

---

## 🚀 The CI/CD Pipeline: Pushing Your Code

We have an automated Continuous Integration & Continuous Deployment (CI/CD) pipeline integrated directly with GitHub. 

**You do not need to run `docker build` or `cdk deploy`.**

### Your Workflow:
1. Make a new branch: `git checkout -b feat/user-login`.
2. Write your amazing FastAPI code inside the `Backend/api/` directory.
3. Test locally if possible, or push to GitHub and open a Pull Request (PR) to the `main` branch.
4. **Merge to `main`**.

Once your code is merged into the `main` branch, **AWS App Runner will automatically detect the change.** Within 1-2 minutes, it will automatically pull your fresh code, build the container, and perform a zero-downtime deployment to our live API!

**No manual deployment commands required. Code -> Push -> Live.**
