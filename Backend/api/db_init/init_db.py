import os
import pg8000

def handler(event, context):
    try:
        # Retrieve db credentials from environment variables
        db_host = os.environ['DB_HOST']
        db_port = int(os.environ['DB_PORT'])
        db_user = os.environ['DB_USER']
        db_password = os.environ['DB_PASSWORD']
        db_name = os.environ['DB_NAME']
        
        # Connect to your postgres DB
        conn = pg8000.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )
        
        # Open a cursor to perform database operations
        cur = conn.cursor()
        
        # Execute initial schema instructions
        # We will replace the query later when the user provides the specific schema
        create_table_query = """
        CREATE EXTENSION IF NOT EXISTS postgis;

        CREATE TABLE IF NOT EXISTS Users (
          id                UUID PRIMARY KEY,
          email             TEXT UNIQUE NOT NULL,
          password_hash     TEXT NOT NULL,
          is_incognito      BOOLEAN DEFAULT FALSE,
          created_at        TIMESTAMP,
          last_login        TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS Venues (
          id                UUID PRIMARY KEY,
          name              TEXT NOT NULL,
          city              TEXT,
          location          GEOGRAPHY(Point),
          seat_map_2d_url   TEXT,
          seat_map_meta     JSONB,
          capacity          INTEGER,
          tags              JSONB
        );
        
        CREATE TABLE IF NOT EXISTS Events (
          id                UUID PRIMARY KEY,
          venue_id          UUID REFERENCES Venues(id),
          name              TEXT,
          artist            TEXT,
          genre             TEXT,
          event_date        DATE,
          ticket_url        TEXT
        );
        
        CREATE TABLE IF NOT EXISTS Seats (
          id                   UUID PRIMARY KEY,
          venue_id             UUID REFERENCES Venues(id),
          section              TEXT,
          row                  TEXT,
          seat_number          TEXT,
          x                    FLOAT,
          y                    FLOAT,
          z                    FLOAT,
          orientation          FLOAT,
          distance_to_stage    FLOAT
        );
        
        CREATE TABLE IF NOT EXISTS Reviews (
          id                UUID PRIMARY KEY,
          user_id           UUID REFERENCES Users(id),
          event_id          UUID REFERENCES Events(id),
          seat_id           UUID REFERENCES Seats(id),

          rating_visual     INTEGER,
          rating_sound      INTEGER,
          rating_value      INTEGER,
          overall_rating    INTEGER,
          
          price_paid        FLOAT,
          text              TEXT,
          images            JSONB,
          created_at        TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS SeatAggregates (
          seat_id           UUID PRIMARY KEY REFERENCES Seats(id),
          avg_visual        FLOAT,
          avg_sound         FLOAT,
          avg_value         FLOAT,
          avg_overall       FLOAT,
          avg_price_paid    FLOAT,
          
          review_count      INTEGER,
          last_updated      TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS AI_Predictions (
          seat_id              UUID PRIMARY KEY REFERENCES Seats(id),
          predicted_visual     FLOAT,
          predicted_sound      FLOAT,
          predicted_value      FLOAT,
          predicted_overall    FLOAT,
          predicted_price      FLOAT,
          confidence           FLOAT,
          explanation          TEXT
        );
        
        CREATE TABLE IF NOT EXISTS SimilarSeats (
          seat_id             UUID REFERENCES Seats(id),
          similar_seat_id     UUID REFERENCES Seats(id),
          similarity_score    FLOAT,
          PRIMARY KEY (seat_id, similar_seat_id)
        );
        """
        cur.execute(create_table_query)
        
        # Make the changes to the database persistent
        conn.commit()
        
        # Close communication with the database
        cur.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'body': 'Schema initialized successfully!'
        }
        
    except Exception as e:
        print(f"Error connecting to database or executing query: {e}")
        return {
            'statusCode': 500,
            'body': f"Error initializing database: {str(e)}"
        }
