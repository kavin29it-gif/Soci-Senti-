# Privacy, Ethics, and Data Governance Policy

## 1. Core Principles
SociSenti is built on the fundamental principle that social intelligence platforms must respect human dignity, data privacy laws (GDPR, CCPA), and the terms of service of public data providers.

### 1.1 Human-in-the-Loop Decision Making
- **No Automated Enforcement:** The platform NEVER autonomously bans, mutes, reports, or penalizes accounts or content.
- **Decision Support Only:** All risk scores, SHAP explanations, and anomaly flags are recommendations designed solely to assist human compliance analysts and fraud investigators in triaging potential threats.

---

## 2. Pseudonymization & Cryptographic Hashing
- **Salted SHA-256 Identifiers:** User handles, platform user IDs, and author identifiers are hashed immediately upon ingestion using a server-side salt (`AUTHOR_HASH_SALT`).
- **Handle Protection:** By default, raw usernames and handles are never stored (`STORE_RAW_HANDLES=false`).
- **Non-Reversibility:** Without the private master salt, third parties cannot cross-reference ingested social media entities with external personal data.

---

## 3. Aggregate-Only Demographic Inference
To prevent profiling and respect anti-discrimination regulations:
- **No Individual Protected Attributes:** The platform does NOT infer, predict, or store age, gender, race, religious affiliation, or political identity at the individual user level.
- **$k$-Anonymity Cohort Threshold:** Demographic distributions are only aggregated across cohorts with a minimum size of $k \ge 50$. Any cohort or bucket with fewer than 50 observations is strictly suppressed from queries and dashboard visualizations.
- **Differential Privacy Noise:** Small calibrated Laplace noise ($\epsilon = 0.5$) is injected into public-facing aggregate counters to prevent reconstruction attacks.
- **Automated Persist Checks:** Automated unit tests run on every commit to ensure that no individual demographic attributes can be written to the database.

---

## 4. Retention & Data Minimization
- **Retention Windows:** Raw social media payloads are retained for a configurable window (default 90 days), after which automated cleanup jobs purge expired records.
- **Evidence Snapshots:** Only content items explicitly attached to open investigation cases are retained under strict access controls for regulatory compliance reporting.
- **Audit Immutability:** Audit records track when and by whom any data item was viewed or added to a case file, ensuring full accountability.
