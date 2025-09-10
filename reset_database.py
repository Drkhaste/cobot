import mysql.connector
from config import HOST, USERNAME, PASSWORD, DATABASE

def reset_database():
    """
    Connects to the database, drops all known tables, and recreates them
    with the correct schema.
    """
    try:
        conn = mysql.connector.connect(
            host=HOST, user=USERNAME, password=PASSWORD, database=DATABASE
        )
        cursor = conn.cursor()

        tables_to_drop = ["admins", "tokens2", "channels2"]

        print("--- Dropping existing tables... ---")
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"Table '{table}' dropped successfully.")
            except mysql.connector.Error as err:
                print(f"Error dropping table {table}: {err}")

        print("\n--- Recreating tables with correct schema... ---")

        # Recreate Admins table
        cursor.execute("""
            CREATE TABLE admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL
            )
        """)
        print("Table 'admins' created successfully.")

        # Recreate Tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tokens2 (
                id INT AUTO_INCREMENT PRIMARY KEY,
                token VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'tokens2' created successfully.")

        # Recreate Channels table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels2 (
                id INT AUTO_INCREMENT PRIMARY KEY,
                tokenusername VARCHAR(255),
                typechannel VARCHAR(50),
                channel_name TEXT,
                username VARCHAR(255),
                channel_id BIGINT,
                status VARCHAR(10),
                text TEXT,
                fileid TEXT,
                txt TEXT,
                size VARCHAR(100),
                nn VARCHAR(255)
            )
        """)
        print("Table 'channels2' created successfully.")

        conn.commit()
        cursor.close()
        conn.close()

        print("\nDatabase has been successfully reset!")

    except mysql.connector.Error as err:
        print(f"Failed to connect to or reset database: {err}")

if __name__ == "__main__":
    print("WARNING: This script will completely wipe all data from the bot's tables.")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() == 'yes':
        reset_database()
    else:
        print("Operation cancelled.")
