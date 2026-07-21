# Clover Talent Intelligence Platform
### Requirements, Architecture & Research — Project A (ATS Matching) + Project B (Bench Deployment Engine)

---

## 0. Executive Summary

You're really building **one platform with two applications on top of it**, not two unrelated systems. Both need the same core capability: turn a resume/profile into structured, comparable data, then match it against a requirement (a JD or a project spec) and produce an explainable score.

- **Project A** = External/portal-facing: match *applicant resumes* → *open job roles* on the Clover portal, replacing manual one-by-one HR screening with an ATS score + ranked shortlist.
- **Project B** = Internal: match *bench employees* → *new project requirements*, bench candidates get first-priority visibility to HR before external hiring is even considered.

Building a shared **Matching Engine + Resume/Profile Parser** underneath both saves a huge amount of duplicate work for your two teams and is the single biggest architectural decision below.

---

## 1. Project A — ATS Resume-to-JD Matching Engine

### 1.1 Problem statement
HR currently reviews every resume manually against every open JD across multiple roles. No standard scoring, no central JD/candidate repository, slow and inconsistent shortlisting.

### 1.2 Goals
- Central repository of all JDs (per role, per department) and all candidate resumes.
- Auto-parse resumes → structured profile (skills, total experience, relevant experience, education, certifications, past companies, location, notice period).
- Auto-generate an **ATS match %** per candidate per JD, with a breakdown of *why*.
- HR sees a ranked list per JD with resume + score, instead of reading every resume cold.

### 1.3 Core features
1. **Bulk resume ingestion** — upload (PDF/DOCX), email-to-portal, or bulk zip upload.
2. **Resume parser** — extracts structured fields (see 1.6).
3. **JD builder** — structured JD with must-have skills, good-to-have skills, min/max experience, education, location, budget/CTC band.
4. **Matching engine** — produces 0–100% match score per candidate-JD pair.
5. **Ranked dashboard** — sortable/filterable list of candidates per JD, with score, resume preview, and a "why this score" breakdown.
6. **Duplicate detection** — same candidate applying to multiple roles / re-uploading old resume.
7. **Status pipeline** — Applied → Shortlisted → Interview → Offer → Rejected, with audit trail.
8. **Search** — natural-language / filter search across all resumes ("5+ yrs React, Mumbai, notice period <30 days").
9. **Notifications** — auto email/SMS to candidates on status change (optional, phase 2).

### 1.4 User roles
- **Recruiter/HR** — creates JD, reviews ranked candidates, moves pipeline stage.
- **Hiring Manager** — reviews shortlist, gives feedback/approval.
- **Admin** — manages roles, JD templates, scoring weights.
- **Candidate** (optional portal login) — uploads resume, tracks application status.

### 1.5 System flow
```
Candidate/HR uploads resume
        │
        ▼
Resume Parser (extract structured JSON)
        │
        ▼
Store in DB + generate embedding vector
        │
        ▼
On JD creation → generate JD embedding + structured requirement JSON
        │
        ▼
Matching Engine runs (hybrid scoring, see 1.6)
        │
        ▼
Score + breakdown stored, ranked list surfaced to HR dashboard
        │
        ▼
HR reviews top-N → moves candidate through pipeline
```

### 1.6 Matching algorithm (this is the core IP — design it as a hybrid, not a single model)

Pure keyword-matching ATS (old-school) gives poor results — it misses synonyms ("ReactJS" vs "React.js") and can't judge seniority. Pure LLM-only scoring is too slow/expensive to run on thousands of resumes per JD and is hard to explain to HR. **Use a hybrid, in this order:**

**Stage 1 — Hard filters (cheap, instant, rule-based)**
- Minimum/maximum total experience
- Mandatory education level
- Mandatory certifications (if any)
- Location / work-authorization constraints
- Notice period ceiling
→ Anything failing a hard filter is excluded or flagged, not scored further (saves compute).

**Stage 2 — Weighted structured scoring**
| Component | Example weight | Logic |
|---|---|---|
| Must-have skills match | 40% | Exact + synonym match against a skills taxonomy |
| Good-to-have skills match | 15% | Same, lower weight |
| Relevant experience (years in matching domain, not just total years) | 20% | Overlap between JD-required domain and candidate's tagged project experience |
| Education fit | 10% | Degree/branch match |
| Semantic similarity (JD description ↔ resume summary) | 15% | Cosine similarity of embeddings — catches things keyword rules miss |

**Stage 3 — Semantic re-ranking (only on top-K, e.g. top 50 per JD)**
- Run a single LLM call per shortlisted candidate to sanity-check the score, generate a 2–3 line "why this match" explanation, and catch resume-JD mismatches the rule engine missed (e.g., candidate lists a skill once in passing vs. as core experience).
- Keeping the LLM call limited to top-K (not all applicants) is the key cost lever — see Section 7.

**Skills taxonomy is the thing to invest in early** — a normalized skill dictionary (React = ReactJS = React.js = one node) is what makes both keyword and embedding matching actually reliable. Build this as its own reusable service; Project B needs the exact same taxonomy.

### 1.7 Data model (simplified)
```
candidates (id, name, email, phone, location, total_exp_years, current_ctc,
            notice_period_days, resume_file_url, parsed_json, embedding_vector,
            created_at)

jobs (id, title, department, must_have_skills[], good_to_have_skills[],
      min_exp, max_exp, education_req, location, jd_text, jd_embedding,
      status, created_by)

applications (id, candidate_id, job_id, match_score, score_breakdown_json,
              stage, ats_explanation_text, applied_at, updated_at)

skills_taxonomy (id, canonical_name, aliases[], category)
```

### 1.8 Tech stack (Project A)
| Layer | Recommendation | Why |
|---|---|---|
| Resume parsing | Start with an ML-based parser API (e.g. Affinda-style, ~$800/mo base or credit-based options from ~$75/mo at lower volume) to launch fast; evaluate replacing with a self-hosted open-source parser (spaCy NER + layout-aware PDF extraction, or a small local LLM extraction pass) once volume justifies the engineering cost | Buying parsing accuracy on day one is much faster than building it; revisit build-vs-buy once you know monthly resume volume |
| Embeddings | Open-weight embedding model (e.g. `bge-small`/`e5` family) self-hosted, or a hosted embedding API for MVP | Open embedding models are now good enough for resume/JD similarity and avoid per-call cost at scale |
| Vector search | **pgvector** (Postgres extension) | For a company-scale dataset (thousands to low millions of resumes) pgvector matches or beats managed vector DBs on cost and removes an entire second system to operate — only move to Pinecone/Qdrant if you cross several million vectors or need extreme QPS |
| Primary DB | PostgreSQL | Structured JD/candidate/application data + pgvector in one place |
| Backend | Python (FastAPI) or Node.js (NestJS) | Team already has Python/FastAPI experience (per your Kineti-AI project) |
| LLM (re-ranking/explanation) | Groq-hosted Llama or similar fast/cheap inference API | Already proven in your Friday assistant stack; fast + inexpensive for short re-ranking calls |
| Frontend | React + Tailwind | Standard, fast to build dashboards |
| File storage | S3-compatible object storage | Resume files |
| Auth | JWT + role-based access control | HR/Manager/Admin/Candidate roles |
| Background jobs | Celery / BullMQ + Redis | Parsing and embedding generation should be async, not blocking upload |

---

## 2. Project B — Bench-to-Project Deployment Engine (Internal Talent Marketplace)

### 2.1 Problem statement
When a new client project/requirement comes in, bench employees should be checked and prioritized *before* external hiring or fresh allocation, based on their actual tech stack experience and recent project history. Right now this matching is manual/tribal knowledge.

### 2.2 Goals
- Every bench employee has a living **skill + project profile** (not a static resume — updated from actual project history, not self-reported once).
- Every new company requirement gets auto-matched against the bench pool first.
- HR/Delivery gets a ranked, explainable shortlist of bench employees: *why this person, for this role, on this project*.
- Only if no strong bench match exists does the requirement fall through to external hiring (Project A).

### 2.3 Core features
1. **Bench employee profile** — auto-built from HRMS project history + manually maintained skill/cert additions, not a resume upload.
2. **New requirement intake form** — project name, client, required tech stack, seniority, duration, start date, headcount.
3. **Bench matching engine** — reuses the same taxonomy + scoring approach as Project A, but weighted differently (see 2.5).
4. **"First right of refusal" queue** — matched bench employees appear to HR/Delivery *before* the requirement is opened to external sourcing.
5. **Explainability card per match** — "Matched because: 3.4 yrs on React+Node projects, most recent project ended 2 weeks ago, tagged skill match: React, PostgreSQL, AWS."
6. **Bench utilization dashboard** — who's on bench, how long, what they're skilled in, upcoming availability.
7. **Skill-gap nudge** — if a bench employee is close-but-not-quite a match (e.g. missing one skill), suggest a targeted upskilling path so they qualify for future similar requirements.
8. **Notify employee** — bench employee gets notified they're being considered and for what, with the "why" explanation (transparency drives morale — this is a known pain point in tools like Gloat where explainability is weak).

### 2.4 System flow
```
New project requirement logged (tech stack, seniority, duration, client)
        │
        ▼
Requirement embedding + structured requirement JSON generated
        │
        ▼
Matching engine scores ALL current bench employees against requirement
        │
        ▼
Ranked bench shortlist surfaced to HR/Delivery FIRST
        │
        ▼
If strong match(es) exist → HR reviews, assigns
If no strong match → requirement flagged for external hiring (feeds into Project A)
        │
        ▼
Employee profile updated with new project assignment (feeds back into future matching)
```

### 2.5 Matching & prioritization logic
Same hybrid approach as Project A (hard filters → weighted scoring → LLM explanation), but reweighted:

| Component | Weight | Notes |
|---|---|---|
| Tech stack match (skills used in **actual recent projects**, not self-reported) | 35% | Weight recency — a skill used 3 months ago counts more than one used 3 years ago |
| Recency of bench availability | 20% | Someone on bench 1 week is prioritized differently than someone idle 3 months (business cost angle) |
| Seniority/role fit | 20% | Match required role level (junior/mid/senior/lead) |
| Domain/industry fit | 15% | e.g. worked in fintech before, new project is fintech |
| Growth/development fit | 10% | If employee has expressed interest in this tech direction — increases retention |

**Key design decision:** bench employees are matched *first and automatically surfaced*, before HR manually searches — this is the "first priority" behavior you described, implemented as a queue ordering rule, not a permission rule (external candidates aren't blocked, they're just shown second).

### 2.6 Data model (simplified)
```
employees (id, name, emp_code, current_status [bench/allocated], bench_since_date,
           skills_json, seniority_level, department, embedding_vector)

project_history (id, employee_id, project_name, client, tech_stack[],
                  role, start_date, end_date)

requirements (id, project_name, client, required_skills[], seniority_level,
              duration_months, start_date, headcount, status, requirement_embedding)

bench_matches (id, employee_id, requirement_id, match_score, score_breakdown_json,
               rank, status [suggested/reviewed/assigned/passed], created_at)
```

### 2.7 Tech stack (Project B)
Reuses almost everything from Project A's shared services (taxonomy, embeddings, pgvector, matching engine core) — the delta is mostly the requirement-intake UI, the bench dashboard, and the reweighted scoring config. This is exactly why building it as **one shared platform** matters (Section 3).

---

## 3. Shared Platform Architecture

Don't let the two teams build two separate matching engines — that's double the maintenance for the same core problem (structured profile ↔ structured requirement ↔ explainable score).

```
┌─────────────────────────────┐   ┌─────────────────────────────┐
│   Project A: ATS Portal UI   │   │  Project B: Bench Console UI │
└───────────────┬──────────────┘   └───────────────┬──────────────┘
                │                                   │
                ▼                                   ▼
        ┌───────────────────────────────────────────────────┐
        │              Shared Matching Engine API             │
        │  (hard filters → weighted score → LLM re-rank)      │
        └───────────────────────────┬─────────────────────────┘
                                    │
        ┌───────────────────────────┼─────────────────────────┐
        ▼                           ▼                          ▼
 ┌───────────────┐         ┌─────────────────┐        ┌────────────────┐
 │ Resume/Profile │         │ Skills Taxonomy  │        │ Embedding +     │
 │ Parser Service │         │ Service          │        │ pgvector Store  │
 └───────────────┘         └─────────────────┘        └────────────────┘
```

Both teams consume the same Matching Engine API with different config (weights, source data), which means one team can own the shared services while both feature teams build their own UI/workflow layer in parallel.

---

## 4. Tech stack summary (whole platform)

| Category | Choice | Notes |
|---|---|---|
| Backend framework | FastAPI (Python) | Fast to build, good async support, team already has Python momentum |
| Database | PostgreSQL + pgvector | One database for structured + vector data, no separate vector DB bill |
| Cache/queue | Redis + Celery (or BullMQ if Node) | Async parsing/embedding jobs |
| LLM inference | Groq API (Llama 3.1/3.3 class model) | Cheap, fast — reuse your existing Friday-assistant experience |
| Embeddings | Open-weight model (bge/e5 family), self-hosted or via a hosted inference endpoint | Avoids per-token embedding cost at high resume volume |
| Resume parsing | Buy (Affinda/RChilli-class API) for MVP → evaluate self-hosted parser later | Don't build a parser from scratch on day one; it's a solved problem you can buy cheaply at low volume |
| Frontend | React + Tailwind | Both dashboards, consistent design system |
| File storage | S3-compatible bucket | Resumes, JD docs |
| Auth | JWT + RBAC | Recruiter/Manager/Admin/Employee roles |
| Deployment | Docker + any cloud (AWS/GCP/Azure) | Whatever Clover's existing infra standard is |
| Observability | Basic logging + a dashboard (Grafana/simple admin panel) | You'll need to explain *why* a score was given — log the breakdown always |

---

## 5. Suggested rollout plan for 2 teams

| Phase | Team A (ATS Portal) | Team B (Bench Engine) | Shared work |
|---|---|---|---|
| Sprint 0 | — | — | Skills taxonomy v1, DB schema, pick parsing vendor, set up pgvector |
| Sprint 1–2 | JD builder + resume upload + parser integration | Employee profile builder from HRMS data | Shared Matching Engine v1 (hard filters + weighted scoring) |
| Sprint 3–4 | Ranked dashboard + pipeline stages | Requirement intake + bench ranked queue | LLM re-ranking + explanation layer |
| Sprint 5 | Search, duplicate detection | Skill-gap nudges, utilization dashboard | Notifications service |
| Sprint 6 | Candidate self-service status page (optional) | Feedback loop: assignment updates profile | Analytics/reporting layer for leadership |

---

## 6. Additional feature ideas worth considering

- **Explainability everywhere** — every score should show *why*, not just a number. Reviewers cited this as a real weakness in commercial tools like Eightfold/Gloat ("AI decision-making is difficult to audit"). Doing this well is a genuine differentiator, not a nice-to-have.
- **JD auto-generation** — HR types 3–4 bullet points, LLM drafts a full structured JD.
- **Natural-language candidate search** — "show me candidates with 4+ years React, based in Pune, notice period under 30 days" instead of dropdown filters.
- **Interview scheduling integration** (calendar auto-invite once shortlisted).
- **Bias/fairness check** — flag if scoring correlates suspiciously with non-job-relevant fields (gender-coded names, college tier, etc.) — important both ethically and because HR-tech regulation is tightening.
- **Predictive bench cost dashboard** — cost of bench idle time vs. cost of external hiring, to justify the "bench-first" policy with numbers leadership cares about.
- **Skill decay tracking** — a skill not used in 2+ years should be weighted lower for Project B matching than one just used.
- **Feedback loop** — when HR rejects a high-scoring match or accepts a low-scoring one, feed that back to recalibrate weights over time.

---

## 7. Cost optimization strategies

1. **Don't run an LLM call per resume.** Use the hard-filter + weighted-scoring stages (cheap, deterministic, near-instant) to narrow thousands of resumes down to a top-K (e.g., 50) per JD. Only run the LLM explanation/re-rank step on that top-K. This alone is the single biggest cost lever in the whole system.
2. **Self-host embeddings once volume justifies it.** A hosted embedding API is fine at MVP scale; once you're processing high resume volumes monthly, a self-hosted open-weight embedding model removes recurring per-call cost entirely.
3. **Use pgvector, not a managed vector database, at your scale.** Independent 2026 benchmarks show pgvector matching or beating Pinecone-class services on both cost and latency for corpora up to a few million vectors, while avoiding the operational overhead of running and syncing a second data store. Only reconsider this if you cross tens of millions of vectors company-wide.
4. **Buy resume parsing at MVP, don't build it.** Credit-based parsing APIs start in the ~$75–100/month range at low volume; compare per-parse cost against engineering time before building your own parser — building only pays off once your monthly resume volume is high enough that vendor cost exceeds engineering cost.
5. **Batch, don't stream, where you can.** Bench matching against new requirements and nightly resume re-scoring against open JDs can run as scheduled batch jobs on cheaper compute rather than real-time synchronous calls.
6. **Cache embeddings.** A JD or an employee profile doesn't need re-embedding every time it's matched — only re-embed on edit.
7. **Reuse one matching engine for both projects** (Section 3) instead of building and maintaining two — this is a development-cost saving, not just a runtime one.

---

## 8. Compliance — build this in from day one, not later

Both projects process resumes and employee data, which is personal data under India's **Digital Personal Data Protection Act (DPDP), 2023** — fully enforceable with rules notified in late 2025 and a compliance deadline running through 2027, with penalties reaching ₹250 crore for serious violations. Since you're a services company in Mumbai handling candidate and employee data at scale, treat this as a hard requirement, not an afterthought:

- **Consent** — while "employment purposes" processing has a legitimate-use exemption, best practice (and what most Indian HR-tech platforms are now doing) is still explicit, purpose-specific consent at resume upload and at bench-profile creation.
- **Audit logging** — every access to a candidate/employee record needs a timestamp, user ID, and access purpose logged — build this into the schema now (it's painful to retrofit).
- **Retention & deletion** — define and automate deletion of rejected candidate data after a set period (many Indian companies use ~180 days as a reference point); don't let resumes sit forever with no lifecycle.
- **Role-based access** — recruiters should not see full employee compensation/PII by default; scope access per role.
- **Breach protocol** — the Act requires breach notification to the Data Protection Board of India within 24 hours of discovery — make sure your incident response plan reflects this timeline from launch, not after an incident forces it.

---

## 9. Non-functional requirements

- **Performance**: JD-to-resume match should return for a JD with thousands of applicants in seconds, not minutes (hard-filter stage should be near-instant; LLM stage only runs on top-K).
- **Explainability**: every score must have a stored, retrievable breakdown — this is both a UX requirement and (per Section 8) increasingly a compliance expectation for automated decision-making.
- **Scalability**: design for company-wide employee count + expected annual applicant volume; pgvector comfortably handles this without needing a dedicated vector DB.
- **Security**: encrypted at rest and in transit, RBAC, audit trails (see Section 8).

---

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Resume parsing accuracy varies wildly by format (scanned, multi-column, creative layouts) | Test chosen parser against a real sample of your actual resume formats before committing; keep a manual-correction path in the UI |
| Bench matching becomes a black box HR doesn't trust | Explainability card (Section 6) on every match, always |
| Skills taxonomy drift (new tech terms, ambiguous aliases) | Assign one owner to the taxonomy service; review quarterly |
| Two teams silently diverge on scoring logic | Shared Matching Engine API (Section 3) with config-only differences, not forked code |
| Data privacy non-compliance | Bake in Section 8 requirements from Sprint 0, not as a later compliance sprint |

---

## 11. Reference points from the market (for context, not to copy)

- **Eightfold AI** — talent intelligence platform, ML-inferred skills from employee data (reduces manual profile-building), matches internal talent to roles using the same model it uses for external hiring, giving a market-benchmarked view of skill availability. Known weakness: AI decision-making reported as hard to audit.
- **Gloat** — internal talent marketplace, AI skill mapping, project/gig marketplace, workforce planning tools. Known weakness: fully AI-generated skills ontology with limited human curation, steep initial setup.
- **RChilli / Affinda / Textkernel(Sovren)** — established resume parsing APIs, credit or subscription priced, useful as a build-vs-buy reference point for Project A's parser.

Your version doesn't need to match these enterprise platforms feature-for-feature — the "bench gets first right of refusal, with a transparent explanation" workflow is a sharper, more focused version of what these tools do broadly, and is achievable with a small internal team using the architecture above.
