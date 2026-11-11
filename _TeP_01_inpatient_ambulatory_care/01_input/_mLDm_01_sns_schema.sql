-- ----------------------------------------------------------------------
-- PTS | Paulo Trigo Silva
-- mLDm | MoP
-- v01
-- ----------------------------------------------------------------------

-- MLDM | TeP_01 -- Inpatient-Ambulatory Care Profile Classification (SNS)
-- PostgreSQL relational schema
--
--
-- source: SNS / ACSS, "Morbilidade e Mortalidade Hospitalar"
-- https://transparencia.sns.gov.pt/explore/assets/morbilidade_mortalidade_hospit/
--
-- the source reports monthly inpatient episodes, inpatient days, ambulatory
-- episodes and deaths by month of DISCHARGE, institution, diagnosis chapter,
-- age group and sex; its records are aggregates, not individual patient data
--
-- terminology and legal references:
-- 1. INPATIENT denotes hospital care involving formal admission for a stay.
--    num_inpatient_admission maps the SNS field "Internamentos"; the period
--    refers to the DISCHARGE month, not necessarily the admission month.
--    num_inpatient_day maps "Dias de Internamento" (total inpatient days).
-- 2. AMBULATORY is preferred here to the broad term OUTPATIENT: the SNS field
--    "Ambulatório" concerns hospital episodes reported under its clinical
--    coding/statistical scope; it must not be interpreted as all outpatient
--    visits or all hospital consultations.
--    The current SNS price regulation distinguishes GDH ambulatory surgery
--    and medical episodes from external consultations (Annex I, Arts. 3,
--    14 and 16 of Portaria 274/2026/1, 25 June).
--    https://diariodarepublica.pt/dr/detalhe/portaria/274-2026-1138714124
-- 3. The SNS source still refers to Portaria 207/2017, 11 July. That diploma
--    was revoked by Art. 16 of Portaria 281/2026/1, 29 June, effective
--    1 July 2026. Keep the old reference only for source provenance.
--    https://diariodarepublica.pt/dr/detalhe/portaria/281-2026-1139897695
--    https://diariodarepublica.pt/dr/detalhe/portaria/207-2017-107669157
--
-- The CSV has a YYYY-MM period; importing it as DATE uses YYYY-MM-01 as a
-- representation convention. No constraint is imposed on the day component.
-- Source records with repeated analytical keys must be kept independently;
-- consolidation and construction of ML observations are separate steps.


-- ----------------------------------------------------------------------
-- recreate data model; CASCADE also removes dependent views
-- ----------------------------------------------------------------------
SET client_min_messages TO WARNING;
DROP TABLE IF EXISTS source_record CASCADE;
DROP TABLE IF EXISTS institution CASCADE;
DROP TABLE IF EXISTS region CASCADE;
DROP TABLE IF EXISTS diagnosis CASCADE;
DROP TABLE IF EXISTS inpatient_level CASCADE;
RESET client_min_messages;


-- ----------------------------------------------------------------------
CREATE TABLE region (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);


CREATE TABLE institution (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    id_region INTEGER NOT NULL,

    FOREIGN KEY (id_region) REFERENCES region(id)
);


CREATE TABLE diagnosis (
    id INTEGER PRIMARY KEY,
    description TEXT NOT NULL UNIQUE
);


CREATE TABLE source_record (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    period DATE NOT NULL,
    id_institution INTEGER NOT NULL,
    id_diagnosis INTEGER NOT NULL,
    age_group TEXT NOT NULL,
    sex VARCHAR(1) NOT NULL,
    num_inpatient_admission INTEGER NOT NULL,
    num_inpatient_day INTEGER NOT NULL,
    num_ambulatory_episode INTEGER NOT NULL,
    num_death INTEGER NOT NULL,

    FOREIGN KEY (id_institution) REFERENCES institution(id),
    FOREIGN KEY (id_diagnosis) REFERENCES diagnosis(id),

    CHECK (num_inpatient_admission >= 0),
    CHECK (num_inpatient_day >= 0),
    CHECK (num_ambulatory_episode >= 0),
    CHECK (num_death >= 0),

    CHECK (age_group IN (
        '[0-1[',
        '[1-5[',
        '[5-15[',
        '[15-25[',
        '[25-45[',
        '[45-65[',
        '[65-120[' )),
    CHECK (sex IN ('F', 'M', 'I'))
);


CREATE TABLE inpatient_level (
  name TEXT PRIMARY KEY,
  min_ratio NUMERIC(5,4) NOT NULL,
  max_ratio NUMERIC(5,4) NOT NULL,
  CHECK (name IN ('low', 'medium', 'high')),
  CHECK (min_ratio >= 0),
  CHECK (max_ratio <= 1),
  CHECK (min_ratio < max_ratio)
);


-- ----------------------------------------------------------------------
-- IMPORTANT:
-- canonical names used to match textual names across data imports
-- ----------------------------------------------------------------------
-- this function only defines a comparison form:
-- - Unicode NFC, lowercase, selected Latin accents mapped to ASCII, and
-- - spaces/punctuation collapsed into single hyphens
-- ----------------------------------------------------------------------
-- NFC requires a PostgreSQL database using UTF8 encoding
-- - the mapping can be extended if future source data require more characters
-- - it does NOT resolve abbreviations, renamed institutions or true synonyms
-- ----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION get_canonical_name(s TEXT)
RETURNS TEXT
LANGUAGE SQL
IMMUTABLE
STRICT
AS $$
    SELECT TRIM( BOTH '-' FROM
        REGEXP_REPLACE( TRANSLATE( LOWER( NORMALIZE( s, NFC ) ),
                        'àáâãäåāăąçćčèéêëēėęěìíîïĩīįñńòóôõöøōőùúûüũūůűýÿŷśšźž',
                        'aaaaaaaaaccceeeeeeeeiiiiiiinnoooooooouuuuuuuuyyysszz'
                        ),
                        '[^a-z0-9]+', '-', 'g' ) );
$$;


-- ----------------------------------------------------------------------
-- ABOUT THE INDEX:
-- the index stores canonical names without adding a column to the table
-- ----------------------------------------------------------------------
CREATE UNIQUE INDEX institution_name_canonical_uq
ON institution (get_canonical_name( name ));

CREATE UNIQUE INDEX region_name_canonical_uq
ON region (get_canonical_name(name));

CREATE UNIQUE INDEX diagnosis_description_canonical_uq
ON diagnosis (get_canonical_name( description ));


-- ----------------------------------------------------------------------
-- CANONICAL UNIQUENESS:
-- the indexes enforce canonical name uniqueness independently of
-- the data-loading procedure, preserving the original text
-- the original name is not modified or duplicated

-- canonical values are stored in the indexes, not as table attributes
-- so, index values cannot be queried directly as table data
-- use get_canonical_name(name) if you need to retrieve canonical values

-- if the function mapping changes after data have been loaded, validate
-- possible collisions and rebuild this expression index (REINDEX INDEX)
-- ----------------------------------------------------------------------

