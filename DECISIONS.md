# Architectural Decision Records (ADRs)

## ADR-001: Replacement of TimescaleDB with Native Postgres & Materialized Views
- **Status:** Accepted
- **Context:** TimescaleDB hypertables are not reliably supported or uniformly enabled across hosted Supabase PostgreSQL instances and local Supabase CLI environments.
- **Decision:** Use PostgreSQL native monthly range partitioning / BRIN indexes on `created_at` for high-throughput time-series queries. Use PostgreSQL materialized views (`mv_hourly_post_volume`, `mv_hourly_sentiment`) with unique indexes, refreshed via `pg_cron` or scheduled worker tasks.

## ADR-002: Salted SHA-256 Pseudonymization at Ingestion Boundary
- **Status:** Accepted
- **Context:** Collecting social media data carries privacy risks and GDPR/CCPA compliance obligations regarding personally identifiable information (PII).
- **Decision:** Hash all incoming author handles and author IDs using `hashlib.sha256(f"{SALT}:{identifier}")` at ingestion before records enter Kafka topics or database stores. Unless explicitly enabled via `STORE_RAW_HANDLES=true`, raw usernames are never persisted.

## ADR-003: Privacy-Preserving Aggregate-Only Demographics
- **Status:** Accepted
- **Context:** Individual-level inference of sensitive demographic attributes poses ethical and legal risks.
- **Decision:** Enforce $k$-anonymity ($k \ge 50$) with suppression of small cohort buckets and Laplace noise addition. No individual demographic records are created or persisted.

## ADR-004: Insert-Only Audit Log with Cryptographic Hash Chain
- **Status:** Accepted
- **Context:** Compliance officers and auditors require tamper-evident records of all analyst actions and case transitions.
- **Decision:** Enforce insert-only constraints on `audit_log` via PostgreSQL triggers that reject `UPDATE` and `DELETE`. Each row computes `row_hash = SHA256(prev_hash || canonical_payload)`, allowing instant linear verification of chain integrity.

## ADR-005: Local Development Dual-Mode & Mock Engine Support
- **Status:** Accepted
- **Context:** Developers and automated CI runners may run on machines without an active Docker daemon or live external Supabase credentials.
- **Decision:** The codebase provides seamless dual-mode capability:
  1. Production / Docker: Connects to live Kafka, Redis, and Supabase Postgres.
  2. Local / Mock / Test: Includes a self-contained in-memory / JSON / SQLite fallback pipeline so tests and CLI demos run anywhere without external service prerequisites.
