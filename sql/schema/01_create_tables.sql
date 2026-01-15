-- ============================================================================
-- Clinical Trial Analytics - Database Schema
-- ============================================================================
-- This script creates the normalized database schema for clinical trial data
-- from ClinicalTrials.gov API v2
--
-- Schema follows Third Normal Form (3NF) principles
-- Foreign keys ensure referential integrity
-- Indexes optimize common query patterns
-- ============================================================================

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS study_design;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS sponsors;
DROP TABLE IF EXISTS outcomes;
DROP TABLE IF EXISTS interventions;
DROP TABLE IF EXISTS conditions;
DROP TABLE IF EXISTS studies;

-- ============================================================================
-- Core Studies Table
-- ============================================================================
-- Central table containing main study information
-- ============================================================================

CREATE TABLE studies (
    -- Primary Key
    study_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Unique Identifiers
    nct_id VARCHAR(20) UNIQUE NOT NULL,
    acronym VARCHAR(100),

    -- Study Information
    title TEXT,
    brief_summary TEXT,

    -- Study Classification
    status VARCHAR(50),
    phase VARCHAR(50),
    study_type VARCHAR(50),

    -- Dates
    start_date DATE,
    completion_date DATE,
    primary_completion_date DATE,

    -- Enrollment Information
    enrollment INTEGER,
    enrollment_type VARCHAR(20),  -- 'Actual' or 'Anticipated'

    -- Eligibility Criteria
    eligibility_criteria TEXT,
    minimum_age VARCHAR(20),
    maximum_age VARCHAR(20),
    gender VARCHAR(20),
    healthy_volunteers VARCHAR(10),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (enrollment >= 0),
    CHECK (enrollment_type IN ('Actual', 'Anticipated', NULL))
);

-- ============================================================================
-- Conditions Table
-- ============================================================================
-- Medical conditions and diseases being investigated
-- One-to-Many relationship with studies (one study can have multiple conditions)
-- ============================================================================

CREATE TABLE conditions (
    -- Primary Key
    condition_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign Key
    study_id INTEGER NOT NULL,

    -- Condition Information
    condition_name VARCHAR(255) NOT NULL,
    mesh_term VARCHAR(255),

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Key Constraint
    FOREIGN KEY (study_id) REFERENCES studies(study_id) ON DELETE CASCADE
);

-- ============================================================================
-- Interventions Table
-- ============================================================================
-- Drugs, procedures, devices, or other interventions being studied
-- One-to-Many relationship with studies
-- ============================================================================

CREATE TABLE interventions (
    -- Primary Key
    intervention_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign Key
    study_id INTEGER NOT NULL,

    -- Intervention Information
    intervention_type VARCHAR(50),  -- Drug, Procedure, Device, etc.
    name VARCHAR(255) NOT NULL,
    description TEXT,
    other_names TEXT,  -- Alternative names

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Key Constraint
    FOREIGN KEY (study_id) REFERENCES studies(study_id) ON DELETE CASCADE
);

-- ============================================================================
-- Outcomes Table
-- ============================================================================
-- Primary and secondary outcome measures
-- One-to-Many relationship with studies
-- ============================================================================

CREATE TABLE outcomes (
    -- Primary Key
    outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign Key
    study_id INTEGER NOT NULL,

    -- Outcome Information
    outcome_type VARCHAR(20),  -- 'Primary' or 'Secondary'
    measure TEXT NOT NULL,
    time_frame VARCHAR(255),
    description TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (outcome_type IN ('Primary', 'Secondary', 'Other', NULL)),

    -- Foreign Key Constraint
    FOREIGN KEY (study_id) REFERENCES studies(study_id) ON DELETE CASCADE
);

-- ============================================================================
-- Sponsors Table
-- ============================================================================
-- Organizations funding or collaborating on the study
-- One-to-Many relationship with studies
-- ============================================================================

CREATE TABLE sponsors (
    -- Primary Key
    sponsor_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign Key
    study_id INTEGER NOT NULL,

    -- Sponsor Information
    agency VARCHAR(255) NOT NULL,
    agency_class VARCHAR(50),  -- 'NIH', 'Industry', 'Other', etc.
    lead_or_collaborator VARCHAR(20),  -- 'Lead' or 'Collaborator'

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (lead_or_collaborator IN ('Lead', 'Collaborator', NULL)),

    -- Foreign Key Constraint
    FOREIGN KEY (study_id) REFERENCES studies(study_id) ON DELETE CASCADE
);

-- ============================================================================
-- Locations Table
-- ============================================================================
-- Geographic locations where studies are conducted
-- One-to-Many relationship with studies (studies often have multiple sites)
-- ============================================================================

CREATE TABLE locations (
    -- Primary Key
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign Key
    study_id INTEGER NOT NULL,

    -- Location Information
    facility VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    country VARCHAR(100),
    continent VARCHAR(50),

    -- Status
    status VARCHAR(50),  -- 'Recruiting', 'Active', 'Completed', etc.

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Key Constraint
    FOREIGN KEY (study_id) REFERENCES studies(study_id) ON DELETE CASCADE
);

-- ============================================================================
-- Study Design Table
-- ============================================================================
-- Detailed study design characteristics
-- One-to-One relationship with studies
-- ============================================================================

CREATE TABLE study_design (
    -- Primary Key
    design_id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Foreign Key (One-to-One)
    study_id INTEGER UNIQUE NOT NULL,

    -- Design Information
    allocation VARCHAR(50),  -- 'Randomized', 'Non-Randomized', etc.
    intervention_model VARCHAR(100),  -- 'Parallel', 'Crossover', etc.
    masking VARCHAR(100),  -- 'None', 'Single', 'Double', 'Triple', 'Quadruple'
    primary_purpose VARCHAR(50),  -- 'Treatment', 'Prevention', etc.

    -- For Observational Studies
    observational_model VARCHAR(50),  -- 'Cohort', 'Case-Control', etc.
    time_perspective VARCHAR(50),  -- 'Prospective', 'Retrospective', etc.

    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Key Constraint
    FOREIGN KEY (study_id) REFERENCES studies(study_id) ON DELETE CASCADE
);

-- ============================================================================
-- Views for Common Queries
-- ============================================================================

-- Complete study information view
CREATE VIEW v_study_complete AS
SELECT
    s.*,
    sd.allocation,
    sd.intervention_model,
    sd.masking,
    sd.primary_purpose,
    COUNT(DISTINCT l.location_id) as location_count,
    COUNT(DISTINCT c.condition_id) as condition_count,
    COUNT(DISTINCT i.intervention_id) as intervention_count
FROM studies s
LEFT JOIN study_design sd ON s.study_id = sd.study_id
LEFT JOIN locations l ON s.study_id = l.study_id
LEFT JOIN conditions c ON s.study_id = c.study_id
LEFT JOIN interventions i ON s.study_id = i.study_id
GROUP BY s.study_id;

-- ============================================================================
-- Database Metadata
-- ============================================================================

-- Create a metadata table to track schema version
CREATE TABLE IF NOT EXISTS schema_metadata (
    version VARCHAR(20) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_metadata (version, description)
VALUES ('1.0.0', 'Initial schema creation with all core tables and indexes');

-- ============================================================================
-- Success Message
-- ============================================================================
-- If you see this without errors, the schema was created successfully!
-- ============================================================================
