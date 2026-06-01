-- Seed default users
-- passwords: admin123 and user123 respectively
INSERT INTO users (username, hashed_password, is_active, role) VALUES 
('admin', '$pbkdf2-sha256$29000$HcO41xpDCCFESGmt1XpvbQ$Mt4aJWzwpdpbKVrdEBgPqQ2D.e01kvUcwy0avX1ojIw', 1, 'ADMIN'),
('user', '$pbkdf2-sha256$29000$DoEQovQewxhjzHmPUap17g$fNESwC95JX6VcTqVKaC77i5mpCJUbXX2R6KBsylxE5o', 1, 'USER');

-- Seed default knowledge graph
INSERT INTO knowledge_graphs (name, description, uri, database_name, username, password, is_active, created_at) VALUES 
('Default Knowledge Graph', 'Default Neo4j Knowledge Graph Connection', 'bolt://localhost:7687', 'neo4j', 'neo4j', '123456', 1, CURRENT_TIMESTAMP);
