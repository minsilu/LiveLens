---
description: Connect local backend and frontend to AWS RDS instance
---
# Connect Local Development to AWS RDS

This workflow configures your local LiveLens backend to use the AWS RDS instance instead of the local SQLite database `dev.db`. Because the frontend is already configured to talk to your local backend API, connecting the backend to RDS will automatically allow the frontend to retrieve data from RDS!

### Prerequisites
You will need your AWS RDS connection string. It usually looks like this:
- **PostgreSQL**: `postgresql://username:password@your-rds-endpoint.amazonaws.com:5432/dbname`
- **MySQL**: `mysql+pymysql://username:password@your-rds-endpoint.amazonaws.com:3306/dbname`

### Steps

1. **Update Backend Environment Variables**
   Open `/Users/mhaoliu/LiveLens/Backend/.env` and replace the existing `DATABASE_URL` with your RDS connection string.
   
   *Example:*
   ```ini
   DATABASE_URL="postgresql://myuser:mypassword@my-rds-db.xxxxxxxxx.us-east-1.rds.amazonaws.com:5432/livelens"
   ```

2. **Restart the Backend Server**
   Since `uvicorn` loads the `.env` file on startup, you must restart your backend server.
   Go to your backend terminal and press `Ctrl+C` to stop the server, then start it again:
   ```bash
   cd /Users/mhaoliu/LiveLens/Backend
   uvicorn api.main:app --reload
   ```

3. **Verify the Connection**
   Make sure the backend is successfully connected to the RDS database. You can check the health endpoint:
   ```bash
   curl http://localhost:8000/health
   ```
   *Expected Output should show the simulated database connection status indicating it found the URL.*

4. **Test the Frontend**
   Your frontend is already running with `npm run dev`. Simply open your web browser to the frontend URL (usually `http://localhost:8080` or `http://localhost:5173`) and you will see it pulling data directly from your AWS RDS instance via your local backend!
