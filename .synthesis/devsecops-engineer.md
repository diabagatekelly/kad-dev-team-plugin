# Synthesis: devsecops-engineer

Internal only — never referenced from `agents/devsecops-engineer/AGENT.md`
or any of its backing skills. Delete once the full roster is built.

**Roster rows 7 and 8, merged.** This persona was scoped mid-session as
`security-engineer` (row 7) alone; the merge with `reliability-engineer`
(row 8) was decided while resolving Contradiction 1, which is why the
security half of this file is more developed than the reliability half —
the security sources were read first and in full, the reliability sources
second and targeted. PERSONAS.md's roster table needs both rows replaced by
one, and the "Next to build" batch drops from four personas to three.

The first persona in this roster built for a **weak area** rather than a
core strength. That changes how the sources get used: for
`docs-writer`/`product-slicer`/`software-architect` the sources mostly
confirmed or sharpened something already known, and gaps could be filled
from judgment. Here the sources are load-bearing — and where all three are
*silent* that silence is the most important finding in this file, not a
detail. There are two such silences, one per half: **threat modeling**
(Contradiction 6) and **safe rollout / rollback / incident readiness**
(Contradiction 11). Both are named as responsibilities by the sources and
taught by none of them.

## Sources consulted

1. **Flexion plugin** —
   `flexion-ai-security-compliance/skills/security-compliance/SKILL.md`;
   `flexion-ai-pr-generator/skills/security-reviewer/SKILL.md` (all 5
   phases + the auto-configuration and progressive-optimization systems);
   `flexion-engineer-base/agents/azure-devsecops-expert-impl/AGENT.md` and
   `azure-devsecops-expert-review/AGENT.md`;
   `flexion-engineer-base/skills/gha-security/SKILL.md`;
   `flexion-ai-dependency-pinning/` — `README.md`,
   `skills/dependency-pinning-review/SKILL.md`, and the per-ecosystem
   `pin-*` skills' threat-model preambles (`pin-nodejs-deps`,
   `pin-jvm-deps`, `pin-docker-images`).
2. **Personal skills** — global `~/.claude/skills`: `code-review/SKILL.md`
   (section 8, "Security") and `deep-pr-review/SKILL.md` (Phase 0/4-5
   synthesis). Unlike `software-architect`'s synthesis, this area is **not
   empty** in the personal sources — but it is thin: security is one
   checklist section inside a general code-review skill, not a subject in
   its own right. It contributes exactly one strong idea (adversarial
   verification of high-severity findings, below) and one already-rejected
   mechanism (numeric scoring).
3. **CAMS** — `agents/devsecops-expert-review/AGENT.md` and
   `devsecops-expert-impl/AGENT.md`; `skills/cams-snyk/SKILL.md` (baseline
   system, classification taxonomy, SCA triage); `skills/cams-gha-security/SKILL.md`;
   `skills/cams-validation-checklists/SKILL.md` (Procedure 5, vulnerability
   triage decision tree, and the manual security checklist).

**Reliability half, added after the merge:**

1. **Flexion plugin** —
   `flexion-engineer-base/agents/azure-sre-expert-review/AGENT.md` and
   `azure-sre-expert-impl/AGENT.md`;
   `flexion-product-base/skills/write-devex-opex-issue/SKILL.md`;
   `flexion-ai-proposal-writer/_org_identity/modernization-strategy.md`
   (the only place in the entire corpus that states a rollback principle —
   see Contradiction 11).
2. **Personal skills** — searched global `~/.claude/skills` and every
   project-level `.claude/skills` under `~/Documents/*` for observability,
   reliability, rollback, and incident material: **nothing**. Same finding
   shape as `software-architect`'s synthesis had for architecture. Noted
   rather than fabricated.
3. **CAMS** — `agents/sre-expert-review/AGENT.md` and
   `sre-expert-impl/AGENT.md`; `skills/cams-error-handling/SKILL.md`
   (error-handling philosophy, expected-vs-unexpected taxonomy, what to
   log / what not to log); `skills/cams-devex-opex-writer/SKILL.md`;
   skimmed `skills/azure-deployment-troubleshooting/SKILL.md` and found it
   entirely vendor-procedural with nothing portable.

**Source-independence caveat, new to this persona.** CAMS's
`devsecops-expert-review/AGENT.md` is a near-verbatim copy of Flexion's
`azure-devsecops-expert-review/AGENT.md` — `diff` shows the only
substantive difference is CAMS adding a `skills:` list. The same holds for
the two `-impl` agents, and for **both SRE agents** on the reliability
side. So for anything sourced from those six files, "both Flexion and CAMS
say it" is **one source stated twice**, not corroboration.
This matters because it's the opposite of what happened in
`software-architect`'s synthesis, where the two-direction dependency check
earned its place partly by appearing in both sources *independently*. Any
principle below that rests only on those four files is marked accordingly.

## Principle table

| Principle | Source(s) | Status |
|---|---|---|
| The security question is about *reachability by an attacker*, not about which file a thing lives in — the same question gets asked of application code, CI config, and infrastructure definitions alike | derived while resolving Contradiction 1 | internal boundary decision, see below |
| Secrets never live in source, in committed config, or in plain environment variables — they come from a managed secret store at runtime | security-compliance; devsecops agents (single source, duplicated); code-review §8 | baseline (roster's "secrets hygiene") |
| Prefer short-lived, federated workload identity over any long-lived credential; a leaked long-lived credential grants access indefinitely, which is what makes it the highest-severity CI finding | gha-security | gap → added; the *why* (indefinite access) is the part worth keeping, not the specific credential names |
| Identifiers that aren't credentials but narrow an attacker's reconnaissance (tenant/subscription/account/resource IDs) still belong in secrets, not plain config | gha-security; cams-gha-security | gap → added — the genuinely non-obvious one in this whole corpus, since the reflex is "IDs aren't secrets" |
| Least privilege is four choices, not one: the right identity, the right role, scoped to the right resource, for the shortest duration | gha-security | gap → added |
| Broad-by-default grants are their own smell, independent of whether anything abuses them yet (`secrets: inherit`, missing/implicit permission blocks, wildcard roles) | gha-security | gap → added |
| Sensitive data must not reach logs, exception messages, error responses, monitoring/telemetry, or test fixtures — five exits, and logs are only the most obvious one | security-compliance | baseline (roster's "PII hygiene"), but the *five exits* enumeration was a gap → added |
| Logging a whole object is a distinct failure from logging a sensitive field: `toString()`/serialization leaks fields nobody chose to log, and it survives refactors that add new sensitive fields later | security-compliance | gap → added — the highest-value concrete pattern in that source |
| Log the identifier, not the subject: reference sensitive records by an opaque ID so the audit trail survives without the data | security-compliance | gap → added |
| Audit-log access *to* sensitive data without logging the data itself | security-compliance | gap → added |
| Trace sensitive data as a flow — where it enters, where it moves, where it exits — rather than checking call sites in isolation | security-compliance | gap → added; pairs directly with the five-exits idea |
| Test fixtures that look like real sensitive values are a finding, both because they may *be* real and because they defeat scanning for the real thing | security-compliance | gap → added |
| Security can be tested, not just reviewed: a test asserting a sensitive value never appears in captured log output turns a review comment into a regression guard | security-compliance | gap → added — the only source idea that survives past the review that found it |
| Validate untrusted input at the system's entry points, and treat "untrusted" as including anything crossing a trust boundary, not just end-user form input | security-compliance; devsecops agents; code-review §8 | baseline |
| Injection is one shape with many surfaces (SQL, NoSQL, OS command, path traversal, template/markup, deserialization) — the shape is "attacker-controlled text becomes structure/code" | devsecops agents (single source, duplicated); code-review §8 | baseline, but the unifying framing was a gap → added |
| Error and exception output is an information-disclosure surface, not just an ergonomics concern | security-compliance; devsecops agents | gap → added |
| Supply-chain question, stated as one testable question: *if an upstream package or registry were compromised right now, would this repo pull the bad version on its next build?* | dependency-pinning-review | gap → added — reframes an open-ended topic into something answerable |
| The lockfile is the trust anchor; pinning, frozen-mode installs, signature/attestation verification, and update automation all exist to keep that anchor honest | dependency-pinning-review | gap → added |
| Automated update tooling updates pins, it does not create them — a Dependabot/Renovate config is not a substitute for pinning | dependency-pinning-review | gap → added, common-mistake framing |
| The supply chain includes CI workflow references and container base images, not only the language package manager | dependency-pinning-review; pin-docker-images; pin-github-actions | gap → added |
| Mutable references (version tags, branches, floating ranges) are the vulnerability; immutable ones (content hashes, full commit SHAs, image digests) are the fix — one idea, many ecosystems | pin-* threat-model preambles | gap → added, generalized away from per-ecosystem commands (see Contradiction 2) |
| Install/lifecycle scripts are a code-execution vector at install time, before any of your code runs | pin-nodejs-deps | gap → added |
| Dependency risk includes license risk, not only vulnerability risk | cams-snyk (`.snyk` license ignores) | gap → added |
| Vulnerability triage is severity × reachability, not severity alone — the same CVE in a production path and in a dev-only tool are different findings | cams-validation-checklists Procedure 5 | gap → added |
| Suppressing/accepting a scanner finding requires a named classification *and* a written reason, recorded where the next person will find it | cams-snyk classification taxonomy | gap → added |
| The human picks the classification for an accepted finding — the agent must never infer it | cams-snyk (explicit `AskUserQuestion` requirement) | gap → added; matches this plugin's existing planning-persona ask convention |
| "Accept temporarily" must not be offered unless something actually enforces the expiry; otherwise it is a permanent acceptance wearing a disguise | cams-snyk (the blocked `Ignore temporarily` row) | gap → added — a source that disabled its own feature for exactly this reason |
| Severity is Critical/High/Medium/Low, anchored to blast radius and exploitability rather than to vulnerability category | devsecops agents; security-reviewer; code-review | baseline; same four-level taxonomy `software-architect` already uses, so the plugin stays internally consistent |
| Findings need file:line, a concrete failure story, and a specific fix — a category name is not a finding | devsecops agents; security-reviewer; deep-pr-review | baseline |
| Adversarially verify each high-severity finding before reporting it, rather than trusting the first pass that produced it | deep-pr-review Phase 4-5 | gap → added — the one substantive contribution from the personal sources |
| Distinguish test/mock/example code from production code before calling something a finding; the same string is a finding in one and noise in the other | security-reviewer (false-positive reduction); devsecops agents | gap → added |
| Dev-environment relaxations are legitimate; flag them by whether they can reach production, not by whether they look bad in isolation | devsecops agents | gap → added |
| Review what changed; note pre-existing issues separately rather than blocking on whole-codebase compliance | devsecops agents | baseline — identical stance to `software-architect`'s legacy-code rule, so it stays worded as this plugin already words it |
| Where a security control belongs is a boundary question: controls sit at the entry points and boundaries, which is the same place `software-architect` puts translation and isolation | devsecops agents ("OeSA Security Boundaries") | gap → added; the hand-off seam between the two personas |
| When a security recommendation collides with a simplicity/pragmatism recommendation, surface the trade-off for the human rather than silently letting either win | devsecops-expert-review conflict-handling | gap → added, but reworded — the source says "security generally takes priority"; see Contradiction 7 |

## Principle table — reliability half

| Principle | Source(s) | Status |
|---|---|---|
| Four signals worth measuring on anything user-facing: latency, traffic, errors, saturation | sre-expert-impl | baseline (roster row 8's "observability"), adopted as the default starting set rather than an open-ended "add metrics" instruction |
| A reliability target is a number someone agreed to (SLI → SLO), and the gap between that number and 100% is a budget that converts reliability into a decision rule rather than an aspiration | sre-expert-impl (SLI/SLO/error budget) | gap → added — the single most useful idea on this half, because it makes "is this reliable enough?" answerable |
| Observability is the ability to answer a question you didn't anticipate; logs, metrics, and traces are three views, and a correlation identifier threaded through all of them is what makes them one story instead of three | sre agents (single source, duplicated) | baseline, but the "one story" framing was a gap → added |
| Structured logging with context fields, not message-string concatenation — the difference decides whether logs are queryable later | sre agents | gap → added |
| Log at boundaries; instrument domain operations for business meaning | sre-expert-impl ("Observability Boundaries") | gap → added; the hand-off seam with `software-architect` |
| Expected errors (validation, business-rule violations) and unexpected errors (bugs, system failures) are different categories and get handled differently — conflating them produces both noisy alerts and silent bugs | cams-error-handling | gap → added |
| Resilience patterns, each answering a different failure: retry (transient failure), timeout (never wait forever), circuit breaker (stop a failing dependency from taking you with it), bulkhead (contain the blast), graceful degradation (partial service beats none) | sre agents | baseline, but pattern-to-failure pairing was a gap → added |
| Retry only what is actually transient — retrying a deterministic failure is not resilience, it's amplification, and it turns one failure into a load spike | sre agents (implied by "transient vs permanent distinguished") | gap → added, sharpened from the source's weaker phrasing |
| Resilience logic belongs in the adapter, not in the business logic — a use case should not know that its dependency retries | sre-expert-impl ("Integration with OeSA") | gap → added; directly reinforces `software-architect`'s Invasive Species and Dependency rules |
| Resource lifecycle is a reliability concern: unclosed connections, unbounded growth, and missing cleanup fail slowly in production and never in tests | sre agents | gap → added |
| An alert must be actionable, anchored to a target rather than an arbitrary threshold, carry a severity, and point at what to do about it | sre agents | gap → added |
| Alert fatigue is a failure mode in its own right — a noisy alert set is worse than no alerts, because it trains people to ignore the one that matters | sre-expert-review; write-devex-opex-issue (the "paged for false alarms" example) | gap → added — the non-obvious one on this half |
| Observability costs money and performance; sampling and deliberate scope are part of doing it well, not a compromise of it | sre-expert-review ("Cost Considerations") | gap → added |
| Separate performance-as-correctness (leaks, unbounded result sets, work that grows without limit) from performance-as-speed (algorithm choice, caching) — the first is a reliability finding, the second usually isn't | derived while resolving Contradiction 12 | gap → added |
| A performance finding needs a concrete scale story — at what volume, on which path, with what consequence — or it's speculation dressed as a finding | sre-expert-review ("avoid premature optimization", "theoretical vs proven") | gap → added |
| Dev-environment relaxations are legitimate; severity tracks whether the issue can reach production | sre agents; devsecops agents | baseline on both halves |
| Operational and developer-experience problems are real work, and stating one well means quantifying the pain, its breadth, and its frequency rather than asserting it | write-devex-opex-issue; cams-devex-opex-writer | gap → noted, **not** folded into a skill — writing that issue up is `docs-writer`'s job in this plugin (see Contradiction 13) |
| Rollback is a tested capability of the delivery pipeline, not a procedure improvised during an incident | modernization-strategy.md (proposal collateral — the corpus's only statement on this, see Contradiction 11) | gap → added, with its provenance flagged |

## Contradictions — flagged and resolved

**1. Scope: is this persona "security" or "DevSecOps"?** Every agent-shaped
source bundles security with infrastructure, IaC, CI/CD pipelines, cloud
resource configuration, and deployment automation into one DevSecOps
persona, and pairs it with a separate SRE persona covering observability,
reliability, and performance. PERSONAS.md instead split the *security*
bundle across two rows: row 7 `security-engineer` (threat-aware review,
secrets/PII hygiene, dependency & supply-chain risk, least privilege) and
row 8 `reliability-engineer` (IaC review, observability, safe
rollout/rollback, incident readiness).

Two candidate boundaries were considered. Splitting **by artifact**
(security owns application code, reliability owns infra/CI files) creates a
dead zone: credential handling inside an infrastructure definition would
belong to neither, or would force the reliability persona to own security
questions it isn't built for. Splitting **by question asked** ("could an
attacker reach this?" vs. "will this stay up?") avoids the dead zone but
means both personas routinely read the same file, which is close to the
overlap PERSONAS.md itself calls a smell.

**Resolved by the user in favor of merging rows 7 and 8 into one
`devsecops-engineer` persona**, which is what both source sets ship in
substance and what PERSONAS.md's own conventions prescribe for this
situation — "if two personas would flag the same thing, merge them or
sharpen the boundary." The overlap here was real and structural rather than
accidental: an over-permissive deployment role and a missing health check
live in the same file, get found by the same read, and get fixed in the
same change.

What keeps the merged persona from becoming the generalist PERSONAS.md
warns against is that **the narrowness lives in the skills, not the
agent.** The agent's mandate is one thing stated one way: *the system's
runtime safety properties — whether it can be attacked, and whether it can
stay up.* Each backing skill covers exactly one trigger. And the mandate is
bounded by explicit non-ownership: this persona does not decide what gets
built (`product-manager`, `product-slicer`), how it is structured
(`software-architect`), whether it reads well (`code-reviewer`), or how it
is tested (`tdd-coach`).

The seam with `software-architect` needs stating because both personas talk
about boundaries: **`software-architect` decides where a boundary is;
`devsecops-engineer` decides what must be true at it.** Validation,
authentication, and resilience all belong at boundaries — which boundary
exists is an architecture question, what it must enforce is this
persona's.

**2. Cloud- and ecosystem-specificity.** Roughly half of both devsecops
agents is one cloud vendor's product surface (managed identity, key vault,
private endpoints, specific role GUIDs, Bicep snippets), and
`flexion-ai-dependency-pinning` is eight per-ecosystem skills of exact
package-manager commands. PERSONAS.md requires this plugin to be portable
and to read as general engineering principles, with project- and
vendor-specific procedure left to project-specific plugins.

Resolved: keep the **principle**, drop the **product**. "Prefer federated
workload identity over long-lived credentials" ports everywhere; the name
of one cloud's identity feature doesn't. "Mutable references are the
vulnerability, immutable ones are the fix" ports everywhere; a table of
eight lockfile commands doesn't, and would rot. Where a check genuinely
needs an ecosystem-specific command, this persona names what to verify and
lets the user's own toolchain supply the command. No cloud vendor, package
manager, or scanner product is named in the shipped files.

**3. Progressive optimization / a learned per-repo config file.**
`security-reviewer` builds `.claude/security-config.json`, counts scans,
and progressively *skips* checks that have never found anything — reaching
a "fast mode" at 20+ scans that only scans for vulnerability classes
already seen, while claiming "no accuracy loss."

Resolved: **rejected**, on three independent grounds. (a) The reasoning is
survivorship bias: "we've never found injection here" is evidence about
past scans, not about present code, and the classes least often found are
often the ones least often looked for. A security check that gets quieter
the longer it finds nothing is backwards — that's the profile of a control
that fails silently. (b) It writes state into the user's repo at a fixed
path, which contradicts this plugin's rule that artifact location is a
parameter, never a hardcoded convention. (c) It's the same family as the
numeric-scoring mechanism already rejected for `software-architect`
(Contradiction 6 there) — an accumulating quantitative apparatus bolted
onto a qualitative judgment. Consistent with that precedent, no scoring, no
scan counters, no learned skip-lists.

**4. Compliance regime.** `security-compliance` is written end-to-end for
one regime and one identifier type (HIPAA, MBI), to the point that its
single most emphasized rule names that identifier. `security-reviewer`
generalizes to a detected list (HIPAA/GDPR/PCI-DSS/FISMA). This repo has
no regime at all.

Resolved in favor of neither: ship **no default regime and no default
sensitive-data list**. The persona asks what data the system actually
handles and what obligations apply, then works from that answer — the same
ask-rather-than-assume convention PERSONAS.md already sets for planning
personas. Shipping HIPAA as a default would be wrong for most projects and
would quietly teach the wrong checklist; shipping an auto-detection step
would be guessing at a legal question from file contents. The *mechanism*
worth keeping from the HIPAA material is regime-independent: name the
sensitive classes, then trace each one's entry, movement, and exits.

**5. Where security requirements come from, and when.** The sources treat
security almost entirely as **review of code that already exists** —
every agent and skill here is diff-driven or repo-driven. Nothing in any
source produces security *requirements* before code exists. But this
plugin's own dogfood run demands exactly that: `evals/example/slice-001.md`
carries a placeholder acceptance criterion owned by this persona,
`design-001.md` defers to it, and `problem.md`'s open question ("what
counts as 'very secure' here in concrete terms") is a requirements
question, not a review question.

Resolved: the pre-code trigger is real and is this persona's *primary*
one, despite being absent from all three sources. Turning a vague security
constraint into concrete, testable acceptance criteria for one slice is a
distinct trigger from reviewing existing code, and gets its own skill. This
mirrors `software-architect`'s design/review split, and it's the reason
this persona is being built now rather than after `tdd-coach`.

**6. Threat modeling: named by every source, taught by none.** Both
devsecops agents list "Threat Modeling" as a core responsibility;
`security-reviewer` maps an "attack surface" and offers to "update the
threat model"; Flexion's user-story templates carry a "Threat model
updated" Definition-of-Done checkbox. Not one of them defines a method,
and no threat model exists in any source to update. This is a corpus-wide
gap, not a disagreement — and it sits directly on top of roster row 7's
own words, "threat-aware review."

Resolved: supply a method rather than inherit a checkbox, and keep it
proportional to a single slice — three questions, asked per slice: what
would an attacker want from this slice; where does untrusted input or
identity cross into it; and what is the worst thing reachable from there.
Each answer that matters becomes an acceptance criterion, which is what
makes it verifiable later. Explicitly **not** adopting a formal
enumeration framework: a full ceremony is the wrong weight for a one-slice
personal-project tool, and a framework nobody completes produces the same
empty checkbox the sources already have.

**7. Whether security automatically wins a conflict.**
`devsecops-expert-review` says security concerns "generally take priority"
over a pragmatism/simplicity reviewer's objections, while also telling the
agent to document the trade-off for a human.

Resolved toward the second half: **surface the trade-off, don't
auto-win.** A persona that always outranks the others isn't reviewing, it's
vetoing, and it would push this plugin toward exactly the
security-theater posture the sources' own "avoid false positives" guidance
warns about. This is also consistent with how every other persona here
behaves — `software-architect` presents a recommendation with rejected
alternatives and waits, rather than deciding. Security findings still
carry the severity that their blast radius earns; what's rejected is
severity-independent precedence.

**8. Impl/review split.** Both source sets ship `-impl` and `-review`
agents for *both* halves — four agents total, where this plugin will have
one. The `-impl` ones write application code, infrastructure, and CI config
under a TDD loop.

Resolved the same way as `software-architect` Contradiction 7: **no
split**. This plugin still has no code-writing persona, and adding one here
would be a larger structural change than these rows justify. The merge makes
the source count look worse than it is — four source agents collapsing into
one persona sounds aggressive, but they are two agents duplicated across two
copies of the same corpus, and the impl/review division is the very thing
being rejected. One agent, multiple narrow skills; `Write`/`Edit` mean this
persona's own artifacts (criteria, findings reports), never source files,
infrastructure, or pipeline config.

**9. ADR ownership.** Not a source contradiction — the same internal
boundary `software-architect` already settled. Decisions that are
architectural, costly to reverse, and non-obvious clear the ADR bar on both
halves: choosing an identity model, accepting a class of risk, or placing a
trust boundary on the security side; committing to a reliability target,
choosing a rollout strategy, or accepting a single point of failure on the
reliability side. This persona **flags** them and hands off to
`docs-writer`; it does not author ADRs.

**10. Observability by default vs. YAGNI.** The SRE sources want logging,
custom metrics, distributed tracing, and alerts on essentially every
significant operation, and grade their absence as findings. That collides
with `software-architect`'s two-directional YAGNI rule (which this plugin
already adopted) and with the same sources' own admission that telemetry
costs money and performance. Instrument-everything and build-only-what's-
needed cannot both be followed literally.

Resolved by tying instrumentation to a question rather than to a coverage
level: **instrument what you would need in order to answer "is this slice
working, and if not, where is it failing?"** — and nothing else, yet. That
makes an observability gap concrete (there's a failure mode you couldn't
diagnose) rather than a checklist miss (this function has no metric), and
it's the same shape as the YAGNI test already in use: a real, present need
rather than an anticipated one. It also gives the cost concern somewhere to
land instead of being an afterthought.

**11. Safe rollout, rollback, and incident readiness: named as a
responsibility, taught nowhere.** The second corpus-wide silence, and the
mirror of Contradiction 6. `sre-expert-impl` lists "Incident Response:
runbooks, diagnostic tools, recovery procedures" and "Disaster Recovery:
backup, restore, failover" among its core responsibilities and then never
mentions any of them again. Feature flags appear in the corpus only as an
example of how to write a ticket. No runbook, post-mortem, or rollout
strategy method exists anywhere. The single substantive statement on the
entire subject — "every deployment includes automated rollback capability;
rollback is tested as part of the deployment pipeline, not as an emergency
procedure" — appears in **proposal and marketing collateral**, not in any
engineering guidance.

Resolved: keep that one statement, because it is genuinely good and
genuinely testable, while flagging its provenance so nobody later mistakes
it for something the engineering corpus established. Everything else on
this trigger has to be supplied rather than synthesized. Kept proportional
to a personal-scale project, the same way the threat-modeling method was:
before a slice ships, three questions — how would we know it broke, how do
we put it back, and what does someone need to know at 2am — with each
answer becoming something checkable rather than a document nobody reads.
Explicitly **not** adopting formal incident-management ceremony (severity
matrices, on-call rotations, post-mortem templates); it presumes a team and
a pager, and this plugin is personal tooling.

**12. How far performance review reaches.** `sre-expert-review` lists
algorithmic complexity, memory usage, CPU usage, and excessive object
creation as review targets, then in the same file instructs the reviewer to
"avoid premature optimization concerns" and to "distinguish theoretical vs
proven issues." Followed literally, the checklist manufactures exactly the
findings the quality standard forbids.

Resolved by splitting the category rather than picking a side.
**Performance-as-correctness** — resource leaks, unbounded result sets,
work that grows without limit, missing pagination — are reliability
findings regardless of current load, because they fail eventually and by
construction. **Performance-as-speed** — algorithm choice, caching,
sync-vs-async — is only a finding when it comes with a concrete scale
story: at what volume, on which path, with what user-visible consequence.
Without that story it stays an observation, not a finding. This keeps the
useful half of the checklist and drops the half that generates noise.

**13. Operational work as a written-up issue.** Both source sets ship a
DevEx/OpEx issue-writing skill with a well-developed method (quantify the
pain, the breadth, the frequency; lead with problem not solution). It is
good material and it is squarely about operational concerns.

Resolved: **noted, not adopted.** Writing an issue up is `docs-writer`'s
mandate in this plugin (roster row 1 already owns problem framing,
user-story and PR write-ups), and duplicating it here would create exactly
the persona overlap PERSONAS.md calls a smell — the same overlap this
persona was just merged to eliminate. What transfers is the *standard*, not
the skill: when this persona reports an operational finding, it quantifies
the pain rather than asserting it, and hands off to `docs-writer` if the
finding warrants a written-up issue.

## Top gaps folded into skills

Skill split follows PERSONAS.md's "one skill per trigger" rule, which is
what keeps a merged persona from being a generalist (Contradiction 1). Each
half resolves into the same three triggers — **requirements** (before code,
per slice), **review** (against code that exists), **posture** (against the
repo or its delivery path, on no particular diff) — which is a good sign the
trigger taxonomy is real rather than imposed.

Security half:

1. `skills/security-requirements/SKILL.md` — **pre-code, per slice**: the
   three-question threat pass (Contradiction 6), naming the sensitive data
   classes and applicable obligations by asking rather than assuming
   (Contradiction 4), tracing each class's entry/movement/exits, and
   converting each answer into a testable acceptance criterion in the same
   Given/When/Then form `product-slicer`'s `acceptance-criteria` skill
   already uses. **This is the dogfood target for this build** — it fills
   `evals/example/slice-001.md`'s live security placeholder and answers
   `problem.md`'s open "what does 'very secure' mean concretely."
2. `skills/security-review/SKILL.md` — **post-code**: the five exits for
   sensitive data, whole-object logging, injection-as-one-shape,
   secrets/identity/least-privilege checks applied to application code and
   config alike, severity by blast radius, adversarial verification of
   high-severity findings before reporting, test-vs-production
   discrimination, changed-code-first legacy stance.
3. `skills/supply-chain-review/SKILL.md` — **repo posture**: the "would a
   compromise upstream reach our next build" question, trust-anchor
   framing, mutable-vs-immutable references across packages/CI/images,
   install-time execution vectors, license risk, and the accepted-finding
   discipline (named classification + written reason, human chooses, no
   unenforced expiry).

Reliability half:

4. `skills/reliability-requirements/SKILL.md` — **pre-code, per slice**:
   what failure modes this slice has, which must degrade gracefully vs.
   fail loudly, what target it's held to (Contradiction 10's question-driven
   instrumentation, and the SLI/SLO framing scaled to a personal project),
   and what must be observable to know it works — each emitted as testable
   criteria alongside the security ones.
5. `skills/reliability-review/SKILL.md` — **post-code**: observability gaps
   framed as undiagnosable failure modes, resilience patterns matched to
   the failure each addresses, retry-only-what's-transient,
   resilience-in-adapters, expected-vs-unexpected error handling, resource
   lifecycle, alert quality and alert fatigue, and the
   performance-as-correctness / performance-as-speed split (Contradiction 12).
6. `skills/operational-readiness/SKILL.md` — **delivery posture, pre-ship**:
   the largely-unsourced rollout/rollback/incident-readiness trigger
   (Contradiction 11) — how we'd know it broke, how we put it back, what
   someone needs to know at 2am — with rollback treated as a tested pipeline
   capability rather than an improvised procedure.

Cross-cutting content shared by all six — the runtime-safety-properties
mandate and its explicit non-ownership list, the seam with
`software-architect` (*where* a boundary is vs. *what must be true at it*),
the four-level severity taxonomy, the no-auto-win conflict stance
(Contradiction 7), the ADR hand-off rule, the `docs-writer` hand-off for
written-up operational issues (Contradiction 13), the ask-don't-assume
convention for planning-time skills, and the artifacts-location rule —
lives in `agents/devsecops-engineer/AGENT.md`'s system prompt rather than
being repeated six times, matching how `software-architect` factors its
four rules into its agent prompt.

## Open question carried into the build

Whether the two `*-requirements` skills (1 and 4) and the two `*-review`
skills (2 and 5) are really four skills or two. Both pairs arguably share a
trigger — "a slice needs its non-functional criteria before code exists"
and "review this diff for runtime-safety problems" — differing by lens
rather than by moment, and a skill loads as a whole unit, so a single
requirements skill covering both lenses would always load both. Against
merging: the content is large and mostly disjoint, and merging would
produce two very long skills where the plugin's convention is narrow ones.
The posture skills (3 and 6) are clearly distinct from everything and from
each other either way. To be decided with the user before the skill files
are written.
