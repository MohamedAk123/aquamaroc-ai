BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_initial

CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;

CREATE TABLE basins (
    id UUID NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    code VARCHAR(60), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_basins PRIMARY KEY (id), 
    CONSTRAINT uq_basins_name UNIQUE (name)
);

CREATE TABLE data_sources (
    id UUID NOT NULL, 
    title VARCHAR(300) NOT NULL, 
    producer VARCHAR(300), 
    dataset_url TEXT, 
    license TEXT, 
    source_type VARCHAR(30) NOT NULL, 
    checked_at TIMESTAMP WITH TIME ZONE, 
    verification_status VARCHAR(20) NOT NULL, 
    CONSTRAINT pk_data_sources PRIMARY KEY (id), 
    CONSTRAINT ck_data_sources_verification_status CHECK (verification_status IN ('DEMO','VERIFIED','TO_VERIFY'))
);

CREATE TABLE ingestion_runs (
    id UUID NOT NULL, 
    source_id UUID NOT NULL, 
    filename TEXT NOT NULL, 
    sha256 VARCHAR(64) NOT NULL, 
    archive_path TEXT NOT NULL, 
    mapping_sha256 VARCHAR(64) NOT NULL, 
    provenance JSONB NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    status VARCHAR(20) NOT NULL, 
    rows_read INTEGER NOT NULL, 
    rows_valid INTEGER NOT NULL, 
    rows_rejected INTEGER NOT NULL, 
    error_summary TEXT, 
    is_demo BOOLEAN NOT NULL, 
    CONSTRAINT pk_ingestion_runs PRIMARY KEY (id), 
    CONSTRAINT ck_ingestion_runs_status CHECK (status IN ('pending','success','partial','failed')), 
    CONSTRAINT ck_ingestion_runs_row_counts CHECK (rows_read >= 0 AND rows_valid >= 0 AND rows_rejected >= 0 AND rows_read = rows_valid + rows_rejected), 
    CONSTRAINT fk_ingestion_runs_source_id_data_sources FOREIGN KEY(source_id) REFERENCES data_sources (id), 
    CONSTRAINT uq_ingestion_runs_source_id UNIQUE (source_id, sha256, is_demo)
);

CREATE INDEX ix_ingestion_runs_sha256 ON ingestion_runs (sha256);

CREATE INDEX ix_ingestion_runs_source_id ON ingestion_runs (source_id);

CREATE TABLE reservoirs (
    id UUID NOT NULL, 
    basin_id UUID NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    normalized_name VARCHAR(200) NOT NULL, 
    capacity_mm3 NUMERIC(16, 4), 
    latitude NUMERIC(10, 7), 
    longitude NUMERIC(10, 7), 
    geometry geometry(POINT,4326), 
    coordinates_source TEXT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    CONSTRAINT pk_reservoirs PRIMARY KEY (id), 
    CONSTRAINT ck_reservoirs_coordinates_provenance CHECK ((latitude IS NULL AND longitude IS NULL AND geometry IS NULL) OR (latitude IS NOT NULL AND longitude IS NOT NULL AND coordinates_source IS NOT NULL)), 
    CONSTRAINT ck_reservoirs_capacity_positive CHECK (capacity_mm3 IS NULL OR capacity_mm3 > 0), 
    CONSTRAINT ck_reservoirs_latitude_range CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90), 
    CONSTRAINT ck_reservoirs_longitude_range CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180), 
    CONSTRAINT fk_reservoirs_basin_id_basins FOREIGN KEY(basin_id) REFERENCES basins (id), 
    CONSTRAINT uq_reservoirs_basin_id UNIQUE (basin_id, normalized_name)
);

CREATE INDEX ix_reservoirs_basin_id ON reservoirs (basin_id);

CREATE TABLE reservoir_measurements (
    id UUID NOT NULL, 
    reservoir_id UUID NOT NULL, 
    source_id UUID NOT NULL, 
    ingestion_run_id UUID NOT NULL, 
    observation_date DATE NOT NULL, 
    storage_mm3 NUMERIC(16, 4), 
    filling_rate_pct NUMERIC(7, 4), 
    published_at TIMESTAMP WITH TIME ZONE, 
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    quality_status VARCHAR(30) NOT NULL, 
    data_kind VARCHAR(20) NOT NULL, 
    CONSTRAINT pk_reservoir_measurements PRIMARY KEY (id), 
    CONSTRAINT ck_reservoir_measurements_data_kind CHECK (data_kind IN ('OFFICIAL','DEMO','UNVERIFIED')), 
    CONSTRAINT ck_reservoir_measurements_filling_range CHECK (filling_rate_pct IS NULL OR filling_rate_pct BETWEEN 0 AND 100), 
    CONSTRAINT ck_reservoir_measurements_has_measurement CHECK (storage_mm3 IS NOT NULL OR filling_rate_pct IS NOT NULL), 
    CONSTRAINT ck_reservoir_measurements_storage_nonnegative CHECK (storage_mm3 IS NULL OR storage_mm3 >= 0), 
    CONSTRAINT fk_reservoir_measurements_ingestion_run_id_ingestion_runs FOREIGN KEY(ingestion_run_id) REFERENCES ingestion_runs (id), 
    CONSTRAINT fk_reservoir_measurements_reservoir_id_reservoirs FOREIGN KEY(reservoir_id) REFERENCES reservoirs (id), 
    CONSTRAINT fk_reservoir_measurements_source_id_data_sources FOREIGN KEY(source_id) REFERENCES data_sources (id), 
    CONSTRAINT uq_reservoir_measurements_reservoir_id UNIQUE (reservoir_id, observation_date, source_id, data_kind)
);

CREATE INDEX ix_measurement_reservoir_date_desc ON reservoir_measurements (reservoir_id, observation_date DESC);

CREATE INDEX ix_reservoir_measurements_ingestion_run_id ON reservoir_measurements (ingestion_run_id);

CREATE INDEX ix_reservoir_measurements_source_id ON reservoir_measurements (source_id);

CREATE TABLE quality_issues (
    id UUID NOT NULL, 
    ingestion_run_id UUID NOT NULL, 
    measurement_id UUID, 
    issue_type VARCHAR(60) NOT NULL, 
    severity VARCHAR(20) NOT NULL, 
    details JSONB NOT NULL, 
    resolved_at TIMESTAMP WITH TIME ZONE, 
    CONSTRAINT pk_quality_issues PRIMARY KEY (id), 
    CONSTRAINT fk_quality_issues_ingestion_run_id_ingestion_runs FOREIGN KEY(ingestion_run_id) REFERENCES ingestion_runs (id), 
    CONSTRAINT fk_quality_issues_measurement_id_reservoir_measurements FOREIGN KEY(measurement_id) REFERENCES reservoir_measurements (id)
);

CREATE INDEX ix_quality_issues_ingestion_run_id ON quality_issues (ingestion_run_id);

INSERT INTO alembic_version (version_num) VALUES ('0001_initial') RETURNING alembic_version.version_num;

-- Running upgrade 0001_initial -> 0002_capacity_provenance

ALTER TABLE reservoirs ADD COLUMN capacity_source TEXT;

UPDATE alembic_version SET version_num='0002_capacity_provenance' WHERE alembic_version.version_num = '0001_initial';

COMMIT;

