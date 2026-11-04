# Cheap IoT Pipeline: MQTT to ClickHouse with Claude Text-to-SQL

A small, readable example of an IoT data path that avoids a managed platform:

MQTT → Python ingestion → ClickHouse → natural-language questions answered by Claude

This repository accompanies an article about where a cheaper stack makes sense, where Databricks earns its cost, and where an LLM can help without taking over the data path. It is a teaching example, not a production system. It has not been run against real sensor traffic.

## Structure

- `schema/`: the ClickHouse table definition
- `ingest/`: subscribes to MQTT topics and writes rows to ClickHouse in batches
- `ask/`: turns a plain-language question into a single SELECT statement and runs it with a read-only user

## Setup

1. Run ClickHouse (locally or in Docker) and create the table:

   ```bash
   clickhouse-client --multiquery < schema/create_telemetry.sql
   ```

2. Copy `.env.example` to `.env` and fill in the values. Never commit `.env`.

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start ingestion:

   ```bash
   python ingest/mqtt_to_clickhouse.py
   ```

5. Ask a question:

   ```bash
   python ask/ask_sql.py "What was the average temperature for device sensor-01 in the last hour?"
   ```

## Known limitations

- Batches are flushed when a message arrives, so a quiet topic can leave rows waiting in memory. A timer-based flush would fix this.
- Malformed messages are silently dropped. A production system should store them in a separate error table.
- The SQL guard is a keyword filter, not a parser. Always connect with a user that has read-only permissions.
- The LLM can produce a query that is valid but wrong. Check results before acting on them.

## License

MIT
