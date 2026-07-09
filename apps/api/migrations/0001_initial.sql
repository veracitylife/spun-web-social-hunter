-- Social Hunter initial schema scaffold.
-- Apply with your migration tool of choice after replacing demo auth and persistence wiring.

CREATE TABLE IF NOT EXISTS searches (
  id UUID PRIMARY KEY,
  actor_id VARCHAR(120) NOT NULL,
  target_type VARCHAR(32) NOT NULL,
  target_hash VARCHAR(128) NOT NULL,
  consent_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(32) NOT NULL DEFAULT 'queued',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_searches_target_hash ON searches(target_hash);

CREATE TABLE IF NOT EXISTS findings (
  id UUID PRIMARY KEY,
  search_id UUID NOT NULL,
  source VARCHAR(120) NOT NULL,
  category VARCHAR(80) NOT NULL,
  status VARCHAR(32) NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  title VARCHAR(255) NOT NULL,
  url TEXT,
  evidence TEXT NOT NULL,
  compliance_flags JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_findings_search_id ON findings(search_id);

CREATE TABLE IF NOT EXISTS source_health (
  id UUID PRIMARY KEY,
  source_id VARCHAR(120) NOT NULL,
  status VARCHAR(32) NOT NULL,
  latency_ms DOUBLE PRECISION,
  error_message TEXT,
  checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_source_health_source_id ON source_health(source_id);

CREATE TABLE IF NOT EXISTS exports (
  id UUID PRIMARY KEY,
  search_id UUID NOT NULL,
  actor_id VARCHAR(120) NOT NULL,
  format VARCHAR(16) NOT NULL,
  filename VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_exports_search_id ON exports(search_id);

CREATE TABLE IF NOT EXISTS audit_events (
  id UUID PRIMARY KEY,
  actor_id VARCHAR(120) NOT NULL,
  action VARCHAR(120) NOT NULL,
  target_hash VARCHAR(128),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_target_hash ON audit_events(target_hash);
