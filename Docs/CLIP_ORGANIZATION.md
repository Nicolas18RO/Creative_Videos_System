# AICOS — Clip Organization Module
## Feature Specification & Phased Implementation Plan

**Branch:** `feature/clip-organization`  
**Module:** Clip Organization (M4)  
**Status:** Planning / awaiting implementation  
**Project:** AICOS — AI Creative Operating System

---

## 1. Purpose of this document

This document is the working contract for implementing the **Clip Organization** module in AICOS.

It is intentionally focused on the organization responsibility and must remain compatible with:

- the current AICOS architecture;
- the existing library taxonomy;
- the current SQLite/Chroma architecture;
- the future Clip Intelligence system;
- the future ML/classification layers;
- the local-first philosophy.

The module must be implemented **incrementally and with verification gates**.

### Golden rule

> **Never advance to the next phase while the current phase has failing tests or unresolved acceptance criteria.**

The coding agent must plan first, wait for approval, implement one phase at a time, run the required verification, report the result, and stop before continuing.

---

# 2. How to use this document with Cursor

The recommended first instruction is:

> **Read `AGENTS.md` and this document completely. Also inspect the current AICOS architecture and the existing Clip Organizer implementation. Do not modify code yet. Propose Phase 1 as a small, testable plan, including files that would change, tests to add/run, risks, and acceptance criteria. Wait for my approval before making changes.**

After approving a phase:

> **Implement only the approved phase. Do not begin the next phase. Run all required tests and verification commands for this phase. If any test fails, stop, diagnose the failure, fix only what belongs to this phase, and rerun the tests. At the end, report changed files, tests executed, results, remaining risks, and whether the phase is ready for approval.**

The agent must treat this document as a **feature contract**, not as permission to redesign unrelated parts of AICOS.

---

# 3. Current architectural context

## 3.1 Current AICOS architecture

The current system is approximately:

```text
React + Vite
      │
      ▼
FastAPI
      │
      ▼
Application / Services
      │
      ▼
Domain / Infrastructure
      │
      ├── SQLite
      ├── ChromaDB
      ├── Filesystem
      ├── FFmpeg / FFprobe
      └── Local AI services
```

The canonical clip identity is the `clips` database record.

Important current structures include:

- `clips`
- `clip_cinematic_metadata`
- `clip_visual_embeddings`
- `clip_semantic_metadata`
- `editorial_metadata`
- `editorial_feedback`
- `recommendations`
- `scenes`
- `usage_events`
- `clip_usage_history`

The Clip Organization module must reuse these structures where appropriate instead of creating duplicate concepts.

---

# 4. What M4 Clip Organization is

M4 is responsible for **organizing physical clip files and applying approved taxonomy-based organization decisions**.

Conceptually:

```text
Existing Clip
     │
     ▼
Classification / Existing Metadata
     │
     ▼
Organization Proposal
     │
     ▼
Validation
     │
     ▼
Human Approval
     │
     ▼
Move / Rename
     │
     ▼
Database Synchronization
     │
     ▼
Verification
```

M4 is therefore an **execution and organization module**.

It is not responsible for becoming the future Clip Intelligence engine.

---

# 5. What M4 is NOT

M4 must not become responsible for:

- object detection;
- VLM analysis;
- OCR;
- audio transcription;
- visual embeddings;
- unsupervised clustering;
- learning-to-rank;
- preference learning;
- genetic algorithms;
- autonomous editorial learning;
- automatic training of ML models.

Those capabilities belong to future intelligence/ML layers.

The future architecture should instead allow:

```text
Clip Intelligence
       │
       ▼
Classification
       │
       ▼
Organization Proposal
       │
       ▼
M4 Organizer
```

---

# 6. Existing library taxonomy

The current library taxonomy is already an important part of AICOS.

The organizer must preserve it.

The current taxonomy has five conceptual axes:

```text
1. Gender
2. Narrative Function
3. Subcategory
4. Context
5. Variant
```

Examples of existing narrative functions include:

- HOOK
- PROBLEM
- BENEFIT
- RESULT
- AUTHORITY
- SOCIAL_PROOF
- NATURAL
- CTA

Example historical naming convention:

```text
F_PROBLEM_BACK_PAIN_POSTURE_01.mp4
```

This should be treated as an existing editorial/library convention, not replaced by a new taxonomy during this feature.

---

# 7. Critical conceptual distinction

The organizer must distinguish between:

### Library taxonomy

Where/how a clip is organized physically.

### Clip Intelligence

What the clip actually contains or what an AI infers about it.

For example:

```text
Filename:
F_PROBLEM_BACK_PAIN_POSTURE_01.mp4

Library taxonomy:
Gender = F
Function = PROBLEM
Context = BACK_PAIN_POSTURE
Variant = 01
```

Future Clip Intelligence could independently infer:

```text
People = 1
Action = touching lower back
Environment = indoor
Emotion = apparent discomfort
Shot = medium shot
Potential uses = PROBLEM, HOOK, EMOTION
```

These are not the same data.

---

# 8. Multi-use principle

A physical clip must not be duplicated merely because it can have multiple editorial uses.

A future clip could potentially be:

```text
PROBLEM
HOOK
EMOTION
```

while remaining one physical asset.

Therefore:

```text
ONE PHYSICAL CLIP
        │
        ├── Library taxonomy
        │
        ├── Observed intelligence
        │
        ├── Inferred intelligence
        │
        ├── Potential editorial uses
        │
        └── Actual usage history
```

M4 should not solve the entire multi-use editorial model unless a specific approved phase requires it.

---

# 9. Current implementation baseline

Before changing anything, Cursor must inspect and report the actual current implementation.

Known areas to inspect include:

- `aicos/modules/clip_organizer.py`
- organizer FastAPI route(s)
- `library_service`
- taxonomy parser
- `ClipRow`
- filesystem/path utilities
- bootstrap/indexing flow
- existing organizer tests
- library API
- React library UI
- configuration for `library_root`
- configuration related to `incoming_folder`
- any watcher/auto-classification behavior.

The agent must not assume that the current code matches this document.

**Code is the source of truth for current implementation.**

---

# 10. Safety requirements

Physical filesystem operations are high-risk compared with pure classification.

The organizer must therefore prioritize:

1. path safety;
2. deterministic behavior;
3. no accidental overwrite;
4. no silent data loss;
5. database/filesystem consistency;
6. dry-run/proposal behavior before destructive execution;
7. testability.

The default behavior for new organization logic should favor **proposal/dry-run** over immediate movement.

---

# 11. Proposed phase roadmap

The following phases are the working plan. They are intentionally small enough to verify independently.

## Phase 0 — Discovery and baseline

### Goal

Understand the current implementation before modifying it.

### Tasks

- inspect current organizer;
- inspect taxonomy parser;
- inspect library service;
- inspect database model;
- inspect routes;
- inspect existing tests;
- inspect configuration;
- identify existing gaps;
- run the current relevant test suite.

### Deliverables

A short report containing:

- current flow;
- current files;
- current tests;
- known defects;
- proposed changes;
- baseline test result.

### Gate

Do not modify production code.

Phase 0 is complete only when the current state is understood and baseline tests are recorded.

---

# Phase 1 — Define organization domain contract

### Goal

Make the organizer's responsibility explicit before changing behavior.

Define conceptually:

```text
Clip
  ↓
Organization Input
  ↓
Organization Decision
  ↓
Organization Proposal
  ↓
Organization Result
```

The phase should establish:

- source path;
- current taxonomy;
- proposed destination;
- proposed filename;
- confidence/eligibility if already available;
- reason for the proposal;
- dry-run/apply distinction;
- collision behavior;
- invalid path behavior.

Do not introduce unnecessary database tables.

### Tests

Unit tests for:

- valid organization input;
- invalid taxonomy;
- destination calculation;
- deterministic destination calculation;
- filename generation;
- collision detection;
- unsafe path rejection.

### Gate

All Phase 1 tests must pass.

---

# Phase 2 — Safe organization proposal / dry-run

### Goal

Allow AICOS to calculate what would happen without touching the filesystem.

Example:

```text
SOURCE
E:/CREATIVE VIDEOS/CLIPS_MASTER/...

        ↓

PROPOSAL

Destination:
E:/CREATIVE VIDEOS/CLIPS_MASTER/F/PROBLEM/...

New filename:
F_PROBLEM_BACK_PAIN_POSTURE_01.mp4

Action:
MOVE

Risk:
NONE / COLLISION / INVALID / ...
```

### Requirements

Dry-run must:

- perform no move;
- perform no rename;
- not delete files;
- report proposed source and destination;
- detect collisions;
- be deterministic.

### Tests

Test:

- correct destination;
- correct filename;
- collision;
- missing source;
- invalid destination;
- repeated dry-run produces the same proposal;
- dry-run leaves filesystem unchanged.

### Gate

All tests pass before proceeding.

---

# Phase 3 — Safe filesystem execution

### Goal

Execute an approved organization proposal.

Flow:

```text
Proposal
   │
   ▼
Validate again
   │
   ▼
Check source
   │
   ▼
Check destination
   │
   ▼
Move / Rename
   │
   ▼
Verify destination
```

### Requirements

The operation must:

- never silently overwrite an existing unrelated file;
- verify the source;
- validate destination;
- perform the move;
- verify the resulting file exists;
- report failures explicitly.

If a move fails, the system must not falsely report success.

### Tests

Use temporary directories and test:

- successful move;
- successful rename;
- missing source;
- destination collision;
- invalid path;
- permission/error handling where practical;
- post-move verification;
- no false success.

### Gate

All filesystem tests pass.

---

# Phase 4 — Database synchronization

### Goal

Ensure SQLite remains consistent with the physical filesystem after organization.

The organizer must carefully update the clip's path-related database state after a successful physical move.

Conceptually:

```text
Filesystem
     │
     │ successful move
     ▼
Database update
     │
     ▼
Verification
```

Important:

> The database must not claim the new path if the physical operation failed.

### Tests

Test:

- successful move + database update;
- failed move + database unchanged;
- path consistency;
- repeated operation behavior;
- rollback/error handling where applicable.

### Gate

All database synchronization tests pass.

---

# Phase 5 — API contract

### Goal

Expose organization safely through FastAPI.

The API should support the concepts already present in the application rather than introducing unnecessary endpoints.

Potential operations:

```text
Preview organization
Apply approved organization
Get organization result
```

Exact endpoint design must be determined after inspecting current routes.

### Tests

API/integration tests must cover:

- valid request;
- invalid request;
- dry-run;
- successful apply;
- collision;
- missing clip;
- filesystem/database consistency;
- correct HTTP error responses.

### Gate

Backend tests pass.

---

# Phase 6 — React integration

### Goal

Allow the user to review and execute organization from the current React interface.

The UI should not own filesystem logic.

Architecture:

```text
React
  │
  │ request
  ▼
FastAPI
  │
  ▼
Organizer Service
  │
  ├── Filesystem
  └── Database
```

Potential UX:

```text
Clip
 ↓
Organization proposal
 ↓
Review
 ↓
Apply
```

The UI should clearly distinguish:

- current location;
- proposed location;
- proposed name;
- reason;
- warnings;
- collision;
- confirmation.

### Tests

At minimum:

- API integration;
- component behavior;
- error state;
- successful organization flow;
- no accidental apply during preview.

Browser/E2E checks should be used for the final user-visible flow where the project's testing setup supports them.

### Gate

All automated tests pass and the main UI flow is manually verified.

---

# Phase 7 — Integration with future Clip Intelligence

This phase should **not** block the basic organizer implementation.

The goal is architectural compatibility.

Future flow (FUTURE / NOT implemented; see §12.1 for intake):

```text
Intake (folder or drag-and-drop)
       │
       ▼
Ingestion
       │
       ▼
Clip Intelligence
       │
       ▼
Classification
       │
       ▼
Organization Proposal
       │
       ▼
Human Review
       │
       ▼
M4 Organizer
```

The organizer should consume a clear classification/organization decision rather than knowing how AI classification was produced.

This keeps M4 independent from:

- YOLO;
- VLMs;
- OCR;
- Whisper;
- OpenCLIP;
- clustering;
- future ML models.

---

# 12. Future ML compatibility

The organizer should not store model-specific assumptions in its core logic.

Future intelligence may produce:

```text
classification:
  function: PROBLEM
  confidence: 0.91
  source: model
  model_version: ...
```

or:

```text
classification:
  function: PROBLEM
  confidence: 0.98
  source: human
```

The organizer's job is to act on an approved organization decision.

---

# 12.1 Future ingestion of unclassified clips (NOT implemented)

Status: FUTURE. Not implemented. Does not change M4 behavior.

M4 can consume an external organization decision. React today works mainly with clips
already registered in SQLite. A new, unclassified clip has no integrated entry from an
intake zone into intelligence, so it cannot be visually exercised as a first-class
unclassified asset.

Future AICOS must support two intake points for clips that have not yet been analyzed.
Neither point is the final library (`library_root`).

1. Temporary ingestion folder (configured later, not active now):

   `C:\Users\nicor\Videos\Clips_Temporal`

   This folder is a staging intake zone for pending analysis. It must not be treated
   as the classified library.

2. React drag-and-drop of a single video file onto an analysis drop zone.

Expected future flow (same for both entry points):

```text
Intake (folder or drag-and-drop)
       │
       ▼
Ingestion
       │
       ▼
Clip Intelligence
       │
       ▼
Classification / metadata
       │
       ▼
Organization proposal
       │
       ▼
Human review when required
       │
       ▼
M4 Clip Organization
       │
       ▼
Move / rename + SQLite update
```

Separation of responsibilities:

- Ingestion = receive a new file (folder or drag-and-drop). Not M4.
- Clip Intelligence = future content analysis. Not implemented here.
- Classification = produce taxonomy/metadata and an organization decision.
- Human review = approve or correct that decision when required.
- M4 = execute a validated organization decision only. M4 does not ingest,
  does not run Clip Intelligence, and does not choose models (YOLO, VLM, OCR,
  Whisper, OpenCLIP, clustering, or learning).

The physical path `C:\Users\nicor\Videos\Clips_Temporal` is a future configuration
requirement. It is not an active setting and must not be treated as the current
`incoming_folder` in `config.yaml`.

This flow must later allow analysis of new clips without depending on a
taxonomy-compliant filename.

---

# 13. Verification strategy

Every phase must follow:

```text
PLAN
  ↓
APPROVAL
  ↓
IMPLEMENT
  ↓
TEST
  ↓
REVIEW
  ↓
PASS?
 ┌───────┴───────┐
 NO              YES
 │                │
FIX               STOP
 │                │
TEST AGAIN        WAIT FOR APPROVAL
```

### No phase skipping

The agent must not say:

> "The next phase is straightforward, so I implemented it too."

That is prohibited.

Each phase requires explicit approval before the next phase begins.

---

# 14. Test categories

The implementation should favor the smallest appropriate test.

### Unit tests

Pure logic:

- taxonomy;
- path calculation;
- filename generation;
- collision rules;
- validation.

### Integration tests

Interactions:

- organizer + filesystem;
- organizer + SQLite;
- API + organizer;
- database/path synchronization.

### End-to-end / UI tests

Only where necessary:

- preview organization;
- review;
- confirmation;
- apply;
- result display.

---

# 15. Filesystem testing rule

Tests must never operate on the real production library:

```text
E:/CREATIVE VIDEOS/CLIPS_MASTER
```

Tests should use temporary directories or isolated test fixtures.

No test should move, rename, delete, or overwrite real library files.

---

# 16. Production safety rule

Until the module is proven reliable:

```text
DRY RUN = DEFAULT / SAFE PATH
APPLY = EXPLICIT
```

The system must not automatically move files merely because an AI classification exists.

---

# 17. Scope control

During this feature, Cursor must not perform unrelated refactors such as:

- migrating documentation;
- replacing React;
- changing FastAPI architecture;
- replacing SQLite;
- replacing Chroma;
- redesigning taxonomy;
- enabling OpenAI;
- enabling OpenCLIP globally;
- implementing Clip Intelligence;
- implementing clustering;
- implementing ML training;
- implementing genetic algorithms;
- redesigning unrelated modules.

If an unrelated architectural problem is discovered, report it separately.

---

# 18. Definition of Done

Clip Organization is considered complete only when:

- [ ] current organizer behavior is understood;
- [ ] organization contract is documented;
- [ ] dry-run works;
- [ ] path safety is tested;
- [ ] collision behavior is tested;
- [ ] filesystem execution is tested;
- [ ] database synchronization is tested;
- [ ] API integration is tested;
- [ ] React flow is integrated where applicable;
- [ ] production library is never used by tests;
- [ ] all relevant automated tests pass;
- [ ] final user-visible flow is verified;
- [ ] no unrelated architecture was changed;
- [ ] current architecture documentation is updated only after implementation is actually verified.

---

# 19. Required agent report after every phase

At the end of every phase, Cursor must report:

```text
PHASE:
Status: PASS / BLOCKED

Implemented:
- ...

Files changed:
- ...

Tests executed:
- ...

Test result:
- ...

Verification:
- ...

Known issues:
- ...

Architecture changes:
- None / ...

Ready for next phase:
- YES / NO
```

If status is `BLOCKED`, stop.

---

# 20. Git workflow

The feature is developed on:

```bash
feature/clip-organization
```

Before starting implementation, ensure the previous frontend migration work is committed and pushed.

Recommended flow:

```bash
git status
git add .
git commit -m "feat: complete React frontend migration"
git push origin feature/migration-frontend-python-to-react
```

Then create the feature branch:

```bash
git checkout -b feature/clip-organization
```

Publish it:

```bash
git push -u origin feature/clip-organization
```

During implementation, prefer small commits aligned with verified phases.

Example:

```bash
git add .
git commit -m "feat: define clip organization contract"
git push
```

Then:

```text
Phase 1 PASS
    ↓
commit
    ↓
Phase 2
    ↓
tests PASS
    ↓
commit
```

Do not create a giant commit containing the entire module.

---

# 21. Relationship with AICOS documentation

This document is a **feature-level implementation specification**.

It does not replace:

- the global PRD;
- the technical design;
- the current architecture document;
- ADRs.

If implementation reveals an architectural decision that affects the whole system, stop and propose the required documentation change before continuing.

---

# 22. Final architectural target

The intended long-term architecture is:

```text
                    ┌─────────────────────┐
                    │     CLIP FILE       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  CLIP INTELLIGENCE │
                    │      (future)       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   CLASSIFICATION    │
                    │      (future)       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ ORGANIZATION        │
                    │     PROPOSAL        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   HUMAN REVIEW      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       M4            │
                    │ CLIP ORGANIZER      │
                    └──────────┬──────────┘
                               │
                     ┌─────────┴─────────┐
                     ▼                   ▼
                FILESYSTEM           SQLITE
```

The key architectural principle is:

> **Intelligence decides what a clip is and proposes how it could be organized. M4 executes a validated organization decision safely.**

---

# 23. First Cursor command

Once this file and the project instructions are available to Cursor, use:

> **Read `AGENTS.md` and `docs/CLIP_ORGANIZATION.md` completely. Inspect the current AICOS architecture and the existing Clip Organization/M4 implementation. Do not modify code or documentation yet. Propose Phase 0 only: discovery and baseline. List the exact files you inspected, the current organization flow, existing tests, commands you will run, risks discovered, and acceptance criteria. Wait for my approval before doing anything else.**
