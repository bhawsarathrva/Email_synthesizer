import logging
from sqlalchemy import text
from backend.app.database.connection import engine, SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inspect_db")

REQUIRED_COLUMNS = [
    "ai_category",
    "ai_confidence",
    "classification_reason",
    "verified_category",
    "verification_status",
    "human_feedback",
    "verified_by",
    "verified_at",
    "received_at"
]


def inspect_database_schema() -> dict:
    """Inspects tables, columns, data types, and primary keys in NeonDB."""
    info = {"tables": {}, "missing_columns": []}
    with engine.connect() as conn:
        # 1. Fetch tables
        tables_res = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)).fetchall()
        table_names = [r[0] for r in tables_res]
        logger.info(f"Discovered public tables: {table_names}")

        for tname in table_names:
            # 2. Fetch columns
            cols_res = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = :tname
                ORDER BY ordinal_position;
            """), {"tname": tname}).fetchall()

            # 3. Fetch primary key
            pk_res = conn.execute(text("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_schema = 'public'
                  AND tc.table_name = :tname;
            """), {"tname": tname}).fetchall()

            pk_cols = [p[0] for p in pk_res]

            info["tables"][tname] = {
                "columns": {
                    c[0]: {
                        "type": c[1],
                        "nullable": c[2] == "YES",
                        "default": c[3]
                    }
                    for c in cols_res
                },
                "primary_key": pk_cols
            }

        # Check existing columns on Email_data
        target_table = "Email_data" if "Email_data" in table_names else ("emails" if "emails" in table_names else None)
        if target_table:
            existing_cols = info["tables"][target_table]["columns"].keys()
            missing = [col for col in REQUIRED_COLUMNS if col not in existing_cols]
            info["missing_columns"] = missing
            info["target_table"] = target_table

    return info


def apply_migrations():
    """Applies necessary schema migration to add classification columns."""
    logger.info("Checking and applying schema migrations...")
    with engine.connect() as conn:
        with conn.begin():
            # Check Email_data table
            res = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM pg_tables 
                    WHERE schemaname = 'public' AND tablename = 'Email_data'
                );
            """)).scalar()

            if res:
                table_target = '"Email_data"'
            else:
                table_target = 'emails'

            sql = f"""
                ALTER TABLE {table_target} 
                    ADD COLUMN IF NOT EXISTS ai_category VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS ai_confidence DOUBLE PRECISION,
                    ADD COLUMN IF NOT EXISTS classification_reason TEXT,
                    ADD COLUMN IF NOT EXISTS verified_category VARCHAR(50),
                    ADD COLUMN IF NOT EXISTS verification_status VARCHAR(50) DEFAULT 'pending',
                    ADD COLUMN IF NOT EXISTS human_feedback TEXT,
                    ADD COLUMN IF NOT EXISTS verified_by VARCHAR(100),
                    ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITH TIME ZONE,
                    ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            """
            conn.execute(text(sql))
            logger.info("Successfully added missing classification and verification columns!")


if __name__ == "__main__":
    schema_info = inspect_database_schema()
    print("Schema Inspection Result:")
    for tbl, details in schema_info["tables"].items():
        print(f"\nTable: {tbl} (PK: {details['primary_key']})")
        for col, col_info in details["columns"].items():
            print(f"  - {col}: {col_info['type']}")
    
    if schema_info.get("missing_columns"):
        print(f"\nMissing required columns: {schema_info['missing_columns']}. Applying migration...")
        apply_migrations()
        print("Migration complete!")
    else:
        print("\nAll required columns are present!")
