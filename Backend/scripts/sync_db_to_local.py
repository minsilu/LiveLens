import os
from sqlalchemy import create_engine, MetaData
from dotenv import load_dotenv

def sync_data():
    """
    Connects to the cloud RDS production database, pulls all data into memory,
    and inserts it into the local SQLite 'dev.db' database for full-stack local development.
    """
    # Specifically looking for production credentials
    load_dotenv(".env.prod")
    
    prod_url = os.getenv("PROD_DATABASE_URL")
    local_url = "sqlite:///./dev.db"
    
    if not prod_url:
        print("❌ Error: PROD_DATABASE_URL environment variable is missing.")
        print("Please create a .env.prod file in the Backend/ directory with your RDS connection string.")
        return
        
    print(f"🔄 Connecting to Production Database...")
    try:
        prod_engine = create_engine(prod_url)
        prod_meta = MetaData()
        prod_meta.reflect(bind=prod_engine)
        print("✅ Production Database connected and schema reflected.")
    except Exception as e:
        print(f"❌ Failed to connect to Production Database: {e}")
        return

    print(f"🔄 Connecting to Local Database ({local_url})...")
    local_engine = create_engine(local_url)
    
    print("🚀 Starting Data Synchronization...")
    
    with prod_engine.connect() as prod_conn:
        with local_engine.begin() as local_conn:
            # Note: SQLite check_same_thread defaults to True but Engine.begin() handles the single sync thread safely.
            for table_name, table in prod_meta.tables.items():
                if table_name in ['spatial_ref_sys', 'geography_columns', 'geometry_columns']:
                    print(f"⏭️ Skipping internal PostGIS table: {table_name}")
                    continue
                    
                print(f"📦 Syncing table: {table_name}...")
                
                # Fetch all rows from AWS RDS Postges
                rows = prod_conn.execute(table.select()).fetchall()
                if not rows:
                    print(f"   -> Table {table_name} is empty, skipping.")
                    continue
                
                # Insert into Local SQLite dev.db
                data_to_insert = [dict(row._mapping) for row in rows]
                
                try:
                    # In case data already exists, clear it first to avoid Primary Key conflicts
                    local_conn.execute(table.delete())
                    local_conn.execute(table.insert(), data_to_insert)
                    print(f"   -> Successfully copied {len(rows)} records.")
                except Exception as e:
                    print(f"   -> ⚠️ Failed to insert into {table_name}: {e}")

    print("✅ Database synchronization complete!")

if __name__ == "__main__":
    # Safety check to ensure relative pathing works
    if not os.path.exists("./api"):
        print("⚠️ Please run this script from the LiveLens/Backend directory.")
        exit(1)
        
    sync_data()
