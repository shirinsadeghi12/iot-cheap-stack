CREATE TABLE IF NOT EXISTS telemetry (
    ts DateTime64(3, 'UTC'),
    device_id LowCardinality(String),
    metric LowCardinality(String),
    value Float64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (device_id, metric, ts);
