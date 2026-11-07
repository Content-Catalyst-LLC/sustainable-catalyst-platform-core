# ADR — Publications, Press, Research, Library and Workspace: product boundaries

**Decision date:** 2026-11-07
**Status:** Approved information architecture and documentation handoff; **not deployed, migrated, renamed, or published as a new site configuration**.
**Decision authority:** Sustainable Catalyst product owner.

## Decision

- **Publications** = the public-facing editorial website: **WordPress blog posts, articles, essays, commentary, explainers and research summaries**. WordPress remains the editorial CMS and website publishing surface.
- **Press** = the **public-facing identity of the existing Engagement & Communications capability**: media relations, press releases, institutional announcements, press kits, outreach, newsletters, audience/campaign planning and communications reporting, when their privacy and release gates are satisfied. This is a naming/product-boundary decision, **not an instruction to rename its GitHub repository, containers, URLs, database, services or API now**.
- **Research** = authenticated investigations: questions, hypotheses, study design, evidence evaluation, analysis, models, notebooks, graphs, findings and scientific manuscript preparation. Its public catalog lists reviewed metadata only. Formal scientific reports/papers remain Research-authoritative until an approved release; an editorial story about them may appear in Publications.
- **Library** = discovery, source capture, citation metadata, source files, provenance and knowledge preservation. Library is the authoritative source record; Research links authorized versioned sources rather than copying them by default.
- **Workspace** = coordination across products: projects, collaboration, milestones, owners, access controls, workflow status and review routing. Workspace's organizational project is not the same as Research's scientific investigation.
- **Lab/Workbench/Site Intelligence** = scientific compute, experiments, analysis, figures and geospatial/observational evidence. Research consumes verified outputs with provenance rather than duplicating computation tools.

## User journey

1. Discover and save sources in **Library**.
2. Link selected, authorized sources into a **Research** investigation and create analyses, figures, findings and reports.
3. Track the work in **Workspace**: collaborators, milestones, reviews, project deliverables. Workspace can be used throughout, not just as a final destination.
4. Prepare public-facing **WordPress Publications** posts and articles based on approved sources and findings. The source study/report stays linked with its original version and provenance.
5. When appropriate, **Press** prepares reviewed media statements, press releases, announcements, newsletter content and outreach that **reference** the approved publication and its authoritative sources.

**A handoff is a permission-checked link between governed objects, not a manual bulk file move, automatic public release, or cross-database merge.**

## Authority and boundary table

| Object or responsibility | System of record | Other products may |
| --- | --- | --- |
| Original scientific sources, DOI/citation metadata and source provenance | Library | Reference approved/versioned source IDs |
| Research questions, methods, experiments, analysis sessions, scientific findings and manuscript revision history | Research (with authorized source services for original notebooks and reports) | Link approved findings and releases |
| Shared project membership, work assignments, milestones and approvals | Workspace / existing identity authorization authority | Request scoped project links/permissions |
| Computation, lab experiments, plots, models and source geospatial imagery | Lab / Workbench / Site Intelligence respectively | Consume verified artifact references |
| WordPress editorial post, permalink, editorial categories, blog revision and public page | WordPress Publications | Link the published post; no second editorial CMS by default |
| Press release, newsroom announcement, campaign and media relations workflow | Existing Engagement & Communications, future Press surface | Refer to WordPress post and approved Research release |
| Inbound contact, feedback and support records | Existing authorized intake/support domains | Transfer only through reviewed privacy-purpose contracts; not silently absorbed into Press |

## Publication and Press release flow

- Scientific work can continue in private Research; **nothing becomes public solely because a source, report, or workspace exists**.
- An explicit, reviewable release record identifies the source version(s), rights/license, attributed authors, intended audience, release scope and approval.
- **Publications** edits and publishes its WordPress editorial article; it is not the source of truth for underlying scientific data.
- **Press** may create a press release or distribution plan **only from approved content** and must separately verify embargo, media claims, channel approvals, consent, suppression and delivery authorization.
- Source revision, withdrawal or correction must generate an actionable notice to dependent Publications and Press workflows; no silent mutation of already-published artifacts.
- No automatic import of contacts, public sharing of research manuscripts, unaudited cross-product writes, or outbound email activation.

## Present implementation versus future work

**Existing:** WordPress public editorial website; separate Research public metadata bridge with verified PostgreSQL status; private Research backend under development; separate Engagement & Communications code and extensive gated staging capabilities; independent Library and Workspace systems.

**Not certified by this decision:** shared-account SSO across all products, Library-to-Research link persistence, private Research owner access, automated WordPress publishing, approval-based Press publication and actual distribution. These require separate security, privacy, acceptance and deployment gates.

## Migration/handoff rules

1. Preserve **sustainable-catalyst-engagement-communications** repository identity, current runtime/API names, migrations, backup/rollback paths and existing release markers.
2. Treat **Press** as the proposed customer-facing label. Inventory old WordPress menu labels, internal routes, README references, integrations and consumer contracts before a separate user-approved rename plan.
3. Keep **Publications** on the existing WordPress posts/articles CMS unless a later approved architecture decision changes this.
4. Do not automatically merge Engagement Intake, Support, Contact or Feedback into Press.
5. Require documented compatibility shims, old-name redirects (when relevant), authorized review, privacy assessment, test coverage and reversible deployment plan before any rename/cutover.
6. Update Research, Workspace and Engagement & Communications handoff documentation to reference this canonical decision. Do not treat writing this document as production certification.

## Worked example — Wexford ERW

Library holds scientific papers, EPA evidence and satellite-source metadata; Research links them to the Wexford enhanced-rock-weathering investigation for additionality calculations, figures, uncertainty analysis, methods and a scientific/policy manuscript; Workspace coordinates milestones and reviews; WordPress Publications posts an accessible, approved public explanation; Press handles any separately approved announcement, media release or newsletter distribution.

## Explicit exclusions

This ADR does **not** authorize: new services or databases, WordPress reconfiguration, repository renaming or deletion, GitHub publicity changes, SSO activation, private data migration, publication without rights review, outbound sending, or a production deployment.
