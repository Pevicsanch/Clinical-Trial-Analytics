# Technical Decisions

**Project**: Clinical Trial Analytics
**Data Source**: ClinicalTrials.gov API v2

---

## Key Architectural Decisions

### 1. Data Source & Limitations
- **Choice**: ClinicalTrials.gov API v2 (public, no authentication required)
- **Limitation**: 10,000 record sample for analysis (API constraint)
- **Impact**: Sufficient for analytical assessment and statistical validity

### 2. Database: SQLite
- **Choice**: SQLite over PostgreSQL
- **Rationale**: Zero-configuration setup, portable single-file database, sufficient for 10K records
- **Trade-off**: Not production-ready, but appropriate for analytical workload and assessment portability

### 3. API Client: WAF Mitigation Strategy
- **Problem**: Cloudflare WAF protection blocking standard HTTP clients
- **Solution**:
  - Browser simulation (User-Agent, Referer, Origin headers)
  - Session warm-up: visit homepage before API calls
  - `requests` library (different TLS fingerprint than `httpx`)
- **Result**: Successful download of 177MB (10,000 studies)

### 4. API Page Size Reduction
- **Choice**: `page_size = 100` (reduced from default 1000)
- **Rationale**: Large page sizes trigger WAF blocking; smaller pages more stable
- **Trade-off**: More requests, slightly slower, but reliable

### 5. ETL Architecture: Modular Pipeline
- **Structure**: Separate extract, transform, load, validate modules
- **Rationale**: Clean separation of concerns, testable components, reusable
- **Pattern**: Polars for heavy transformations, pandas for compatibility

### 6. Data Scope: Partial Loaders (4 of 7 Tables)
- **Implemented**: studies, conditions, locations, sponsors
- **Not Implemented**: interventions, outcomes, study_design
- **Rationale**: Core tables provide sufficient data for business questions (10K studies, 18K conditions, 64K locations)
- **Decision**: Prioritized analysis over complete ETL

### 7. Analysis Approach: Notebook-First
- **Choice**: Jupyter notebooks as primary analytical deliverable
- **Rationale**: Standard DA tool, shows thought process and exploration, appropriate for technical assessment
- **Alternative Rejected**: Dashboard would be over-engineering for assessment scope

### 8. Schema Design: Normalized (3NF)
- **Choice**: Normalized schema with 7 tables, foreign keys, constraints
- **Rationale**: Data integrity, query flexibility, demonstrates SQL modeling skills
- **Indexing**: 20+ indexes on common query patterns (status, phase, dates, conditions)

### 9. Configuration Management
- **Pattern**: Pydantic settings with environment variable override
- **Logging**: Console-first (optional file logging), appropriate for interactive DA workflows
- **Task Runner**: poethepoet + Makefile wrapper for cross-platform compatibility

### 10. Python Requirements
- **Version**: Python ≥3.11 (broader compatibility than 3.12)
- **Dependencies**: 18 runtime dependencies (minimal, focused)
- **Key Libraries**: requests, polars, pandas, sqlalchemy, plotly, statsmodels

---

## Data Quality Notes

**Current Database State**:
- studies: 10,000 records
- conditions: 17,973 records
- sponsors: 16,143 records
- locations: 64,198 records

**Known Limitations**:
- 10,000 record sample (not full database)
- 3 supplementary tables not implemented
- Sufficient for 4 of 5 business questions; 1 question may require creative approach

---

## Repository Structure Principles

- **Code**: Modular, DA-focused, pragmatic
- **Documentation**: Minimal, oriented to technical reviewers
- **Deliverables**: SQL queries, notebooks, visualizations, insights
