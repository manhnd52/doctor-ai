import pandas as pd
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "12345678"
CSV_PATH = "data/uberon_is_a.csv"
BATCH_SIZE = 1000

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def create_index(tx):
    """
    Create an index on the 'id' property of 'anatomy' nodes to speed up lookups.
    """
    tx.run("""
        CREATE INDEX anatomy_id IF NOT EXISTS
        FOR (n:anatomy) ON (n.id)
    """)

def clear_old_relationships(tx):
    """
    Remove all existing 'parent_child' relationships between 'anatomy' nodes to prepare for fresh insertions because the bidirectional relationships.
    """
    tx.run("MATCH (:anatomy)-[r:parent_child]-(:anatomy) DELETE r")

def batch_insert(tx, rows):
    query = """
    UNWIND $rows AS row
    OPTIONAL MATCH (child:anatomy {id: row.id})
    OPTIONAL MATCH (parent:anatomy {id: row.is_a})
    WITH row, child, parent
    WHERE child IS NOT NULL AND parent IS NOT NULL
    MERGE (child)-[:parent_child]->(parent)
    RETURN count(*) AS created
    """
    result = tx.run(query, rows=rows)
    return result.single()["created"]

def main():
    print("Reading CSV...")
    df = pd.read_csv(CSV_PATH)

    df = df.dropna(subset=["id", "is_a"])

    df["id"] = df["id"].astype(str).str.strip()
    df["is_a"] = df["is_a"].astype(str).str.strip()
    
    data = df.to_dict("records")

    total = len(data)

    print(f"Total rows: {total}")

    inserted_total = 0

    with driver.session() as session:
        print("Creating index...")
        session.execute_write(create_index)

        print("Clearing old parent_child relationships...")
        session.execute_write(clear_old_relationships)

        print("Start inserting...")

        for i in range(0, total, BATCH_SIZE):
            batch = data[i:i + BATCH_SIZE]
            created = session.execute_write(batch_insert, batch)

            inserted_total += created

            print(
                f"Batch {i//BATCH_SIZE + 1}: "
                f"{created}/{len(batch)} inserted | "
                f"Progress: {i + len(batch)}/{total}"
            )

    driver.close()

    print("\n===== DONE =====")
    print(f"Inserted: {inserted_total}/{total}")
    print(f"Skipped: {total - inserted_total}")


if __name__ == "__main__":
    main()