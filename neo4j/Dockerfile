FROM neo4j:5.15.0

ENV NEO4J_PLUGINS='["apoc","n10s"]'

# APOC export/import
ENV NEO4J_apoc_export_file_enabled=true
ENV NEO4J_apoc_import_file_enabled=true
ENV NEO4J_apoc_import_file_use__neo4j__config=true

# Enable procedures
ENV NEO4J_dbms_security_procedures_unrestricted=apoc.*,n10s.*
ENV NEO4J_dbms_security_procedures_allowlist=apoc.*,n10s.*
ENV NEO4J_server_databases_default__to__read__only=false

# # Optional memory tuning
# ENV NEO4J_server_memory_heap_initial__size=2G
# ENV NEO4J_server_memory_heap_max__size=4G

COPY conf/neo4j.conf /var/lib/neo4j/conf/neo4j.conf
COPY conf/apoc.conf /var/lib/neo4j/conf/apoc.conf
COPY init/init.cypher /var/lib/neo4j/import/init/init.cypher

COPY start.sh /start.sh
RUN chmod +x /start.sh

ENV EXTENSION_SCRIPT=/start.sh
