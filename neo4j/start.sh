#!/bin/bash

set -e

DB_PATH="/data/databases/neo4j"

echo "Checking for existing database at $DB_PATH..."

if [ ! -d "$DB_PATH" ]; then
    echo "No database found. Restoring dump..."

    neo4j-admin database load neo4j \
        --from-path=/backup \
        --overwrite-destination=true

    echo ">>> Setting up full-text search indexes for PrimeKG..."
    cypher-shell -d neo4j -u neo4j -p 12345678 -f /startup/init.cypher
    if [ $? -ne 0 ]; then
        echo "Error while setting up full-text search indexes!"
        exit 1
    fi
fi

echo "Starting Neo4j..."
