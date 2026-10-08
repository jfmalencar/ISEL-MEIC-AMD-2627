
-- ----------------------------------------------------------------------
-- PTS | Paulo Trigo Silva
-- mLDm | MoP
-- v01
-- ----------------------------------------------------------------------

-- MLDM MoP 02 — Palmer Penguins database
-- PostgreSQL schema
-- here we use CASCADE to also remove auxiliary views
-- created during the MoP that depend on the dropped tables

DROP TABLE IF EXISTS observation CASCADE;
DROP TABLE IF EXISTS penguin;
DROP TABLE IF EXISTS batch;
DROP TABLE IF EXISTS lab;
DROP TABLE IF EXISTS island CASCADE;
DROP TABLE IF EXISTS species;
DROP TABLE IF EXISTS study;
DROP FUNCTION IF EXISTS haversine_km(
    DOUBLE PRECISION, DOUBLE PRECISION,
    DOUBLE PRECISION, DOUBLE PRECISION );

CREATE TABLE study (
    name VARCHAR(20) PRIMARY KEY
);

CREATE TABLE species (
    name VARCHAR(20) PRIMARY KEY
);

CREATE TABLE island (
    name VARCHAR(20) PRIMARY KEY,
    centroid_latitude DOUBLE PRECISION NOT NULL,
    centroid_longitude DOUBLE PRECISION NOT NULL
);

CREATE TABLE lab (
    name VARCHAR(20) PRIMARY KEY
);

CREATE TABLE batch (
    name VARCHAR(20) PRIMARY KEY,
    name_lab VARCHAR(20) NOT NULL,
    FOREIGN KEY (name_lab) REFERENCES lab(name)
);

CREATE TABLE penguin (
    id INTEGER PRIMARY KEY,
    name_species VARCHAR(20) NOT NULL,
    sex VARCHAR(20),
    FOREIGN KEY (name_species) REFERENCES species(name),
    CHECK (sex IN ('MALE', 'FEMALE') OR sex IS NULL)
);

CREATE TABLE observation (
    id_penguin INTEGER NOT NULL,
    date_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    name_study VARCHAR(20) NOT NULL,
    name_island VARCHAR(20),
    name_batch VARCHAR(20),
    sample_number INTEGER NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    bill_length_mm DOUBLE PRECISION,
    bill_depth_mm DOUBLE PRECISION,
    flipper_length_mm INTEGER,
    body_mass_g INTEGER,

    PRIMARY KEY (id_penguin, date_time),
    FOREIGN KEY (id_penguin) REFERENCES penguin(id),
    FOREIGN KEY (name_study) REFERENCES study(name),
    FOREIGN KEY (name_island) REFERENCES island(name),
    FOREIGN KEY (name_batch) REFERENCES batch(name),

    CHECK (sample_number > 0),
    CHECK (latitude BETWEEN -90 AND 90 OR latitude IS NULL),
    CHECK (longitude BETWEEN -180 AND 180 OR longitude IS NULL),
    CHECK ((latitude IS NULL) = (longitude IS NULL))
);


-- PostgreSQL schema
-- haversine function | Earth distance computation
CREATE OR REPLACE FUNCTION haversine_km(
    lat1 DOUBLE PRECISION,
    lon1 DOUBLE PRECISION,
    lat2 DOUBLE PRECISION,
    lon2 DOUBLE PRECISION
)
RETURNS DOUBLE PRECISION
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
  SELECT 2.0 * 6371.0088 *
         ASIN( LEAST( 1.0,
                      SQRT(
                        POWER( SIN( RADIANS( lat2 - lat1 ) / 2.0 ), 2 )
                        +
                        COS( RADIANS( lat1 ) )
                        *
                        COS( RADIANS( lat2 ) )
                        *
                        POWER( SIN( RADIANS( lon2 - lon1 ) / 2.0 ), 2 ) )
                    )
             );
$$;