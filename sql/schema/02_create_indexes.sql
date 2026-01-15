-- ============================================================================
-- Clinical Trial Analytics - Database Indexes
-- ============================================================================
-- This script creates indexes for performance optimization
-- Run AFTER 01_create_tables.sql
-- ============================================================================

-- ============================================================================
-- Studies Table Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_studies_status ON studies(status);
CREATE INDEX IF NOT EXISTS idx_studies_phase ON studies(phase);
CREATE INDEX IF NOT EXISTS idx_studies_study_type ON studies(study_type);
CREATE INDEX IF NOT EXISTS idx_studies_start_date ON studies(start_date);
CREATE INDEX IF NOT EXISTS idx_studies_completion_date ON studies(completion_date);
CREATE INDEX IF NOT EXISTS idx_studies_enrollment ON studies(enrollment);
CREATE INDEX IF NOT EXISTS idx_studies_dates ON studies(start_date, completion_date);

-- ============================================================================
-- Conditions Table Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_conditions_study_id ON conditions(study_id);
CREATE INDEX IF NOT EXISTS idx_conditions_name ON conditions(condition_name);
CREATE INDEX IF NOT EXISTS idx_conditions_mesh_term ON conditions(mesh_term);

-- ============================================================================
-- Interventions Table Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_interventions_study_id ON interventions(study_id);
CREATE INDEX IF NOT EXISTS idx_interventions_type ON interventions(intervention_type);
CREATE INDEX IF NOT EXISTS idx_interventions_name ON interventions(name);

-- ============================================================================
-- Outcomes Table Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_outcomes_study_id ON outcomes(study_id);
CREATE INDEX IF NOT EXISTS idx_outcomes_type ON outcomes(outcome_type);

-- ============================================================================
-- Sponsors Table Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_sponsors_study_id ON sponsors(study_id);
CREATE INDEX IF NOT EXISTS idx_sponsors_agency ON sponsors(agency);
CREATE INDEX IF NOT EXISTS idx_sponsors_agency_class ON sponsors(agency_class);
CREATE INDEX IF NOT EXISTS idx_sponsors_lead_or_collab ON sponsors(lead_or_collaborator);

-- ============================================================================
-- Locations Table Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_locations_study_id ON locations(study_id);
CREATE INDEX IF NOT EXISTS idx_locations_country ON locations(country);
CREATE INDEX IF NOT EXISTS idx_locations_continent ON locations(continent);
CREATE INDEX IF NOT EXISTS idx_locations_city ON locations(city);
CREATE INDEX IF NOT EXISTS idx_locations_country_continent ON locations(country, continent);

-- ============================================================================
-- Study Design Table Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_study_design_study_id ON study_design(study_id);
CREATE INDEX IF NOT EXISTS idx_study_design_allocation ON study_design(allocation);
CREATE INDEX IF NOT EXISTS idx_study_design_primary_purpose ON study_design(primary_purpose);
