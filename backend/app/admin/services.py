from typing import LiteralString, cast
from sqlalchemy.orm import Session
from app.auth.models import User
from app.auth.utils import verify_password, hash_password
from app.auth.exceptions import InvalidCredentialsException, InactiveUserException
from app.database import get_db
from app.database import get_db
from app.kg_connection.models import KgConnection, Connecting
from fastapi import Depends
from app.kg_connection.utils import KGSessionManager
from neo4j import Query
"""
One user have many kg connections, but only one active connection at a time.
The table Connecting will store the current active connection for each user. 
When a user connects to a new kg connection, we will update the Connecting table to point to the new connection and set the previous connection as inactive.
"""
def add_kg_connection(user: User, uri: str, database_name: str, username: str, password: str, db: Session):
    new_connection = KgConnection(user_id=user.id, uri=uri, database_name=database_name, username=username, password=password, is_active=True)

    session_manager = KGSessionManager()
    result = session_manager.validate_connection(new_connection)
    if not result:
        db.rollback()
        raise Exception("Failed to connect to the knowledge graph.")
    
    new_connection.node_count = result['nodeCount']
    new_connection.relationship_count = result['relationshipCount']

    db.add(new_connection)
    db.commit()
    db.refresh(new_connection)

    # Automatically set this connection as active in the Connecting table
    current_connecting = db.query(Connecting).filter(Connecting.user_id == user.id).first()
    if current_connecting:
        current_connecting.kg_connection_id = new_connection.id
    else:
        new_connecting = Connecting(user_id=user.id, kg_connection_id=new_connection.id)
        db.add(new_connecting)
    db.commit()

    return new_connection

def get_all_connections(user: User, db: Session):
    connections = db.query(KgConnection).filter(KgConnection.user_id == user.id).all()
    return connections

def get_current_connection(user: User, db: Session) -> KgConnection | None:
    connection = db.query(KgConnection).join(
        Connecting, Connecting.kg_connection_id == KgConnection.id
    ).filter(
        Connecting.user_id == user.id
    ).first()
    return connection

def connect_to_kg(user: User, kg_connection_id: int, db: Session):
    connection = db.query(KgConnection).filter(KgConnection.id == kg_connection_id, KgConnection.user_id == user.id).first()
    if not connection:
        raise Exception("Connection not found")
    
    if not connection.is_active:
        raise Exception("Connection is inactive")

    session_manager = KGSessionManager()
    if not session_manager.validate_connection(connection):
        raise Exception("Failed to connect to the knowledge graph.")
    
    current_connecting = db.query(Connecting).filter(Connecting.user_id == user.id).first()
    if current_connecting:
        current_connecting.kg_connection_id = kg_connection_id
    else:
        new_connecting = Connecting(user_id=user.id, kg_connection_id=kg_connection_id)
        db.add(new_connecting)
    
    db.commit()
    return connection

def delete_connection(user: User, connection_id: int, db: Session):
    connection = db.query(KgConnection).filter(KgConnection.id == connection_id, KgConnection.user_id == user.id).first()
    if connection:
        db.delete(connection)
        db.commit()
        return True
    return False

def run_query(user: User, query: str, db: Session):
    session_manager = KGSessionManager()
    current_connection = get_current_connection(user, db)
    if not current_connection:
        raise Exception("Don't have any connection to knowledge graph")
    session = session_manager.get_session(current_connection)
    result = session.run(cast(LiteralString, query))
    return result.data()