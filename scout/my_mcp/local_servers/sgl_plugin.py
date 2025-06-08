import os
import re
import pymysql
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

HOST     = os.getenv("AIVEN_HOST")
PORT     = int(os.getenv("AIVEN_PORT"))
USER     = os.getenv("AIVEN_USER")
PASSWORD = os.getenv("AIVEN_PASSWORD")
DATABASE = os.getenv("AIVEN_DATABASE")

# Initialize the MCP server
mcp = FastMCP("MySQL MCP Server")

# Database connection helper
def get_connection():
    return pymysql.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
        db=DATABASE,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
        read_timeout=10,
        write_timeout=10,
    )

@mcp.tool()
async def get_schema() -> dict:
    """
    Returns the database schema: tables and their columns with types.
    """
    schema = {}
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # List all tables
            cur.execute("SHOW TABLES;")
            tables = [row[f'Tables_in_{DATABASE}'] for row in cur.fetchall()]
            # Describe each table
            for table in tables:
                cur.execute(f"DESCRIBE `{table}`;")
                cols = [{
                    'Field': r['Field'],
                    'Type': r['Type'],
                    'Null': r['Null'],
                    'Key': r['Key']
                } for r in cur.fetchall()]
                schema[table] = cols
    finally:
        conn.close()
    return schema

@mcp.tool()
async def query_select(sql: str) -> list:
    """
    Executes a SELECT query and returns results. Only SELECT statements are allowed.
    """
    # Basic validation: allow only SELECT statements
    cleaned = sql.strip().lower()
    if not cleaned.startswith('select'):
        raise ValueError("Only SELECT queries are permitted.")
    # Prevent dangerous statements
    if re.search(r"\b(delete|update|insert|drop|alter|create)\b", cleaned):
        raise ValueError("Only read-only SELECT queries are allowed.")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        conn.close()

if __name__ == '__main__':
    import anyio
    anyio.run(mcp.run_stdio_async)
