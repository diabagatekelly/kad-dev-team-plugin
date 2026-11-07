# Eval suite work list

From `AUDIT-2026-10-12.md`. Phases are ordered by dependency: each phase's
re-record depends on the previous phase's graders being right, so finish a
phase before running its evals. "Run" marks items that need a paid eval run
to close; everything else is a file edit. Keep the README playbook's rule:
read every failure before re-recording a bar.

Note 2026-11-06 (0.13.0): the heavy `tdd-implementation` skill and its five
cases were retired after G2 and run 2 showed lite matching it; every item
below that names them is history, and the compare policy and
`compare_arms.py` are gone.

## A. Gate arithmetic (no runs except the final re-record)

- [x] A1. Delete `agent-delegated-legacy-task-display` (`tool: Task`) from
      `library-app-lending-review-via-agent` and
      `code-review-fine-notices-pr-via-agent`. (Their bars still include
      the old failure until A5 re-records them.)
- [x] A2. (Recorded from the 2026-10-13 morning gate run, 1 run each.)
      `architecture-review-neg-security-review` and
      `architecture-review-neg-test-quality-review`: no conversion needed,
      the markdown format is the same one the other eleven negative cases
      use; they only lacked a recorded run. The 2026-10-12 local "gate
      run" was a zero-turn sandbox refusal (the gate grants Bash to every
      case) that the `tool_used` count-0 grader passed vacuously; those
      bars and result files were removed. Record from the GitHub workflow
      (`cases: architecture-review-neg-security-review
      architecture-review-neg-test-quality-review`). Run.
- [x] A3. `record_thresholds.py` stores per-grader pass rates (`graders`);
      `eval_gate.py` re-runs a case when an always-passing grader fails
      and fails the gate when it fails in every re-run. Bars recorded
      before this field existed get the aggregate check only until A5.
- [x] A4. Bars come from gate-mode runs. `record_thresholds.py` records
      `mode` and warns on calibration sources; `--gate-only` filters them.
      Documented in the README's "Eval gate". A5 is what actually moves
      every existing bar onto gate mode.
- [x] A5. (Done 2026-10-14; the record is at the end of this entry.)
      After B, C and F land: `eval_gate.py --all --runs 3` once, then
      `record_thresholds.py --gate-only` for everything. Run (109 cases,
      about 330 runs, two subscription windows). Still open after the
      2026-10-13 full run: that run was one run per case, so 68 bars are
      still calibration bars (aggregate check only, no per-grader rates)
      and 31 gate bars come from a single run. Evidence is not a bar:
      the PR check passed against those weak bars within tolerance.
      Since 2026-10-13 this is also what clears the PR check: the branch
      reaches nearly every case and `evals/evidence.json` holds one entry
      (`tdd-implementation-named-fix`, from the run that proved the
      parallel path). `wsl -d Ubuntu -- bash evals/tools/wsl-gate.sh
      --all`, about 20 minutes wall-clock at eight runs in flight, but
      roughly three five-hour subscription windows of usage.
      **First full gate run, 2026-10-13 evening (WSL2, `--parallel 8`):**
      92 affected cases in 36 minutes wall-clock including twelve
      automatic three-run re-runs, no rate limit, no errored run; 84
      passed and got evidence, 8 below bar. Read from the traces:
      - `orchestrator-route-implementation` 0.60 (2/2 runs): routed
        correctly in prose, then asked "Do you want me to continue?"
        about the quarantine flow's cost before writing the log, so
        `log-written` and the routing grader (reads the log) both
        failed. The skill's log rule now says the entry precedes any
        question to the user, cost confirmations included. Re-run 1.00.
      - `reliability-review-catalog` 0.75 (3/3, had passed 1.00 that
        morning on one run): every run rated a Medium on the clean
        module, "capture context lacks a `catalog` tag / request id" or
        "pool-wait semantics unverified", co-locating the alerts.yml
        alert-fatigue finding with the route. The skill's own Medium
        tier said "missing context in error handling", which is what the
        model applied. The Severity section now says an observability
        gap is Medium only when the failure could not be told apart with
        what is reported, that an unverified behaviour is a question not
        a Medium, and that Location is where the fix goes. Re-run 1.00;
        the other six reliability-review cases and the three tdd cases
        (whose final review loads the skill) re-ran green.
      - `design-system-payfine-phase2` 0.75: runs 2 and 3 wrote the
        three candidate HTML files with `cat > a.html <<'EOF'` heredocs
        and `renders-candidates` (Write-only) saw nothing. The grader
        now accepts a heredoc target too (not a bare `>`, the candidates'
        own HTML is full of them). How the files are written isn't this
        grader's point, unlike the tdd cases. `asks-which-candidate`
        failed once on a reply that called one candidate "the most
        legible" while asking which to keep; judge call, left. Re-run
        pass.
      - `architecture-design-payfine-phase2` 0.88: `decisions-show-
        approval` FAIL 9/9 votes on a Decisions section that carries
        recommendation, rejected alternative and approval for each
        decision; the next run passed 3/3. Judge variance on a 9k-char
        file; nothing changed.
      - `architecture-design-payfine-via-agent` 0.73: the delegated
        architect can't ask (no `AskUserQuestion` in a subagent), so it
        saved a draft design with every decision "pending" and the
        waits grader failed 3/3. The skill now says what to do without
        `AskUserQuestion`: the first decision only in the final report,
        nothing saved, no sections laid out around it (a first wording
        that allowed "the few independent decisions" produced a reply
        that walked through structure, technology and violations, which
        the judge rightly read as the design delivered: phase1 0.78).
        With the tightened text phase1 is 1.00 at 3; via-agent presents
        and waits but skips the `map-query` consult inside the subagent
        in most runs (1/3, 2/3, then 3/3 skipped), which the direct
        phase1 run never does. Found 2026-10-14: the skill named the
        consult `architecture-cartographer:map-query`, the same wrong
        name the tdd skill had; the subagent read the map file instead
        of invoking anything. Now `map-query` / `kad-dev-team:map-query`.
        With the right name the subagent still reads the map file
        instead of invoking the skill in 2 of 3 runs (0.87 at 3); the
        direct phase1 run invokes it 3/3. Recorded honestly at 0.867
        (`consults-map-query` 0.333) for G: a delegated architect that
        treats "consult map-query" as "read the map".
        `security-requirements-payfine-phase2` recorded at 0.667 (gate,
        3 runs, fork grader 0/3) the same morning, for D1.
      - `security-requirements-payfine-phase1` 0.78 and `-phase2` 0.78,
        `reliability-requirements-payfine-phase2` 0.67: the fork and
        question graders (`does-not-decide-the-fork-itself`,
        `does-not-ask-what-the-code-answers`) with split judge votes
        and scores that bounce between 0.67 and 0.89 from run to run.
        Phase 2 writes criteria on the assumption of its own
        recommendation; phase 1 asks "is `cardToken` a browser-side
        token?" as a question rather than a confirmation. D1 and D5
        territory; two bars recorded honestly from gate runs (0.889,
        0.778) to be re-recorded after D.
      Two more facts the run produced: with three graders at three runs
      one grader flip moves a score by 0.11, more than the 0.1
      tolerance, so a bar recorded from one three-run sample fails the
      next sample as often as not (A-phase arithmetic, open: tolerance
      should reflect grader count, or the per-grader rates should carry
      the verdict); and two cases errored with "OAuth token revoked"
      when a concurrent child refreshed the subscription token, so the
      gate now re-runs such a case once. The subscription's session
      limit hit after about 170 runs in one window.
      **Full three-run gate, 2026-10-14 (WSL2, `--all --runs 3`):**
      started 00:55 EDT; 68 cases ran clean in 35 minutes, then the
      subscription session limit ("resets 5am") errored the other 41 on
      all three runs, and the gate dropped their evidence with the
      failures'. Resumed at 06:50 with `--stale` (38 affected cases,
      132 runs, 27 minutes, no error), then the five unaffected cases
      the limit had hit, then re-runs of what the reads below changed.
      Every one of the 109 bars is now a gate-mode three-run bar with
      per-grader rates (`record_thresholds.py --gate-only`), and
      `evidence.json` covers 109/109. Read from the traces:
      - `screen-design-payfine` 0.85: `three-mockups-in-visual-ux`
        (a trace regex on `Write` calls) failed every run. In two runs
        the model had written the HTML through Bash, a Python generator
        and a heredoc, which the case never granted: the gate passed
        `--allow-tools Write Edit Bash` to every case. `eval_gate.py`
        now grants each case only the gated tools its `allowed_tools`
        names. The third run, and one of three on the re-run, was a
        real miss: one HTML file with every state side by side, which
        `one-mockup-per-state` also failed. The skill's rendering step
        said "write the mockup as a real HTML file", singular, against
        its own one-per-state rule; it now says one file per state.
        Re-run 1.00 at 3, four to six files each.
      - `test-quality-review-reminders` 0.89: `no-false-alarm-inline-
        fakes` failed 2/3 on reviews whose email finding said the
        no-op email fake "can't fail" and should capture its calls.
        The grader meant the SMS and postal capture fakes; the reviews
        praised those. Grader now says that naming the email fake's
        no-op inside the untested-email finding is part of that
        finding. Re-run 1.00 at 3.
      - `technology-bootstrap-phase3` 0.80 then 0.73: `recommends-
        rather-than-decides` failed 17/18 votes on documents that
        record recommendation, rejected alternative and approval for
        every category. The CLI keeps no judge rationale, so a Sonnet
        judge was asked by hand with the same document and criterion:
        the grader told it the user "delegated the package manager
        ('whatever you'd recommend')", when phase 2 actually set a
        criterion for it ("pick the one where safe is the default"),
        so the document's accurate "the user asked for the manager
        where safe is the default" read as an invented requirement.
        Grader now quotes the user's actual words per category.
        Re-run 0.93 at 3 (one run still lost that grader 3/3).
      - `reliability-requirements-payfine-phase1` 0.89, `security-
        requirements-payfine-phase1` 0.78, `-phase3` 0.89: the known
        D1/D5 graders. Phase 1 asked "is there on-call or alerting?"
        with `ops/alerts.yml` in the repo; security phase 1 asked
        "does the portal tokenise cards in the browser?" after stating
        it would treat that as the design; security phase 3 lost
        `criteria-cover-error-and-monitoring-exits` once and `records-
        the-decision-without-relitigating` once on documents that meet
        both by the letter. Bars recorded from these runs (0.889,
        0.778, 0.889); the second samples came in at 0.89, 1.00, 0.94.
      - `reliability-review-catalog` 0.83 and `-alerts` 0.89 in the
        first half: both 1.00 on the resumed run. Judge variance.
      Two facts for the playbook: recording bars rewrites each case's
      `skills_invoked`, which is part of its reach, so five cases'
      evidence went stale with no file edited (the orchestrator cases
      had consulted `reliability-requirements` in some run; the two
      neg cases had invoked `security-review`): record bars first,
      then take the final evidence run. And the CLI stores judge
      votes but no rationale; `claude -p` with the grader's criterion
      and the judged file reproduces the verdict with reasons in one
      call, which is how the bootstrap grader fault was found.
      **Sourcery review of PR #2, 2026-10-14:** 22 findings, 8 taken.
      `validation_gate.py` now fails when git cannot compute the change
      set (an unknown base read as "nothing changed"), fails coverage
      for a changed source file the table does not list (never loaded
      by a test), and lost an unused parameter. `eval_evidence.check`
      reports a case with evidence but no bar instead of passing it.
      A changed `thresholds.json` entry now makes its case affected,
      so a raised bar is checked against the evidence. The gate
      fingerprints each case before its runs and records no evidence
      for one whose inputs moved while it ran. `wsl-gate.sh` passes
      `--` to sed; the documented distro name matches what the setup
      installs. The Bash guard covers inline interpreters (B5 above);
      the four cases re-run at 3. Declined, with the reasons on the
      PR: token revocation is retried (the error text contains
      "authenticate"); `Edit` on a new file cannot happen and a wrong
      tool fails the ordering grader rather than passing it; a trace
      can fake `ℹ fail 0` only if the model prints the reporter's
      summary itself; a CLI version mismatch would invalidate every bar
      on each upgrade; evaluator-tool edits fingerprinting every case
      would cost a full run per tool edit; removed graders show in the
      diff; partial runs keep the September rule (clean runs only, the
      count recorded); one developer takes runs one at a time; the
      opengrep subprocess hits are a list call without a shell and the
      operator's own test command.

## B. tdd cases as the mechanical gate (depends on nothing; do before C)

- [x] B1. `code-plants/tdd/package.json`: `--test-reporter=spec` added.
- [x] B2. `a-green-run-happened` copied into both cancel-hold cases.
- [x] B3. `red-runs-seen` replaced by `red-then-green-per-test`: a test-file
      Write or Edit, no other Write/Edit before a red summary, then a green
      summary, three times.
- [x] B4. `can-fail-check-in-trace` added beside the report grader: after
      the last test-file edit, green, then red, then green with no later
      red.
- [x] B5. `no-bash-writes` added to both cancel-hold cases, `named-fix` and
      `map-update-cancel-hold`: a Bash command that redirects, `tee`s,
      `sed -i`s, heredocs, `cp`/`mv`/`rm`s into any app directory fails.
      (2026-10-14: an inline interpreter, `python3 -c`, `node -e` or a
      heredoc into one, naming an app directory counts as a write too.)
- [x] B6. `design-doc-unchanged` now anchors the whole fixture text,
      whitespace-insensitive (verified to reject an edit in Structure).
- [x] B7. `writes-only-the-map` matches on the path suffix.
- [x] B8. `escalates-queue-question` requires naming `acceptance-criteria`
      or `architecture-design` as the owner; "product" or "the user" fails.
- [x] B9. `reviews-each-cycle` requires a test run between consecutive
      reviews.
- [x] B10. `map-query-before-implementation` tool_order added to the two
      cancel-hold cases. Not `named-fix`: the skill's handed-back path is a
      structural fix, not a Test List entry, and the consult rule applies
      before an entry's implementation (4/4 gate runs never consulted).
      All of B3–B9 verified against synthetic traces
      (scratch `test_b.py`): each passes a disciplined trace and fails the
      shortcut it was written for.
- [x] B11. (Done 2026-10-13 in WSL2; the entries below are the record.)
      Run the four changed cases at `runs: 3`, read failures,
      re-record. Run. **Blocked on this Windows machine:** `claude plugin
      eval` refuses any case that grants Bash when no sandbox backend is
      active ("sandbox required but unavailable … Windows sandbox is not
      active"), so every tdd and map-update run exits at turn zero and is
      scored as all-fail. Run these through the GitHub workflow
      (`workflow_dispatch` with the four case names; it installs
      bubblewrap), or under WSL2 with bubblewrap, or on a Mac. The
      zero-turn results from 2026-10-12 were deleted; `eval_gate.py` and
      `record_thresholds.py` now treat an all-errored result as an error,
      not a score.
- [x] B12. `tools/validation_gate.py`: suite green, optional Node coverage
      per changed file, scope diff against `--allow` prefixes, `--protect`
      files unchanged; JSON verdict, exit 1 on any failure. Exercised on
      the scaffolded tdd fixture: catches an under-covered file, an
      out-of-scope edit, an untracked file, and a touched design doc, and
      passes a clean change. Not yet wired into the orchestrator's Grade
      step (that is a skill change, see PERSONAS.md's quarantine flow).

## C. Long reports to files (one pattern, many cases)

- [x] C1. 31 review cases now save the report as
      `docs/reviews/<case>.md` (`Write` allowed, `review-written`
      file_exists, every llm grader on the file, `leaves-the-code-alone`
      forbids any other Write/Edit); the three tdd cases save their report
      as `docs/reports/<case>.md` (`report-written`). Via-agent prompts
      tell the subagent to save and still return the report verbatim.
- [x] C2. `reliability-review-catalog/reports-nothing-above-low` counts
      only findings located under `catalog/`, the catalog reader or the
      catalog route; the capacity sentence is gone.
- [x] C3. Five severity graders now say Critical or High passes, Medium or
      lower fails.
- [x] C4. "Or equivalent" wording in the holds, mailer-timeout and
      member-object graders; the authentication/authorization wording
      clause dropped from the IDOR grader.
- [x] C5. (Done; every review case passed the 2026-10-13 full run.)
      Run the changed cases, read failures, re-record. Run. First
      real workflow run 2026-10-13 (run 38386051763): 12 of the 35 cases
      ran clean, all 1.00; then the workspace's credit balance ran out and
      the other 23 errored. Three cases failed one grader before that:
      `code-review-catalog/nothing-above-low` (the reviewer rated a bare
      `2` constant Medium in a 35-line clean module: a real restraint
      miss, re-run at 3 to see the rate),
      `library-app-catalog-review/reports-nothing-above-low` (grader
      fault: the judge counted High items in the review's "pre-existing,
      outside `catalog/`" list; now location-scoped like C2), and
      `reliability-review-alerts/no-false-alarm-burn-rate-alerts`
      (fixture fault: the burn alerts selected `path="/books/search"`
      while the route is `/books/search/:terms`, so the reviewer flagged a
      real mismatch; the selectors now use the route template). Bash was
      unavailable in every run (bubblewrap's loopback setup is blocked by
      AppArmor on Ubuntu 24.04 runners); the workflow now runs on 22.04
      and probes the sandbox before spending. Nothing recorded from that
      run.
      Second run (38387443843, Ubuntu 22.04, shell working, $16.35): 34 of
      36 cases finished before the 150-minute job limit (now 300); the two
      cancel-hold tdd cases did not. 30 bars recorded in gate mode. Read
      failures: `no-bash-writes` matched `2>/dev/null … lending/` (any
      `>` counted as a write; the pattern now needs a write token and an
      app path in the same shell segment, 23 synthetic commands checked);
      `library-app-structure-review` judge counted `main/jobs.ts` business
      sequencing and `lending/` importing `main/wiring.ts` as "main/
      reported as a violation" (criterion now says those pass);
      `test-quality-review-fines/finds-subject-mocked` failed 4/4 because
      the review proposed deleting the can't-fail test (the first test
      already covers the real `run`) and shared Critical with the
      unwired-mock test (criterion now accepts both);
      `code-review-catalog/nothing-above-low` failed 4/4 on the bare `2`
      rated Medium, a fair readability point, so the fixture now names
      `MIN_TERMS_LENGTH` with a why comment; `tdd-implementation-named-fix`
      never ran the final reviewers in 4/4 runs because the skill's
      handed-back section ended at "report" while FINAL REVIEW said it
      applies after a fix too (step 5 added to the section).
      `why-comments-collect-fine/stays-on-comments` 2/4: the skill wanders
      into code review (retry loop, duplicated description); recorded as
      is, a skill question for G. Two single-run bars carry one failed
      grader (`code-review-fine-notices-pr-via-agent`,
      `reliability-review-nightly-via-agent`); re-run at 3 when cheap.
      Third run (38406868836, $2.34 before the balance ran out):
      `code-review-catalog`, `library-app-structure-review`,
      `map-update-cancel-hold`, `test-quality-review-fines` all 1.00,
      recorded. `tdd-implementation-named-fix` 0.85 then 0.81: it still
      fails `no-bash-writes` (unknown command; no trace, see below) and
      `final-review-runs`, and this time the report says why: "code-review,
      security-review and reliability-review were not run. The change is a
      constructor-injection refactor", "applied by reading the files
      myself". The skill's step 5 now says all four, however small. The
      cancel-hold cases got one run each (0.38 direct over 40 turns, 0.41
      via-agent over 3 turns) before the balance died; both need traces to
      read. No traces reached the artifact: the CLI deletes its scaffold on
      exit, so the gate now passes `--keep-temp`, copies the trace beside
      the result and removes the scaffold itself.
      Fourth run (WSL2 Ubuntu 26.04 on the subscription, traces kept,
      2026-10-13): `named-fix` 0.92 over 20 turns, `cancel-hold` 0.92
      over 38, `via-agent` 0.64 then 0.70 at 3. All four reviewers ran
      after the handed-back fix (step 5 verified, 1/1). Traces read:
      `no-bash-writes` fires on real shell writes, not a false match:
      the named-fix run applied the fix with a Python heredoc over
      `lending/return-book.ts` and `main/server.ts`, did the can-it-fail
      flip with `sed -i`, and wrote the report with `cat >`; every
      via-agent run (4/4) created the test and the use case with `cat >`
      heredocs and never called Write or Edit, which is why every
      ordering grader reported "Write never called". Not harness-induced:
      CLI 2.1.296 injects its Bash-first editing steer only in auto or
      bypass mode, and evals run under dontAsk. The skill never said
      which tools to edit with; it now does (Write/Edit only, including
      the can-fail flip and the report). The grader stays as it is.
      The direct `cancel-hold` run was disciplined (Write/Edit, three
      cycles, RED seen on cycle 2, can-fail check, four reviewers) and
      lost two graders to their own strictness: `red-then-green-per-test`
      wanted three RED-then-GREEN pairs, but cycle 3 legitimately passed
      first (the skill allows it and the report said so) and cycle 1's
      red summary was cut off by the model's own `| head -30`;
      `reviews-each-cycle` wanted four cycles and the design has three
      behaviours. Now `test-run-after-each-test-edit` {3} (a summary line
      before any other edit) plus `red-then-green-seen` {1}, and reviews
      at {3}. Checked against the kept traces: the direct run passes all
      nine trace regexes, the heredoc via-agent run still fails four.
      The earlier "edited before invoking the skill" run did not recur
      (skill invoked at turn 2 in every run). Two name misses: one
      via-agent run called `architecture-cartographer:map-query` first
      (not found) because the skill text named it that way; the text now
      names `map-query` / `kad-dev-team:map-query`. And the first `Agent`
      call in every via-agent run used `kad-dev-team:tdd-coach` and got
      "not found": 2.1.296 lists agents as `kad-dev-team:tdd-coach:AGENT`.
      The model recovers in one turn and the display grader accepts
      both; left alone.
      Verification run (one each, new skill text): `named-fix` 1.00,
      `cancel-hold` 0.96, `via-agent` 0.96, every file now written with
      Write/Edit, the can-fail flip included. The two misses were grader
      faults: the model called Write with a `path` key instead of
      `file_path` (the CLI accepts it), so every grader anchored on
      `"file_path"` missed the test file; all case files now match
      `"(?:file_path|path)"`. And `test-run-after-each-test-edit` looked
      for the runner's summary line, which the model's own `| head -20`
      cut off on cycle 1; it now looks for the `npm test` command itself
      between the test edit and the next edit.
      Recording run at `--runs 3` (gate option added): `cancel-hold`
      1.00, `via-agent` 1.00, both recorded. `named-fix` 0.92 x3, every
      run failing `last-test-run-green`: with the can-fail flip now done
      by Edit, the model breaks, runs (red), restores, and reports "the
      suite was green again" without running it. A narrated result, the
      thing the skill's first rule forbids. The REPEAT section now says
      the restore must be re-run and the last run before reporting must
      be green. Re-run at 3: 1.00, recorded. All three tdd bars are gate
      mode at three runs with per-grader rates.

## D. Phase chains

- [x] D1. Re-freeze `security-requirements`, `reliability-requirements`,
      `supply-chain-review-accept` and `technology-bootstrap` chains from
      the current skill text, with each case's own `allowed_tools`. Phase 2
      stops at the fork with no criteria written (the skill's own rule).
      Run (phase-1 runs to freeze from).
      *2026-10-14, done.* Every history is current
      (`tools/history_stale.py`). The skill's rule did not say it: both
      requirements skills said "get approval before writing them in" and,
      in the same breath, "a criterion that depends on a pending decision
      waits for it; write the rest", so every phase-2 run wrote the whole
      document with the decisions marked pending, and the phase-2 judge
      failed two runs in three on `does-not-decide-the-fork-itself`
      against documents of three thousand words that said "nothing is
      marked approved" at the end (`gate-20261014T104758`,
      `gate-20261014T045557`). Both skills now say approval comes before
      the document: after the questions, the next response is the forks
      (one at a time through `AskUserQuestion` when it exists, all of
      them in one plain-text turn when it doesn't), no criteria yet, and
      the document is written once after the approvals. That is also
      what the real flow does when the question tool is there. A
      staleness check over every `history.jsonl` (diff of the loaded
      `SKILL.md` text against the file) found two more stale chains
      besides the audit's three: `architecture-design-payfine-phase2`
      (the 2026-10-14 `map-query` naming fix) and
      `operational-readiness-ops-phase2`; both are re-frozen here too.
      `technology-bootstrap-phase2`'s history is current, but phase 3's
      is re-frozen from a new phase-2 run because the phase-2 prompt
      changed (below). `eval_gate.py --keep-scaffold` keeps a run's
      directory for `freeze-history.sh`, so a freeze comes from a gate
      run instead of a hand-run CLI.
- [x] D2. Phase-3 graders: keep only what phase 2 could not contain (the
      decision record, the flipped choice, duplicates-findable).
      *2026-10-14.* With D1's skill rule, phase 2 cannot contain criteria
      at all, so the two requirements phase-3 cases keep their criteria
      graders and gain `decisions-all-approved` (the user's "go with your
      recommendations" approves every other fork; nothing may stay
      pending) and grade the saved file (`docs/pay-fine/
      <skill>-001.md`, `Write` granted, `leaves-the-code-alone` guard)
      instead of a long `last_message`. `technology-bootstrap-phase3`
      drops `defers-persistence-with-the-in-memory-reason` (folded into
      `records-non-choices-and-open-categories` as the required reason)
      and `pinning-posture-treated-as-a-choice`, which moves to phase 2
      where the recommendation is actually made; it gains a
      `writes-nothing-else` guard (the runs offered to scaffold; the
      document is the output). `technology-bootstrap-phase2`'s prompt now
      asks for the whole set in one message: two runs in three followed
      the skill's one-at-a-time loop literally (runtime first, UI
      framework "next"), which the UI-framework grader and the
      supply-chain consult regex both read as a miss; the grader also
      accepts "comes next, not settled".
- [x] D3. Add one rejecting chain: `technology-bootstrap-phase3-reject`
      ("no, npm and Jest"), graded on recording the user's choice and the
      recommendation as rejected. *2026-10-14.* Same frozen phase 2 as
      phase 3; graded on the saved file: the user's choices decided with
      their reason and the recommendations recorded as rejected, no
      re-arguing, and the pinning posture restated for npm (`npm ci` is
      a remembered command, not a default) rather than dropped.
- [x] D4. `design-system-payfine-phase3`: reword
      `chosen-direction-committed` and `rejected-candidates-in-prose` so
      they don't name the frozen candidates; have the scaffold write the
      three candidate files. *2026-10-14.* The scaffold recreates them
      from `history.jsonl` with the new `tools/history_files.py` (the
      resumed run had nothing to rewrite into `visual-ux/` before). The
      direction graders say "the second of three candidates" and count
      two rejected ones; which candidate won is a trace regex for the
      second candidate's brand colour in the `visual-ux/` mockup, pinned
      in the case and checked by the scaffold so a re-freeze fails
      loudly. `rejected-candidates-in-prose` had failed 2/3 on documents
      that gave each rejected candidate a reason of the document's own
      ("warmer than a money-owed screen needs"); the criterion now says
      any kind of reason counts.
- [x] D5. Phase-1 question graders: `requirements-refinement` requires the
      trade-off and rejected-alternatives questions;
      `operational-readiness-release-phase1` requires the rollback
      question. *2026-10-14.* Each is its own grader
      (`asks-trade-off-and-alternatives`,
      `asks-whether-rollback-was-ever-run`).
- [x] D6. `requirements-refinement-payfine-phase2`: leave one thing unsaid
      in the prompt (what staff see) and grade that the doc marks it open.
      *2026-10-14.* "shows as paid to them and to staff" is now "shows as
      paid"; `marks-what-staff-see-as-open` fails a document that
      confirms a staff-facing view either way or says nothing about it,
      and `in-scope-as-confirmed` lists a staff-facing view among the
      capabilities that must not be added.
- [x] D7. Re-run the chains, re-record. Run.
      *2026-10-14, done.* Four passes in WSL2 (about 170 runs in all, one
      five-hour window); every phase-D case has a gate-mode three-run bar
      and current evidence. What the runs turned up, in order:
      - The two requirements phase-2 cases stop at the forks in every run
        once the skill says approval comes before the document; their
        phase-3 cases score 27/27 each on the saved file, the user's
        overrule recorded and every other decision approved. The
        phase-2 fork grader still loses a run in three to the judge
        reading an openly stated assumption or a firm heading as a
        decision; two rewordings got it from 4/6 lost to 1/3, and the
        bars (0.92) carry the rest.
      - `technology-bootstrap-phase2`: two runs in three followed the
        skill's one-at-a-time loop literally (runtime first, UI framework
        "next"), which the UI-framework grader and the consult regex
        both read as a miss; the prompt now asks for the whole set in
        one message. Every run then argued the UI framework is not forced
        by a domain-level first test, so both phase-3 prompts approve the
        deferral instead of React with Vite. Phase 3's approval grader
        demanded rejected alternatives inside each entry while the
        template gives them their own section (0/3 until reworded).
      - `technology-bootstrap-phase3-reject` (new): 18/18 once its
        relitigation grader let a sub-choice that follows from the
        overrule (a committed `.npmrc`) stay open; recorded at 0.89 from
        the last batch, where one run lost `does-not-relitigate` again.
      - `requirements-refinement-payfine-phase2`: the staff-view grader
        scored 0/9 over three batches because the scripted answer's
        "desk staff, who should stop taking these payments" reads as
        answering the phase-1 staff question; with staff left out of the
        answer it is 1/3, and that one is the skill's new rule working
        (an unanswered question recorded as a finding to resolve). Two
        skill rules came out of it: an answer that skips a question is
        recorded as not yet confirmed and asked again; a finding names
        what is forced and its owner, not the code change (two runs in
        three had prescribed the member route and its ownership check,
        which `no-thin-path-or-criteria` caught, 3/3 after the rule).
      - Then `history_stale.py` showed those three batches had run
        phase 2 against the history frozen on 2026-10-11, carrying the
        skill text from before both rules: a resumed phase runs the
        text in its history, not the file. Phase 1 re-run and re-frozen
        (twice: the second after a third rule), the gate now warns
        before running a case whose history is stale. With the current
        text, all three runs record "Not yet confirmed" and two of
        three name the staff view there. The replies then re-asked
        things the user had answered (a deadline when they gave the
        why; other alternatives when they gave one), which the
        `finishes-without-reasking` grader caught 3/3; the skill now
        says a question answered without every example is answered.
        Final sample 24/27: one run clean, the other two re-ask a long
        list of genuinely open items (waivable fines, duplicate
        charges, how card details are collected) and the judge reads
        the list as re-asking; recorded as it scores (0.89).
      - `vertical-slicing-handback` lost a run to the skill not firing
        at all ("Sort it out."), then went 3/3 again: a trigger flake for
        G to look at. `orchestrator-route-design-system` routes to
        `reliability-requirements` one run in three on the unlabeled
        slice fixture, every batch; bar recorded at 0.89 (F1).
      - Sourcery on PR #3 (2026-10-15): five findings, four taken. The
        gate now refuses to run a case whose history carries stale skill
        text (it had only warned, and would have recorded evidence for
        the old text); `wsl-gate.sh` sets `TMPDIR` regardless of the
        environment's value (`KAD_EVAL_TMP` overrides);
        `history_files.py` resolves symlinks before its containment
        check; `decisions-all-approved` on both requirements phase-3
        cases names the forks phase 2 presented (pinned from the
        history, re-pin after a re-freeze) so a document that drops one
        fails. Declined: a collision-proof tag for two gate processes
        started in the same second, since one subscription runs one
        gate. Both phase-3 cases re-run: security 27/27, reliability
        26/27.
      - Facts for the handoff: WSL's `/tmp` is a tmpfs that dies with the
        VM seconds after each `wsl` command, so kept run directories now
        live under `~/.cache/kad-eval-tmp` (`wsl-gate.sh` sets `TMPDIR`);
        the Windows checkout had rewritten every `.sh` with CRLF after
        the merge, so `.gitattributes` pins them to LF; the CLI appends
        an `ARGUMENTS:` line to a skill invoked with arguments, which the
        staleness check ignores.

## E. Leaks (edits only, re-run with C5 or D7)

Done 2026-10-15 on branch `eval-phase-e`. Three gate passes in WSL2
(15 cases, then 7, then 1; about 70 runs); every case the edits reach
has a gate-mode three-run bar and current evidence.

- [x] E1. `acceptance-criteria-payfine`: new vague criterion, not the
      skill's worked example (or move the example out of the skill).
      *"Paying a fine is quick; the member isn't left waiting."* The
      undecided thing is now a time bound instead of a failure outcome,
      so `flags-undecided-behaviour` became `flags-undecided-target`
      (a stated bound must be flagged for the user or routed to the
      reliability placeholder). 9/9; the skill's "handles errors
      gracefully" example stays where it is.
- [x] E2. `vertical-slicing-handback`: different handed-back capability in
      the fixture, no option menu in `security-requirements-001.md`;
      change the skill's refund example.
      *The hand-back is a receipt the merchant agreement requires;* the
      section states the gap and that it is handed back, nothing about
      how the slice could change. The skill's example is now a
      guardian's consent step. `orchestrator-backward-route` shares the
      fixture and its grader had kept the refund wording: it failed a
      run that routed correctly and, as product-slicer, chose growth
      with a reason against each other option (a receipt cannot be
      demonstrated before a payment exists); reworded to say a chosen
      option with the others rejected is product-slicer's job. The
      first handback run also read "recorded against their own card
      number" as the payment card, contradicting the no-card-number
      criterion; the fixture now says library card number. Sourcery on
      PR #4 (taken): `leaves-the-what-to-requirements` called the
      receipt's contents undecided while the fixture says the merchant
      agreement fixed them; the rubric now treats the agreement's facts
      as settled and sends only the rest (channel, re-viewing, who may
      see it, retention) to requirements. Re-ran 15/15.
      **Real miss found:** one run in three answered the hand-back
      without the skill and wrote the receipt slice in full, edited
      `slice-001.md` and marked the hand-back picked up (the exact
      behaviour the skill's hand-back section forbids). The skill has
      that section but its description never mentioned a hand-back, so
      "Sort it out" on a security document did not trigger it (the
      2026-10-14 handoff had seen the same in one run of six). The
      description now names a scope change handed back by a later
      stage; 15/15 after, and `vertical-slicing-payfine-phase1`,
      `vertical-slicing-no-requirements`, `orchestrator-route-slicing`
      re-ran 1.0 on the new text.
- [x] E3. Cut the hint sentence from `security-review-reminders`,
      `reliability-review-http`, `reliability-review-fine-payment`; drop
      the staleness sentence from `map-query-consults` and make the map
      header date carry it.
      *All three reviews 3/3 with every plant found and no trap taken.*
      `map-query-consults`: the prompt says only that cancel-hold merged
      this morning; the map's "updated 2026-09-28" header is the only
      evidence, and every run caveated it (the grader now says so).
      One run grepped `docs/` (which holds only the map) to confirm no
      cancel-hold entry; `answers-from-the-map` forbade any Grep not
      naming the map and now allows the docs folder. 18/18 after.
      Sourcery on PR #4 (both taken): the allowance matched
      `architecture-map` anywhere in the Grep input, so a source grep
      for that word passed, and it missed a bare relative `docs` path;
      the guard is now anchored on the `path` key (the docs folder or
      the map file, relative or absolute). Re-ran 1.0, 1.0, 0.94 (one
      2-1 judge split on `honest-empty-result`, the grader that was at
      0.667 before this phase); bar left at 1.0.
- [x] E4. Remove persona names from `pay-fine-security/design-001.md`,
      `pay-fine-screen/…/screen-design-001.md`, `backward-pm/slice-000.md`.
      *Done, and `pay-fine-handback/design-001.md` (same section).* The
      design docs end with "Open questions: none"; the screen design
      says only that the accessibility criteria are still a placeholder;
      `slice-000` says nobody confirmed the step's WHAT and no
      requirements document covers it. The slice placeholders
      themselves ("to be authored by devsecops-engineer") are the slice
      template's own text and stay: the orchestrator's routing table
      keys on them. The three route cases went 3/3 each.
- [x] E5. `test-quality-review-fines`: reword the prompt so it isn't the
      description's trigger sentence.
      *"I'm not confident it would catch a real bug. Have a look at the
      file and tell me what you make of it."* The skill fired in 6/6
      runs (the README had recorded it not firing until the description
      quoted the old sentence). The new wording pulled every review
      toward "what bug would slip through", so each said the sound
      exact-value tests were thin (one data point, no boundary case) and
      suggested more; `no-false-alarm-exact-tests` ("does not report any
      of these as weak") lost 3/3 to that, and had been at 0.667 before.
      It now fails only a genuine false alarm (false positive, cannot
      fail, wrong assertion, brittle-because-exact, implementation
      detail) and says a sound-but-thin verdict with suggestions is
      fine. 29/30 after; the one loss is a 2-1 judge split on a
      9.5k-character review, bar 0.97.
- [x] E6. `scope-map-self-service` fixture: drop the sentence that
      generalises the privacy constraint for the skill.
      *Dropped; the grader's framing now says the doc says nothing
      wider.* 15/15, privacy routed to every step's requirements pass
      in every run (the previous bar had a borderline miss).

## F. Routing, restraint, UI

Done 2026-10-15 on branch `eval-phase-f`. Edits in `61afee4`; the runs
and what they taught are under F10. The change reached 64 cases: the 26
whose graders changed outright, the 32 that hold a trap grader (F4) or
copy the shared UI slice (F1), and six more through the two skill fixes
(`adr` reaches `technology-bootstrap-phase3` and the tdd via-agent case
through agent files; the orchestrator row reaches every orchestrator
case). Every one has a gate-mode three-run bar and current evidence.

- [x] F1. Each `orchestrator-route-*` case: one LLM grader on
      `orchestrator-log.md` (names the matched row and an artifact path
      under the target) and one on `last_message` (ends with the routed
      skill's questions or a stop, not the next artifact).
      *Done for all thirteen route cases, `orchestrator-backward-route`
      (log grader: names the hand-back, not just the destination) and
      `orchestrator-route-implementation` (its log grader existed; the
      final-message grader accepts a stop to ask about the quarantine
      flow's cost, a report that the flow could not be launched without
      an `Agent` tool, or its outcome). The final-message rubric accepts
      either ending the orchestrator's step 5 allows: the routed skill's
      own questions, or the routed step's result plus the question
      whether to continue, with nothing from a later stage produced.*
      *The fixture note:* `ui-plants/pay-fine/slice-001.md` now prefixes
      its two security bullets with "Security:" and the double-charge
      bullet with "Reliability:", the convention the cancel-hold slice
      already used. The 2026-10-14 traces showed
      `orchestrator-route-screen-design` (bar 0.89, one run routed to
      `reliability-requirements`) losing its run the same way as
      `orchestrator-route-design-system`; both bars should return to 1.0.
      The nine UI cases copy the slice, so their evidence all went
      stale together.
- [x] F2. `orchestrator-asks-for-target`: fix the `\\.md` regex and check
      `Grep` as well as `Glob`.
      *The single-quoted `'\\.md'` was the regex `\\.md`, a literal
      backslash; now `'\.md'`. A second `tool_used` guard matches the
      same words in `Grep` input. Checked against `**/*.md`, `docs/**`,
      `**/problem*` (fail) and `src/**/*.ts`, `*.json` (pass).*
- [x] F3. Restraint cases (`*-catalog-review`): add a positive grader
      requiring at least two of the module's real controls to be named.
      *`names-what-holds-it-up` on each of the four catalog cases
      (architecture, security, reliability, code review), each listing
      the module's actual controls from the source (bound `$1`
      parameter and `escapeLike` inside it, the `catalog_reader` role
      and pool, the 2-character minimum and 50-row cap, the
      `CatalogUnavailable` translation, the generic 503 with path and
      reason only, the named constants and the WHY comment). Paraphrase
      counts; generic praise does not.*
- [x] F4. Every "does not flag" trap grader: PASS only if the review has at
      least one real finding and none is the trap.
      *Sixty graders in thirty-three cases: every `no-false-alarm-*`,
      the three restraint graders in `code-review-fine-notices-pr` (and
      via-agent), the three `keeps-*` in `code-review-days-left-pr`,
      `respects-documented-rounding-split`, `no-enterprise-ceremony`,
      `no-retry-of-declines`, `keeps-the-one-implementation-port`. Each
      keeps its wording and gains a closing paragraph sized to what it
      judges: a review must also report at least one real finding; a
      phase-2 response must also present at least one real fork; a
      criteria document must also hold at least one Given/When/Then
      criterion; the design doc must also record a decision. The catalog
      cases' `reports-nothing-above-low` are restraint on a clean module
      and keep their floor through F3 instead.*
- [x] F5. `accessibility-review-payfine-subtle`: copy
      `leaves-the-mockup-alone`, `says-it-read-the-markup`,
      `criteria-split-now-and-later`; both accessibility cases: grade
      `slice-001.md` for the filled placeholder.
      *Done; the subtle case's criteria grader asks for the Pay button's
      focus indicator and the error-to-field association at least. Both
      cases gain `slice-placeholder-filled` (the placeholder line gone,
      Given/When/Then criteria in its place, other criteria unchanged)
      and `writes-only-review-and-slice`. The skill's output template
      says the criteria replace the slice's placeholder but never says
      to edit the slice file; the prompt asks for it, so the runs will
      show whether the skill needs the sentence.*
- [x] F6. `screen-design-payfine`: trace regex on the mockup Writes for the
      system's token values; `design-system-payfine-phase2`: pin candidate
      filenames and grade the files.
      *`mockups-carry-the-system-brand-token`: three Writes to
      `visual-ux/*.html` each carrying `#1F5F5B` (`--brand`) in their
      own content, either key order, matched as a JSON string so the
      HTML's braces and quotes don't cut it short; checked against
      three good writes, two of three, writes outside `visual-ux/`, and
      a hex that appears only in a later write. Phase 2's prompt now
      names `docs/pay-fine/design-candidates/candidate-N.html`; two
      `file_exists` and two file-judged `candidate-N-is-a-real-render`
      graders (a full phone-width page of the pay-fine screen with
      concrete values, not a swatch or a hedge). Distinctness between
      candidates stays judged from the final message: an LLM grader
      reads one file, and `focus: trace` elides the middle of the run.
      The prompt change makes `design-system-payfine-phase3`'s history
      (frozen from a phase-2 run) describe a different turn, so F10
      re-runs phase 2 with `--keep-scaffold`, re-freezes phase 3 from
      it, and re-pins the second candidate's brand colour in phase 3's
      grader and scaffold check.*
- [x] F7. `architecture-design-payfine-phase1`: trace guard against any
      Write under `docs/pay-fine/`.
      *`writes-nothing-under-pay-fine`, Edit or Write, `not_contains`.*
- [x] F8. `adr-*`: regex on the three worthiness checks in the response.
      *`opens-with-the-three-checks` on the trace: `Architectural`,
      `Significant`, `Non-obvious`, each answered yes or no, bold
      markers allowed, in that order; the skill's own template in the
      trace says `yes/no` and is excluded by a lookahead for `/`.
      Checked against the template alone (fail), plain and bold answers
      (pass), prose with no checks and two of three (fail).*
- [x] F9. `vertical-slicing-payfine-phase1`: `tool_used` on
      `acceptance-criteria`; grade the deferred and still-open sections.
      *`consults-acceptance-criteria` (the skill says to invoke it before
      writing the criteria) and `deferred-and-still-open-are-real` on
      the slice file: both sections present and specific, or an
      explicit nothing-to-defer with a reason; filler fails.*
- [x] F10. Run the changed cases, re-record. Run.
      Batches in WSL: the 26 cases whose graders changed outright;
      `design-system-payfine-phase2` with `--keep-scaffold`, then the
      phase 3 re-freeze and re-pin, then phase 3; then the 32 reached
      only by the F4 floor or the F1 fixture. Read every failure before
      recording a bar.
      *Batch 1 (2026-10-15, 26 cases, 78 runs, 24 passed):* every
      failure read.
      - `adr-payment-gateway` 0.80: all three runs loaded the skill and
        went straight to `Write`, no worthiness checks anywhere in the
        trace, though the skill says the response opens with them.
        `adr-neg-rename` 0.89: one run answered "Significant:
        borderline". **Real miss, fixed in the skill:** write the three
        lines even when all three are plainly yes, and each is a yes or a
        no with its reason.
      - `orchestrator-route-design-system` 0.83: with the fixture
        labelled, one run still routed to `reliability-requirements`,
        reasoning that one reliability criterion leaves "failure
        behaviour otherwise unspecified". The row said "reliability
        behavior has never been made concrete", a semantic read step 2
        forbids, while the security row keys on the placeholder.
        **Fixed in the skill:** the row now says "reliability criteria
        are still an unfilled placeholder". Reaches every orchestrator
        case (16), all re-run in batch 2.
      - `orchestrator-route-slicing` 0.95 and `-scope-decision` 0.90:
        the new final-message grader lost 3-0 votes on correct runs.
        `rejudge.py --explain` showed the judge reading a slicer's own
        call ("same fine is keyed on the fine ID, which was my call") as
        the orchestrator answering the routed skill's questions, and the
        scope-map step's "no map needed, one unit" result as the
        orchestrator deciding for the skill (both runs had invoked
        `scope-map`). Rubric reworded: a skill that delivers without
        needing to ask, making judgment calls inside its work, is the
        second ending; FAIL only when the skill had stopped to ask and
        the response answers in the user's place; scope-decision names
        the no-map result as the step's result.
        `orchestrator-route-reliability` 0.96: the log grader failed a
        correct entry 3-0; the explained judge first failed it, then
        corrected itself to PASS. Noise on the heading paraphrasing the
        row; the rubric now accepts the row's words or the entry's own
        and says the heading need not list every element.
      - `screen-design-payfine` 0.92, three different graders over three
        runs: the brand-token regex missed a run that put every rule in
        a shared `visual-ux/screen-design-001.css` the mockups link
        (pattern now accepts one `.html` or `.css` Write under
        `visual-ux/` with the value; the file count stays with
        `three-mockups-in-visual-ux`); the judge read a "Paid" group on
        the same page as payment history and a "choose and pay" default
        view as a missing list state (both rubrics now say what counts).
      - `rejudge.py` could not send a prompt holding `→` on Windows
        (cp1252 stdin); fixed.
      The other 19 cases went 3/3 on every grader, including all four
      catalog positives, both accessibility `slice-placeholder-filled`
      graders (the runs edit the slice unprompted by the skill text),
      `vertical-slicing-payfine-phase1`'s consult and sections, the
      ADR-free `architecture-design` phase 1 guard, and the asks-for-target
      regex fix (no run searched).
      *Batch 2 (2026-10-15, 19 cases, 57 runs, 17 passed):* the sixteen
      orchestrator cases after the row change, both adr cases, screen-design.
      - `orchestrator-route-design-system` 1.0 (was 0.83 and 0.89),
        `-screen-design` 1.0, `-reliability`, `-scope-decision`,
        `-slicing` 1.0 on the reworded rubrics; `orchestrator-security-stage`
        and `-superseded-scope-map` 1.0 on the new row.
      - `adr-payment-gateway` 0.80 again: the new paragraph was loaded and
        all three runs still went Skill, Write, "I wrote the ADR" with no
        checks anywhere. The rule is now the skill's step one in so many
        words: the three lines come before any tool call, and a fully
        argued request is the case most worth checking. `adr-neg-rename`
        1.0 on the first wording.
      - `orchestrator-route-user-story` 0.90: two log entries left the
        artifact to the skill ("see the skill's own output"; the
        directory with "destination to be decided by the skill"). A
        story's file name is the skill's, and it may not be a local file
        at all, so the rubric now accepts the directory and fails only an
        entry that names no location under the target.
      - `orchestrator-backward-route` 0.95: one run routed to
        product-slicer, cut the receipt slice, then narrated the whole
        round trip (requirements-002, design, security) and opened with
        requirements-refinement as what's next; the existing
        `routes-back-to-the-owner` failed it 3-0. The skill forbids that
        narration in its own words; one run in three, left as recorded.
      - `screen-design-payfine` 0.92: `reuses-the-system` lost 8 of 9
        votes across all three runs on documents that say no new pattern
        is needed and then list two optional additions under the
        new-patterns heading; the explained judge called that a
        contradiction while conceding it was a close call. The rubric
        now says that is the second form, not a contradiction. The new
        brand-token regex passed 3/3 on the .html-or-.css form.
      *Batch 2b and 2c (2026-10-15):* user-story 1.0 and screen-design 1.0
      on the reworded rubrics; `design-system-payfine-phase2` 1.0 on the
      pinned names (every run wrote `candidate-1.html` to `-3.html` under
      `docs/pay-fine/design-candidates/`; both file-judged candidates
      passed every run).
      - `adr-payment-gateway` 0.80 a third time: with "step one, before
        any tool call" loaded, all three runs still went Skill, Write,
        "I wrote the ADR". Nine of nine runs under two wordings that kept
        the checks in the reply. **Fix that took:** the template gains a
        "Why this is an ADR" section holding the three lines, and the
        skill says the lines go there when the ADR is written, so the
        document carries its own justification and the model writing the
        file writes them. 1.0 after (and `adr-neg-rename` 1.0 on every
        wording: when the answer is no, the checks are the reasoning, so
        they were never skipped there).
      - `design-system-payfine-phase3` re-frozen from phase 2's run 0
        ("Friendly Neighbour" picked the branch); second candidate's
        `--brand` is `#0b6e7a`, pinned in the grader and the scaffold
        check. First run on the new history 0.81:
        `rejected-candidates-in-prose` lost every run on documents that
        name two rejected candidates with reasons and link only the
        winner, now saved as `visual-ux/candidate-2.html`; the explained
        judge failed it on that link, then corrected itself to PASS. The
        rubric now says the winner's file may keep its candidate name and
        only a link to a rejected candidate's file counts.
        `accessibility-by-construction` 2-1 in two runs (0.667 before this
        phase; the CLI flags the 8-9k-character file as judge-noisy).
      *Batch 3 (2026-10-15, 35 cases):* hit the subscription's session
      limit after two cases. `design-system-payfine-phase3` passed on the
      clarified rubric and `architecture-design-payfine-phase2` on its
      floor; `library-app-lending-review` was cut off mid-case (0.41 over
      two runs is the limit, not the skill); the other 32 errored on every
      run. **To resume** (after the reset the error names, 12:40pm
      America/New_York): `wsl -d Ubuntu -- bash evals/tools/wsl-gate.sh
      --stale --runs 3`, read every failure, then record bars for every
      phase-F case with `record_thresholds.py --gate-only` (no bar has
      been recorded yet in this phase; the gate wrote evidence only), check
      `eval_evidence.py --base origin/main`, update the hand-off, open the
      PR.
      *Resumed after the reset (33 cases, 99 runs): 33/33 passed.* The
      graders lost, each read: `code-review-fine-notices-pr`
      `leaves-mocking-to-test-quality-review` in two runs (0.333; the
      explained judge passes the run: the mocking is named in the
      hand-off section and the ranked finding is about the test names,
      a close call on wording); `reliability-review-alerts`
      `no-false-alarm-burn-rate-alerts` 3-0 in one run on an 11k-character
      review that praises both alerts (the explained judge passes it);
      `reliability-review-nightly` duplicate-fines trap 2-1 once on a
      16k file; `supply-chain-review-build` dependabot trap and
      `test-quality-review-fines` exact-tests trap once each, both at
      their previous bars; the tdd via-agent case's two trace regexes in
      one run (0.97, as before). None of the five trap losses was the new
      floor: every review had real findings, and the explained judge
      named the trap's own wording each time. The floor itself cost no
      run anywhere in the 33 cases that carry it.
      *Bars recorded* (`record_thresholds.py --gate-only`, 64 cases; no
      case went stale from recording this time). Moved: up to 1.0 for
      `accessibility-review-payfine`, `design-system-payfine-phase2`,
      `orchestrator-route-design-system` (0.889), `-screen-design`
      (0.933), both requirements phase-2 chains (0.917; the forks grader
      went 3/3 this time), `reliability-review-nightly-via-agent`;
      down for `code-review-fine-notices-pr` 0.97 to 0.94,
      `orchestrator-backward-route` 1.0 to 0.95 (the round-trip
      narration above), `reliability-review-alerts` 1.0 to 0.94 and
      `reliability-review-nightly` 1.0 to 0.97 (long-file judge noise,
      both). `adr-payment-gateway` 1.0 with the checks in the document.
      Open for G: the orchestrator narrating the backward round trip
      (one run in three), and the three long-file review traps that lose
      a run to the judge each pass.
      *Sourcery on PR #5, ten findings, seven taken:* the ADR trace regex
      had gone vacuous once the template itself said `yes — <why>` (the
      runs did write the section, but the grader could not tell);
      `adr-payment-gateway` now grades the written file for the "Why
      this is an ADR" block and `adr-neg-rename`'s trace regex excludes
      `<why>`, and the skill says where the lines live (reply when
      declining, document when writing). `each-mockup-styled`: every
      mockup carries the brand value or links a stylesheet (checked
      against all nine recent runs, including the shared-.css one).
      The accessibility write guard anchors its two allowed paths
      (`backup/docs/pay-fine/slice-001.md` tripped it before; now a
      stray). `consults-before-writing-the-slice`: no write of
      `slice-001.md` before the `acceptance-criteria` consult.
      `orchestrator-asks-for-target`: any `Glob` or `Grep` before asking
      fails, whatever its pattern. `orchestrator-route-implementation`'s
      log grader also wants the artifact line or the quarantine
      sub-entries. Declined: a cross-file distinctness check on the
      phase-2 candidates (an LLM grader reads one file and `focus:
      trace` elides the middle of the run; still judged from the final
      message, as recorded under F6); trace checks that no later-stage
      skill ran on the route cases (each already carries two or three
      `not-<skill>` `tool_used` guards for exactly that); the
      `subprocess.run` audit in `rejudge.py` (its argument list is built
      from constants and the model name, no user string reaches a
      shell); that one is opengrep's static rule and the only item that
      kept Sourcery's check red after the fixes, so the call now carries
      the reason in a comment and a `nosemgrep` marker for that rule.
      *Re-run after the Sourcery fixes (eleven cases, 33 runs, after one
      session-limit false start):* 10/11 passed first time; both adr
      cases 1.0 on the file-graded block, both accessibility cases,
      slicing (consult before every write in 3/3), asks-for-target
      (no Glob or Grep at all), screen-design (`each-mockup-styled` 3/3;
      `copy-rules` lost one run 3-0, bar 0.97), the two agent-file cases
      1.0. `orchestrator-route-implementation` 0.83: the tightened log
      rubric failed three correct entries, because the skill writes the
      entry before invoking the flow and its template says "see
      sub-entries below", which is the right line when the run stops to
      ask; rubric now says so, 1.0 after. Bars recorded for the eleven.

## G. Only after A–F

G3, G4 and G5 done 2026-10-16/17 on branch `eval-phase-g` (PR #7, merged
2026-10-17, `c6b9e19`), in the order G5, G4, G3 (the two carried-over
findings first, because their evidence was already in hand; the coverage
work needed runs of its own). G1 done 2026-10-18 (PR #16) and G2 done
2026-10-19 (PRs #17 and #18); nothing in this section is open.

- [x] G1. Harder plants and rejecting answers so scores leave the 1.0
      ceiling.
      *One harder plant landed with G3's review-mode case: the design
      system's `--muted` value was changed under a document that still
      claims the old contrast figure, so the reviewer has to compute
      rather than trust the text.*
      *Done 2026-10-18 on branch `eval-g1-harder-plants`, PR #16.* The hand-off's
      first candidate, a phase-3 answer that overrules a safety
      recommendation, was already covered: the security chain's phase 3
      keeps the shared staff route and the reliability chain's keeps
      "failed, try again" with duplicates refunded by hand. Four new cases
      for the other three candidates and H6's observation:
      - *The stop rule tested against its own restraint* (the hand-off's
        "arguable gap"): `security-requirements-payfine-phase2-proceed` and
        `reliability-requirements-payfine-phase2-proceed`, each on the same
        frozen phase-1 history as its phase 2 and stop case, with an answer
        that reads like the stop case's but carries no gap. Security: the
        merchant agreement requires that any online charge can be matched
        to the fine it paid and that disputes are answered within 14 days,
        which finance does by hand from Stripe's dashboard; the ledger
        already records the charge id on settlement (`settle(id, chargeId,
        on)`, migration 0012), so matching is a criterion on the slice's
        own data and disputes are a process outside it. Reliability: the
        day-long Stripe outages from the stop case, but a member who can't
        wait phones the desk and pays over the phone, so the target needs
        nothing unscoped. Graders: presents the forks, not a hand-back; the
        obligation or outage placed without stopping; the phase-2 fork
        grader and `no-criteria-before-approval` reused verbatim. *Runs:*
        security 3/3 at 1.0 on the first run (every run put matching in the
        criteria and disputes out of scope, and presented the route fork).
        Reliability 0.75 on the first run, the outage grader lost 3/3
        (`rejudge.py --explain` passed two of the three: the judge's own
        reading of "says nothing at all about the outage" was stricter than
        the one-word vote, and the third run really did fold the outage
        into the timeout fork without naming it). That clause was wrong
        about what a correct forks turn may omit: the skill says the forks
        response is the forks, and a provider outage with a fallback is a
        rule application the document covers, not a fork. Reworded as
        `does-not-invent-a-scope-gap`, two FAIL conditions and a list of
        what passes (G6's lesson, the short form): 9/9 on the recorded
        outputs under `--criteria-from`, then 3/3 at 1.0 on the re-run.
      - *A review plant whose defect only shows across files:*
        `reliability-review-portal-pay-pr`, overlay
        `code-plants/reliability-review/portal-pay/` (answer key R14, R15,
        RT10, RT11; verify.sh loops over it). A PR adds pay-a-fine to the
        portal: `PayOwnFine` charges with `{ idempotencyKey: fine.id }`, the
        port's comment promises a repeat is not charged again, the test
        asserts the key reaches the port; the Stripe adapter puts it in
        `metadata`, which the overlay's `types/vendor.d.ts` describes as
        labels Stripe never reads, and never passes the request option that
        deduplicates. The route answers "Payment failed, please try again"
        at the use case's 10-second timeout, so the retry double-charges
        (R14); the charge still in flight at the timeout is abandoned
        unrecorded (R15). Traps: the bounded wait itself (RT10) and the
        shared 404 for a missing fine and another member's (RT11, told apart
        server-side). *Run:* 3/3 at 1.0 on the first run: every run read
        the use case, the adapter and the vendor types, said the key as sent
        does not deduplicate, found the abandoned charge, and flagged
        neither trap. Hard for a human skim; not hard for a reviewer that
        reads the boundary, which is the behaviour the skill asks for.
      - *The pre-named stage from H6's second session:*
        `orchestrator-route-implementation-prenamed`, the cancel-hold
        scaffold with "if the next step is the implementation and its
        quarantine flow, go ahead with it", graded for the orchestrator
        invoked, no direct `tdd-implementation` call, the log entry, and a
        stop with nothing built. *First run:* 0/3, each run invoking
        `tdd-implementation` straight away, inline, with no orchestrator,
        no log and no sandbox check, and stopping only because the session
        has no shell: H6's miss reproduced exactly. The choice is made from
        skill descriptions before any body loads, so the fix is in both:
        the orchestrator's description and its "skip this skill" paragraph
        now say a stage guessed at in passing or conditionally is not a
        skill named, and that implementation reaches `tdd-implementation`
        only through the sandbox check and the quarantine flow;
        `tdd-implementation`'s description says the same from its side.
        *After the fix:* 3/3 at 1.0, every run routing through the
        orchestrator, writing the log, and stopping at the sandbox check
        (Bash disabled) with no code written; the sixteen other
        orchestrator cases and the three tdd cases re-ran at three runs,
        19/19 at 1.0.
      *On the ceiling:* the four cases sit at 1.0 after one rubric
      rewording. The two-file plant was found three times in three and
      the arguable gaps were not stopped on, so Sonnet with the skill is at
      the bar these cases set, and the headroom G1 was meant to open has
      not opened; what the round did produce is one real plugin defect
      found and fixed by a case (the pre-named stage) and the rubric lesson
      restated. A lite-versus-heavy comparison (G2) should therefore lean
      on the pairwise judge over bars.
      *Also:* `verify.sh` had been red since 2026-10-11 on the
      `code-review/days-left` overlay, whose test builds `Loan` objects from
      the planted runtime cycle and so cannot run; it now type-checks that
      overlay and says why it skips its tests. Bars recorded for the four
      new cases (118 cases with bars), evidence current for every case the
      branch reaches, every frozen chain current.
      *Sourcery on PR #16, five findings, two taken, three declined:*
      - *Declined, "staff and member payments can overlap" (High), "waived
        fine can still be charged" (Medium):* both review the planted PR as
        production code. The overlap of `PayOwnFine`, `CollectFine` and a
        staff waiver on one fine with no atomic claim is RR2's race across
        two routes; it is not planted, a review that raises it is right,
        and no grader fails it. Recorded in the answer key's
        not-false-alarms note for the overlay rather than "fixed" in the
        code under review.
      - *Declined, "successful charges remain outstanding" (High):* the
        late completion is R15, the plant; `ledger.settle` failing after a
        successful charge is R6 newly routed through. Both in the same note.
      - *Taken in part, "retries after a day can recharge" (Medium):* the
        request option covers only Stripe's window (24 hours in the SDK's
        contract), so a retry on a fine still outstanding a day later can
        charge again. The grader's PASS already accepted "or otherwise
        making a repeat attempt safe"; it now also says a review that names
        the window and asks for the attempt to be recorded is right, and
        R14's fix column says the same. Not made a requirement: the planted
        defect is the key sent to the wrong place, and the request option
        is its fix. Re-run 3/3 at 1.0.
      - *Taken, "overlay test coverage is overstated" (Low):* verify.sh's
        header now says the days-left overlay is only type-checked, and why.
- [x] G2. A lite variant of `tdd-implementation` as a second plugin dir,
      run through the same cases as a third arm.
      *Done 2026-10-18/19: PR #17 (merged `5e3e133`) and PR #18 (the
      augmented lite). Reframed 2026-10-18, branch `eval-g2-lite-tdd`.* Not a second plugin
      directory. The user's question was how a plugin user would choose
      between the two implementations for a slice, or run both to compare,
      so the variant is a sibling skill in the one plugin
      (`skills/tdd-implementation-lite/SKILL.md`) and the choice is the
      orchestrator's to offer. What lite is for, in the user's words: the
      default may dictate things a current model does on its own, so lite
      keeps only what the model cannot know — the contract (what it owns
      and does not, where things go, `Write`/`Edit` not the shell, the
      `map-query` consult, gaps decided visibly or escalated to a named
      owner, no edits to other stages' documents, the final reviewers
      unless the orchestrator grades, the report's shape) — and says
      nothing about how to run the loop: no Test List, no one test at a
      time, no RED seen failing, no `test-quality-review` per cycle, no
      can-it-fail check, no refactor rules. The comparison then says which
      of those instructions the model still needs.
      *The policy question.* The orchestrator's `tdd-implementation` row
      asks once per slice, after writing the entry and before the sandbox
      check, with three options and "not now": heavy (both candidates on
      `tdd-implementation`, the recommended default), lite (both on the
      lite skill), compare (candidate 1 heavy, candidate 2 lite). Under
      heavy and lite the read context stays the one variable between the
      candidates (H4); under compare the skill is the variable, so both
      get candidate 2's full-unit context and the C line's "wider read
      changed" clause becomes "discipline changed". Finalize builds with
      lite under lite and with the full skill under heavy and compare.
      The A line records the policy and each candidate's skill. The
      question is skipped only when the user's own message named a policy;
      a plain "go ahead" names none. The lite skill's description, the
      orchestrator's and the `tdd-coach` agent all say lite is reached
      only when a task names it (G1's pre-named-stage lesson, applied
      before it bites); `not-heavy-skill` graders check the other
      direction on the lite cases.
      *Cases.* Three lite twins of the tdd cases
      (`tdd-implementation-lite-cancel-hold`, `-named-fix`,
      `-cancel-hold-via-agent`), the prompt naming the lite skill, each
      grader marked floor or measurement in a comment at the top of the
      case's grader list. Floor is the contract: skill invoked first, the
      heavy skill not invoked, tests run for real and green last, no shell
      writes, inside the slice, design untouched, `map-query` consulted,
      the queue question escalated to its owners, the wording decided
      visibly, a report naming what was built and what the suite showed,
      the final reviewers run. Measurement is what heavy prescribes and
      lite leaves to the model: test-first order, a run after each test
      edit, RED then GREEN, the can-it-fail check, minimal GREEN,
      behaviour tests, the whole suite last; their rates are the finding,
      recorded in the bar like any other grader's. `reviews-each-cycle`
      is dropped (a plugin ritual nothing native would do) and the heavy
      report-shape grader is replaced by `reports-verification`.
      *The measurement.* G1 left the bars at the ceiling, so the
      comparison is the blind judge: `evals/tools/compare_arms.py` takes a
      heavy and a lite gate result kept with `--keep-scaffold`, renders
      each run's change set against the case's pristine scaffold with
      nothing naming the arm, judges every pair of runs in both orders
      with the plugin's implementation rubric, and keeps every reason in a
      `*.pairwise.json` next to the first result.
      *Runs (2026-10-18, `gate-20261018T181429-*`, six tdd cases at three
      runs, kept):* the three heavy cases held their bars (cancel-hold
      0.97 against 0.99: one run collapsed the loop into a single cycle
      and lost `test-run-after-each-test-edit` and `reviews-each-cycle`,
      inside tolerance; the other two 1.00). The lite cases: named-fix
      1.00 (15/15 in every run); cancel-hold 0.92 and the via-agent twin
      0.91, every floor grader 3/3 in both, the score lost entirely to
      the measurement graders. What the model did, read from the traces
      (`seq.py` in the session's scratch, the edit/run/skill sequence per
      run), with the one thing lite does tell it about the loop said
      first: told to build test-first and run for real, every lite run
      invoked the skill first, consulted `map-query`, wrote the test file
      before any code (8 of 9 runs saw it fail before the code existed;
      the ninth wrote test and code together; test-first is in the lite
      text, so the two test-before-code graders are floor, not
      measurement, as Sourcery pointed out), and then, unprompted,
      ran the real runner, finished on the whole suite green,
      kept GREEN to the design, tested behaviour through the public
      interface, escalated the queue question to `acceptance-criteria`
      and `architecture-design`, decided the wording visibly, and ran the
      four reviewers. What it never did unprompted: the per-test cycle.
      Every lite cancel-hold run wrote all its tests in one file, saw one
      RED, wrote all three code files, saw one GREEN
      (`test-run-after-each-test-edit` 0/6), where heavy ran four or five
      cycles; and only one run in six broke the implementation on purpose
      to see a test fail (`can-fail-check-in-trace` 0/6: the one run that
      did, the via-agent twin's run 2, "changed `remove` to match any
      hold, two tests failed, restored", then edited the test file again
      after the reviewers, which is the shape the grader cannot see; left
      as it is, the heavy case has the same grader). So the heavy skill's
      instructions the model still needs are exactly two: one test at a
      time with a run between, and the can-it-fail check. Everything else
      in the 292 lines, the model does on its own at Sonnet.
      *The blind judge (`compare_arms.py`, every pair, both orders,
      $0.55 a case):* cancel-hold **lite 9/9**, via-agent **lite 9/9**,
      named-fix lite 3, heavy 1, tie 3, split 2 (the code identical to
      the line, one extra assertion deciding the non-ties). Eighteen of
      eighteen on the slice case in both orders is not noise, and the
      reasons are the same every time: lite's tests cover more of the
      slice's behaviour through the public interface (cancelling the
      head so the next member becomes head, a title with no queue,
      cancelling twice, a hold on another title untouched: five or six
      tests to heavy's two or three for `CancelHold`, read from the kept
      trees), and heavy's adapter writes an empty array back for an
      unknown title and removes every hold of that member where lite's
      `findIndex`/`splice` removes one and leaves a miss untouched; one
      heavy run tested `CancelHold` against a hand-rolled fake whose
      `remove` returned a canned boolean, so its use-case test checked
      delegation. Heavy's one credit, a separate adapter test file, did
      not outweigh that. The cause is in the heavy text, not the judge:
      "list every scenario the current goal actually needs ... no
      defensive case nobody asked for" and "the minimum that passes"
      read, at Sonnet, as two or three scenarios and a filter, where the
      model's own judgment writes five and a splice. The per-cycle
      `test-quality-review` call did not catch the thinness, because it
      reviews the test just written, not the scenarios not written.
      *What this says for the plugin (recorded, not acted on; the user's
      call):* the two instructions worth keeping could move into the lite
      contract as two lines, and the Test List's "only what's needed now"
      clause is costing coverage the model would otherwise write; a
      heavy-vs-lite compare in a real quarantine run would say whether the
      reviewers in Grade see the same difference. One case, one model, one
      slice: the via-agent twin repeating it 9/9 is the only replication
      so far.
      *Second run (`gate-20261018T183555-*`, the evidence run with the
      bars in place):* lite cancel-hold 0.88 against 0.92, the via-agent
      twin 0.87 against 0.91, both inside tolerance, named-fix 1.00
      again; the measurement graders lost exactly as before (the
      per-test cycle 0/6, the can-it-fail check 0/6), and this time two
      floor graders lost runs under the agent path, which the first run
      had not shown: `final-review-runs` 1/3 (two delegated agents
      skipped the four reviewers and said so: "this was a small change
      and I only self-checked it, so that step is skipped, not passed";
      the same miss the heavy skill took on 2026-10-13, when it was
      fixed with the line about the one-line refactor that shipped a
      missed null check) and `map-query-before-implementation` 2/3 (one
      agent went straight to the test). Both are contract, so both are
      lite-skill text: the final-review section now carries the heavy
      skill's reason and says "small change, self-checked, reviewers
      skipped" is the step skipped however honestly reported, and the
      consult section says the `Skill` call comes before the first
      implementation file and a grep is not the consult. Two judge
      losses were the rubric being narrower than a correct output, G5's
      lesson again: `escalates-queue-question` failed "out of scope
      until it is specified" with `acceptance-criteria` named (the FAIL
      example "out of scope" was written for a decision, not a deferral;
      now says so, and a second owner named beside the skill does not
      fail), and `tests-check-behaviour` failed a file whose last test
      exercised the adapter's `remove` directly, true/false, through its
      public interface (now passes by name). Both rewordings applied to
      the heavy twins as well, `rejudge.py --criteria-from` 3/3 on each
      lost output, and the four cancel-hold cases re-run. Also from the
      orchestrator re-run: `orchestrator-route-implementation-prenamed`
      0.93, one judge loss on a log entry headed with the row's own
      words ("slice has a design doc, runtime-safety criteria filled,
      project has a stack, not yet implemented") instead of the
      template's "slice ready for implementation", the same shape the
      judge had passed in run 0; both route-implementation graders now
      say either heading is correct and "Routed to: quarantine flow" is
      the route whether or not the entry names the skill; 3/3 at 1.0 on
      the re-run. Every orchestrator run asked the policy question in
      text (heavy recommended, lite, compare, not now) and stopped.
      *Third run (the evidence run after the text and rubric edits; the
      one before it was voided by the session limit):* heavy cancel-hold
      1.00 and 1.00, lite cancel-hold 0.91, the via-agent twin 0.92,
      lite named-fix 1.00; the agent-path reviewers and the consult held
      3/3 after the text fix, the two measurement graders lost 0/6
      again, and one judge vote on `escalates-queue-question` was lost
      (2/3) under the reworded rubric. Bars for the three lite cases
      recorded from this run; evidence current for every case the branch
      reaches. Over three runs of three, the lite per-test cycle is 0/9
      and the can-it-fail check 1/9: the finding is stable.
      *Sourcery on PR #17, thirteen findings, nine taken, one in part,
      three declined:*
      - *Taken, `compare_arms.py` (two High, five Medium):* a result file
        is data and chose what ran and what was read — the case
        directory now has to be `evals/<name>/` in this repository and a
        kept run a `claude-eval-*` directory under the temp root the gate
        used, holding its trace; symlinks are listed as links and never
        read (the plugin judge's own rule); `--paired` matches run
        indices and names the unmatched; the record's default name
        carries a UTC stamp and an existing file is never overwritten;
        the record is written whole-or-nothing through a temp file and
        after every judged pair, so an interruption keeps what was
        judged; and the two results must be two arms of one slice
        (byte-identical `scaffold.sh`, identical prompts once the lite
        clause and the case's own name are removed), which the first
        version did not check and which the test of the check found
        wanting at once: the report path in each prompt names its case,
        so the brief now carries `<case>` for both. Re-run on the kept
        trees, paired: lite 3/3, the same verdict with a neutral brief.
      - *Taken in part, "the judge can identify each arm":* the brief
        half, above. The label half declined: the case names key the
        sides so the winner comes back by name, and the judge's prompt
        labels them `implementation_1` and `implementation_2`
        (`pairwise_judge.py`'s template); said so in the tool's docstring.
      - *Taken, "lite prompts test-first behaviour":* right. Lite says
        "write the tests first and the code to pass them", so test-first
        is told, not unprompted; the two test-before-code graders moved
        from measurement to floor in both cancel-hold lite cases, and
        the account above, the hand-off and the PR say "told only to
        build test-first and run for real". What stays unprompted is
        everything about how.
      - *Taken, "the policy choice is missing from the log":* the text
        now says the A line is written when step A runs, as every
        sub-entry of this row is, and the entry carries only the route
        until then; the mechanics were already that, the sentence read
        otherwise.
      - *Declined, "lite omits architecture constraints":* the three
        per-change checks (dependency direction, plain data across a
        boundary, the design's names) are craft the measurement exists
        to observe; the contract is "the design's boundaries, interface
        ownership and names are the structure you build inside", which
        lite keeps, and `inside-the-design-boundaries` held 9/9 with the
        Grade step's `architecture-review` behind it in real use.
      - *Declined, "mutation checks accept unrelated failures":* the
        regexes are the heavy cases' own, the fixture's suite is
        deterministic, and binding a fail count to an implementation
        edit from a trace needs a plant (G3 recorded right-reason RED as
        ungraded for that reason).
      - *Declined, "floor grader misses can pass the gate":* true of the
        gate's arithmetic (A5: one flip at three runs is over the
        tolerance, absorbed by the re-run), and a per-run hard floor
        would fail the gate on judge noise the suite records honestly
        (one `escalates-queue-question` vote in nine this round). The
        label says what a miss means, and reading the misses is what
        found the two agent-path text fixes; the gate's always-passing
        rule catches a floor that goes to 0/3.
      *Re-run after the round (the orchestrator wording and the two
      case comments):* nineteen cases 19/19 at bar, the seventeen
      orchestrator cases all at 1.0, lite cancel-hold 0.92 and its
      via-agent twin 0.92 (the per-test cycle and the can-it-fail check
      0/6 once more: 0/15 and 1/15 over the five runs of three now).
      *Augmented lite (2026-10-18 night, the user's decision after the
      finding).* The lite runs were test-first, not TDD, and not even
      verified test-first: every RED was the whole test file failing to
      import a module that did not exist yet, so no assertion ever ran
      red, and the can-fail check was skipped, so the broader tests the
      judge preferred had never been seen to catch anything. The user
      asked whether the verification could be had without heavy's two
      runs per test, and chose this: lite now asks for four things and
      leaves the loop alone — tests before the code; a stub so the RED
      run fails on the tests' own assertions, read for a test failing
      for the wrong reason; implement and run the whole suite green;
      break the implementation on purpose, see a test fail, restore,
      re-run. About four test runs to heavy's two per test. The skill's
      description, the orchestrator's option line, the README and
      PERSONAS now say "test-first with verification rather than TDD":
      the model cannot be made to do TDD proper at Sonnet without being
      told one test at a time, which is heavy's instruction and heavy's
      cost, and the user chose not to change heavy. The experiment this
      sets up is the one the user named: whether verified test-first is
      as good as TDD on the shipped code, heavy against augmented lite,
      judged blind. Two floor graders carry the verification on both
      cancel-hold lite cases: `red-on-assertions` (before the first green
      run, a "✖ <test name> (<n>ms)" item that is a test, not a
      `.test.ts` file; the trace keeps the runner's summary lines but not
      always the error text, so the item line is what is checked; tested
      against the twelve recorded cancel-hold traces, matching the heavy
      runs whose first RED was an assertion and none of the old lite
      runs) and `can-fail-check-in-trace`, moved from measurement.
      *First run (`gate-20261018T234559-*`):* the protocol held in every
      run. All six cancel-hold runs wrote stubs, then the tests, saw the
      tests fail on their assertions (five or six failures named by the
      runner), implemented, went green, broke the adapter on purpose
      (four to six failures), restored and went green again;
      `red-on-assertions` 6/6, `can-fail-check-in-trace` 6/6, and the
      named-fix runs did the break-and-restore too. The one miss was the
      order: every run wrote the three stub files before the test file,
      so the two test-before-code graders failed (0.88 and 0.87, flagged
      as regressed) — the text said "before the real code, give the
      tests something to import" and the model read it as stubs first.
      Step 1 now says tests before any code, stubs included, and step 2
      says after the tests. The seventeen orchestrator cases re-ran
      17/17 at 1.0 with the new option line.
      *Second run (`gate-20261018T235548-*`):* the order held in all six
      runs (test file, then the three stubs, then the RED on four to six
      assertions, implement, green, break, restore, green), both
      test-before-code graders back to 3/3, `red-on-assertions` and
      `can-fail-check-in-trace` 6/6 again. Two things left: the heavy
      case's `red-then-green-seen` went 0/6 and the gate flagged it as
      an always-passing grader lost, because it wants no edit between
      the test edit and the RED run and lite's stub step puts the stub
      writes exactly there by design — dropped from the two lite cases,
      with `red-on-assertions` as the RED check (the comment in each
      case says why); and `map-query-before-implementation` lost one run
      that consulted after the stubs, so the consult sentence now says
      "before the first file of code, stubs included".
      *Third run (`gate-20261018T235959-*`, kept; the bars and evidence
      come from it):* lite cancel-hold 0.96, the via-agent twin 0.96,
      named-fix 1.00; the only grader lost in any run is the per-test
      cycle, 0/6, which lite does not ask for. Every floor grader 3/3 in
      every case, the consult before the first stub in all six runs, the
      RED on assertions and the break-and-restore in all six, six or
      seven tests per run (the first lite wrote five or six, heavy two
      to four).
      *The experiment the user named, heavy against augmented lite,
      judged blind (`compare_arms.py`, every pair, both orders):*
      cancel-hold **augmented lite 9/9**, via-agent **9/9**, named-fix
      lite 2, tie 1, split 6, heavy 0 (identical code; one extra
      assertion on the error path deciding the non-ties either way).
      The reasons are the first comparison's reasons again: more of the
      slice's behaviour covered through the public interface (the head
      cancel, no queue, another title untouched, a double cancel, only
      the target removed from a queue of three) and the adapter that
      removes one hold and leaves a miss untouched, against heavy's two
      cases per layer and a `filter` that writes an empty array back.
      What the judge cannot see is the verification, which is the
      point of the augmentation: it reads the tests as written, and the
      two floor graders are what say the tests were seen red on their
      assertions and seen to catch a break. So on this slice, verified
      test-first at four runs is at least as good as TDD at twelve on
      everything the judge weighs, and better on tests; what TDD would
      still buy, the incremental shaping of the code by each test, this
      slice is too small to show. The `compare_arms.py` lite-clause
      regex also strips the via-agent prompt's "telling it to build
      with the lite skill" form, which the first form of the check
      refused (found when the via-agent pair returned no tally).
      *PR #17 was merged (`5e3e133`) before these commits were pushed,
      so the augmented lite is PR #18, branch `eval-g2b-augmented-lite`.*
      *Sourcery on PR #18, seven findings, six taken, one in part:*
      - *Taken, the three graders made exact (two lite cancel-hold
        cases):* `tests-before-any-code` is new (no `lending/` or
        `infra/` file written or edited before the first test file is
        written, so a stub before a test fails, which the two pair
        graders could not see); `map-query-before-any-code` replaces the
        tool-order grader (the consult before the first code file,
        stubs included, as the skill now says); `break-and-restore-in-
        trace` replaces the heavy case's `can-fail-check-in-trace` (a
        green run, a code edit with no failing run between, a failing
        run with no green between, a code edit with no green between,
        a green run with nothing failing after: an unrelated failure
        between two greens with no edit around it no longer passes).
      - *Taken, "a valid baseline run is rejected":* `red-on-assertions`
        now starts its span at the first test-file write instead of the
        start of the trace, so a green run of the existing suite before
        the tests are written is allowed.
      - *Taken in part, "assertion failures go unverified":* the
        grader cannot prove every new test failed on its assertion from
        a trace that keeps the runner's summary lines but not reliably
        the error text; what it can prove is that the failing item the
        runner names is a test, not a file, which is the module-not-
        found case the step exists to exclude. A test that passes
        against the stub is for the model to notice (step 2 says to read
        the output) and for the break check to catch. Left as the
        item-line check; the grader's comment says exactly what it
        proves and what it does not.
      - *Taken, "the agent still prescribes TDD":* right, and a real
        conflict for a lite build through `tdd-coach`: the agent's
        "follow it as written" summary named the Test List, each RED,
        minimal GREEN and the per-cycle review for every build. It now
        says what heavy is and what lite is, and that the skill wins.
      - *Taken, "an interrupted check leaves broken code":* as text, not
        isolation: whatever the broken run shows, the restore comes
        first and the report never follows an unrestored break. An
        isolated copy for a two-line break is more machinery than the
        step, and the heavy skill's same step has run without it.
      - *Found on the way, by the user's question "is this proper
        TDD":* no, and the first `red-on-assertions` pattern began with
        `\A`, which Node's engine (the eval's) reads as a literal `A`,
        so its 6/6 was for the wrong reason; every regex here is now
        tested under Node (`regexjs.sh` in the session's scratch),
        where the four graders pass the six final runs, fail the
        stub-first run on ordering and the first lite's runs on the RED
        and the break, and pass the one old run that did break and
        restore. Lesson for the suite: `^` and `$`, never `\A` or `\z`.
      *Re-run after the round (2026-10-19; the first attempt hit the
      session limit part way and was void):* eight cases 8/8 at bar —
      lite cancel-hold 0.95 and the via-agent twin 0.96 with the four
      exact graders 6/6 (the only losses the per-test cycle, 0/6 as
      ever, and one judge vote on `tests-check-behaviour`), lite
      named-fix 1.00, heavy cancel-hold 0.97 and its via-agent twin
      0.99 with the agent's new per-skill summary, the three
      test-quality-review cases at bar. Bars for the two lite
      cancel-hold cases re-recorded from this run; evidence current.
- [x] G3. Coverage items from the audit's section 8 that no case checks
      (stop-and-report paths, ADR hand-offs, consult calls).
      *Taken against the section 8 list, item by item:*
      - *Both requirements skills' stop-and-report path:*
        `security-requirements-payfine-phase2-stop` and
        `reliability-requirements-payfine-phase2-stop`, each a phase-2
        chain on the same frozen phase-1 history as its sibling, whose
        answer carries what the slice cannot satisfy as scoped (the
        merchant agreement requires an online receipt; a member blocked
        for fines must clear the block the same day from home through
        outages that have run most of a day). Four `last_message`
        graders each: reports the gap and stops (no forks, no criteria),
        lays out no scope menu, writes no criteria, does not design the
        missing capability. The hand-back fixture under
        `planning/pay-fine-handback/` is what a correct stop produces
        once saved; these two cases grade the turn that produces it.
        *First run (3 runs each, old skill text):* every run stopped,
        named the gap and hands it to product-slicer, but the reliability
        case listed the capabilities that could fill the gap in two runs
        of three ("it would be one of these: a second way to settle a
        fine...; a way to lift or defer the block") and once said, in
        the same breath, that it was not listing them; the security case
        did not. The rule ("don't lay out the ways the slice could grow")
        lived only in the instructions, with no shape for the stop
        report, so F's first lesson applies: both skills' output format
        now carries a stop-report template ("## Handed back to
        product-slicer — blocking": the gap, what it forces, one
        recommendation, the forks held by name) with "one
        recommendation, not a list" under it. *Second run, with the
        template:* six of six responses took the shape exactly, no forks
        presented, no criteria, no menu. The skill edit staled six
        frozen histories (both phase 2s, both phase 3s, both stops);
        re-frozen in the D1 loop: phase 1 at three runs with
        `--keep-scaffold` (3/3 each; security run 2 and reliability run
        1 chosen, the ones whose questions the phase-2 prompts answer
        most directly), phase 2 at three runs (3/3 each) and phase 3
        frozen from the resumed transcripts beside the clone's
        histories. The stop graders were then reworded against the
        judge's explanations (`rejudge.py --explain`, and
        `--criteria-from` to re-judge the recorded outputs under the new
        text): a preview of the decisions held back is a deferral, not
        the forks presented; stating the hand-back's two sides ("in this
        slice, or it can't ship until a slice provides it") is the
        hand-back, not a menu; a recommendation may name the capability
        it favours and a means the code already has, and a contrast
        that supports it names no second option; FAIL stays for a list
        of alternative mechanisms, for criteria written now, and for
        internals settled rather than held (the one reliability run that
        designed "an alternative adapter behind the `FinePayments` port
        with provider-neutral decline codes" still fails, rightly).
        `rejudge.py --criteria-from` parsed the case file with `ruby`,
        absent from the WSL clone; it now uses PyYAML when present.
      - *`code-review`'s mandated `why-comments` consult:*
        `consults-why-comments` on `code-review-catalog`,
        `code-review-fine-notices-pr` (a `tool_used` grader) and the
        via-agent twin (a trace regex, the form the tdd via-agent case
        proved for calls made inside a delegated agent). Not on
        `code-review-days-left-pr` or `-fines-report-pr`: their plants
        carry no comments, and the two latest runs that skipped the
        consult were exactly those two (15 runs read; the three
        comment-bearing cases consulted in 9 of 9).
      - *`design-system`'s reference path and review/evolve mode:*
        `design-system-payfine-reference` (the public site's stylesheet
        under `ui-plants/design-system-reference/` as the reference; one
        mock carrying its plum `#5B2A86` in its own markup, a
        confirmation asked, the system document not written before it,
        no candidates, no reference-or-generate question) and
        `design-system-payfine-review` (the fixture system copied to
        `ui-plants/design-system-review/` with two planted problems,
        `--muted` at `#9AA3AA` under a stale 6.01:1 claim and no focus
        state anywhere; its deliberate choices as traps; findings to a
        file, the system and sample untouched by a trace guard).
      - *`tdd-implementation`'s full suite after GREEN:* the proxy that
        is gradable from the trace, `final-run-is-the-whole-suite` on
        all three tdd cases: the last Bash test command is an `npm test`
        naming no `.test.ts` file, with no test command after it.
        Checked against the 69 recorded tdd traces: every run that ran
        at all passes; the twelve that fail are the 7.5 KB traces of
        runs the session limit emptied. Right-reason RED, REFACTOR, the
        Critical/High fix loop and the revert of a design edit stay
        ungraded: none has a trace signature that does not need a
        plant of its own.
      - *Already covered since the audit:* the orchestrator's log entry
        and save location (F1), not answering the routed skill's
        questions (every route case's final-message grader ends on
        those questions), `vertical-slicing`'s consult and sections
        (F), the `adr` worthiness test (F). *Left uncovered, with
        reason:* the requirements skills' ADR hand-off (no fork in the
        pay-fine fixture clears the ADR bar, so a grader would have
        nothing true to require); all five data exits (phase 3 grades
        two; the other three are not in the slice's path); the
        quarantine flow (G2's ground).
- [x] G4. From F: `orchestrator-backward-route` 0.95. One run in three
      routes correctly, cuts the slice, then narrates the whole round
      trip (requirements-002, design, security) and opens with
      requirements-refinement as what's next; the skill's step 3 forbids
      that narration in so many words. Decide whether the skill needs
      the rule restated where the backward step reports, or whether
      one run in three is the noise floor for a long inline routing.
      *Restated where the report is written.* Step 5's first bullet says
      "name what that next step would be", and for a backward route the
      model obeyed it by guessing the row re-inspection would land on;
      the prohibition sat forty lines earlier under step 3. Phase F's
      first lesson applied: step 5 now says that after a backward route
      the next step is always "return to step 2 and re-inspect", named
      and nothing past it. Reaches every orchestrator case (17).
- [x] G5. From F: three long-file review traps lose a run to the judge
      each pass with the explained judge passing the run
      (`reliability-review-alerts` burn-rate, 11k characters;
      `reliability-review-nightly` duplicate-fines, 16k;
      `code-review-fine-notices-pr` leaves-mocking, close call on
      wording). The CLI's own note says to prefer a regex on large
      artifacts; a findings-only excerpt file, or a shorter review
      format, would take the judge off the long text.
      *Read from the three failed runs' review text, each a different
      cause, none of them length alone:*
      - *alerts:* the run reported "Burn-rate alerts have no guard
        against low traffic or a confirmation window" at **Low**, a
        refinement that keeps both alerts; the rubric's PASS clause
        ("not noisy, duplicated, arbitrary or non-actionable") read
        against its own words ("noisy at low volume"). Reworded: a
        refinement that keeps both and adds to them passes at any
        severity; FAIL only for removing, demoting or replacing either.
      - *nightly:* the run's finding was the check-then-insert race
        plus an accurate second mechanism: `outstandingFor` excludes
        settled and waived fines, so a loan still open after its fine
        is paid is fined again (verified in
        `fines/assess-overdue-fine.ts` and the ledger query). The old
        rubric allowed the race and forbade "re-run double-fines",
        with nothing said about the settled-fine gap. Reworded: both
        mechanisms pass; FAIL only for a sequential re-run double-fining
        an outstanding fine with no mention of the check, overlap, or
        settled fines. Twin grader in `-via-agent` reworded alike.
      - *fine-notices:* two runs lost. One put "and the second doesn't
        exercise real code" in the heading of a ranked finding, a real
        boundary slip the rubric is right to fail; the other described
        the mock inside the duplicate-names finding and deferred the
        judgment to `test-quality-review` in the same breath, which the
        judge read as a ranked finding. Reworded: context inside the
        names finding and a deferring sentence pass; FAIL only when the
        finding's own complaint (heading, severity reasoning, fix) is
        the mocking. Twin grader in `-via-agent` reworded alike.
      So: rubrics, not excerpt files. All three were lesson 2 from F
      (the judge tripping on the rubric's wording), with the twist that
      in two of the three the rubric was also wrong about what a correct
      review may say.
- [x] G6. Runs and bars for G3–G5: every affected case at three runs,
      failures read, bars recorded, evidence current, hand-off updated.
      *2026-10-16/17, seven WSL batches, about 190 runs in all.*
      *Batch 1 (29 cases, 87 runs): 29/29 passed.* G5's three traps lost
      no run to their old cause: `reliability-review-alerts` 1.0 (bar was
      0.94), `-nightly` 0.97 (one run missed the fine-loop isolation
      finding, a real miss, not the trap), `code-review-fine-notices-pr`
      0.97 (one run again put "the second doesn't test the code under
      review" in a ranked finding's heading, the boundary slip the
      rubric is right to fail; recorded at 0.667 for that grader). G4:
      `orchestrator-backward-route` 3/3, bar back to 1.0; the sixteen
      other orchestrator cases 1.0 except `-route-scope-decision` 0.95
      (its log entry named the row and the artifact path; the judge
      failed it once, noise, bar left at 1.0). The consult grader passed
      9/9 on the three comment-bearing code-review cases; the tdd
      whole-suite grader 9/9. The design-system cases passed 3/3 each on
      their first run: the reference case wrote one mock carrying the
      plum, asked for confirmation and wrote no system document; the
      review case found the muted contrast (computing 2.4:1 against the
      document's 6.01:1) and the missing focus state, left the teal,
      the font, the radii and the no-shadow choice alone, and wrote
      nothing but the findings file. The two stop cases scored 0.58 and
      0.83, which led to the template change and the re-freeze recorded
      under G3, then 0.67 and 0.58 under the first rubric rewording,
      0.58 and 0.92 under the second, and 3/3 each under the terse
      scope rubric. *Lesson, paid for in four rounds:* on a one-word
      judge, a rubric that grows a clause per false failure gets noisier,
      not stricter; the version that held is the short one that says the
      two things that fail and lists what passes afterwards. Phase 3
      lost 3/3 on `decisions-all-approved` after the re-freeze because
      its pinned forks were the old history's (the grader's own note
      said to re-pin; the re-frozen phase 2 presents declines-and-abuse
      and error-monitoring forks where the old one had at-most-once
      charging and an attempt limit); re-pinned on both chains, 3/3.
      tdd bars moved to 0.99 and 0.97: `escalates-queue-question` lost a
      run in each cancel-hold case to reports that named both owning
      skills (judge noise, recorded honestly). Recording bars on the
      twenty changed or new cases staled six orchestrator cases whose
      runs invoke the requirements skills (the batch-1 runs predate the
      template edit); re-run last, 6/6 at 1.0. Final state:
      `eval_evidence.py --base origin/main` 39/39 affected cases ok,
      `history_stale.py` every chain current, 114 cases with bars.
      *Sourcery on PR #7, nine findings, six taken, two folded into those,
      one declined:*
      - *Taken, the tdd whole-suite grader (three findings):* the
        pattern matched command text only, so a final run that ended red
        passed (the separate `last-test-run-green` caught it, but the
        grader itself did not); `echo npm test` would have passed; a
        `--test-name-pattern` filter passed as the whole suite; and the
        fixture's own direct `node ... --test ... test/*.test.ts` form
        failed as "filtered" because the glob ends in `.test.ts`. The
        grader now requires a test command as a command word (start of
        the command or after `;`, `&&`, `||`), no named `.test.ts` file
        and no filter flag, that command's own output reaching `ℹ fail
        0` before any later test command, and no test command after it.
        Checked against eleven synthetic traces and the 78 recorded tdd
        traces: every modern run passes; the fails are the fifteen
        empty traces plus the four 2026-10-13 runs that predate phase B,
        three of which ended red ("green again" narrated without a run,
        the miss B fixed) and one that wrote tests through Bash heredocs
        inside the same command as its test run.
      - *Taken, `no-criteria-written` (both stop cases):* one or two
        Given/When/Then criteria without a heading passed; now at most
        one, quoted as an illustration, and two or more fail with or
        without a heading.
      - *Taken in part, the scope-menu grader (both stop cases):* a
        "rejected alternatives" list beside the recommendation was
        allowed; now a list of two or more mechanisms fails whether or
        not one is recommended, and only a contrast inside the
        recommendation's own sentence passes. `rejudge.py
        --criteria-from --votes 3` on the six recorded outputs: 17 of 18
        votes unchanged, one output (naming "a second payment route or a
        change to how the block is lifted" before recommending one) now
        fails two votes in three, which the skill's template ("naming
        two ways the gap could be filled is the menu") says it should.
      - *Taken, the reference-mock grader:* one brand colour was the
        whole proof of a matched reference; `mock-carries-reference-
        typeface` now also requires the stylesheet's serif face
        ("Source Serif 4" or Georgia) in the mock's markup. The three
        recorded runs all carry it.
      - *Taken, the orchestrator's two backward-route sentences:* step 3
        said "state only the single routed destination and why" while
        step 5 asked for what the owner produced and the offer to
        re-inspect; step 3 now lists the same four things.
      - *The re-run after those fixes (22 stale cases, 66 runs) found two
        more things.* (a) The tightened scope-menu rubric failed every
        security stop run because the judge read the "Held until scope
        is settled" bullets (the route fork "versus" its alternative) as
        a menu; the rubric now says that list names deferred forks, not
        gap options. Under that text the six recorded outputs re-judge
        9/9 on the security side; on the reliability side two outputs
        that say "a payment route that doesn't depend on Stripe, or a
        different rule for what a blocked member can do" fail 3/3, which
        the skill's template ("naming two ways the gap could be filled
        is the menu") says they should. So the template's "What it
        forces" line now says the missing capability is named by what it
        has to achieve, not by the ways it could be built; that edit
        staled both chains again, re-frozen once more. (b)
        `orchestrator-route-tech-bootstrap` fell to 0.76 with two runs
        of three stopping to ask whether the design's "existing port"
        and `PlaceHold` exist, since the repo is empty apart from
        `docs/`; the shared cancel-hold plant was written for the
        library app, where they do. Its scaffold now rewrites those
        words for the empty repo (new port, new adapter, the design's own
        constructor convention) and fails loudly if "existing" survives.
        The other two cases that copy the plant scaffold the app too, so
        the plant itself is unchanged.
      - *The second re-freeze surfaced the phase-1
        `does-not-ask-what-the-code-answers` graders again* (reliability
        3/3 lost, security 2/3), both explained PASS by the judge:
        reliability's runs asked who watches the error reporter's alerts
        (people, not code; the reporter named by path); security's asked
        how the browser collects the card, which the repository cannot
        answer because the portal's browser code is not in it, while the
        rubric's own FAIL example read "do card details reach our
        server?". Both rubrics now say so, the contradicting example is
        gone, and each names the people-and-process questions that pass.
        Re-judged under the new text: reliability 3/3, security 8/9 (the
        one dissent explained PASS). The tech-bootstrap case went 3/3
        with the patched plant. Final stale-set run: 13/14 at or above
        bar, with the security phase-1 case re-run after its rubric fix;
        one-flip losses on `orchestrator-route-design-system` (log
        grader) and `reliability-requirements-payfine-phase3`
        (double-submit criterion), noise, bars left at 1.0.
      - *Declined, "mock check misses actual file":* the brand regex
        accepts the plum in any written .html or .css rather than the
        file the reply names. A regex cannot read the reply's path, and
        the skill lets the pre-confirmation mock live anywhere; the
        typeface grader narrows the gap, and a mock styled from a linked
        stylesheet (the form one screen-design run used) must stay
        legal.

## H. The plugin fix order (agreed 2026-10-12; order chosen 2026-10-17: H first, H6 the first real run, then G1, then G2)

Skill changes, not eval changes: each edits `skills/orchestrator/SKILL.md`
(or `tdd-implementation`), so each re-runs the orchestrator cases
`affected_cases.py` lists (sixteen, 48 runs) as the regression check.
The quarantine flow itself has no case: it needs the `Agent` tool and up
to twelve reviewers, so these items are proven by reading and by the
first real execution (the hand-off says what to watch).

- [x] H1. Wire the validation gate into the orchestrator's Grade step.
      *2026-10-17, branch `plugin-fix-grade-gate`.* The script moved from
      `evals/tools/validation_gate.py` to
      `skills/orchestrator/scripts/validation_gate.py`: a skill can only
      reach a script that ships inside the plugin, and the skill body
      names it as `${CLAUDE_SKILL_DIR}/scripts/validation_gate.py`, which
      Claude Code substitutes with the skill's installed directory when
      the skill loads (the docs' "Available string substitutions"; the
      variable is not in the Bash tool's environment, only the body
      substitution works). Grade now runs the gate first, per candidate,
      against the candidate's worktree with `--base` the commit noted
      before Quarantine (the gate's default `HEAD` would miss a
      candidate's committed work), `--allow` the design doc's module
      directories plus the test directory and the report path,
      `--protect` the design doc and the slice, `--coverage` on Node; a
      failing candidate gets no map diff and no reviewers, its checks go
      in the log's B sub-entry, Combine still reads its code; both
      failing still reaches Combine with the gate reports as the
      findings; the orchestrator may not fix, relaunch or widen `--allow`.
      Finalize runs the same gate on the real tree before the map is
      persisted, hands a failure back to the same instance once as a
      named fix, and on a second failure stops and reports the slice as
      not implemented. The log template's B and D lines carry the
      verdicts. `PERSONAS.md` and the README say so.
      *Run:* sixteen orchestrator cases at three runs, 16/16 at bar;
      `-route-problem-framing` 0.95, one run's log entry gave the target
      directory as the artifact where the skill had only asked its
      questions and written nothing yet (judge 2-1 FAIL), the same
      judgment-call noise F recorded, bar left at 1.0. Evidence recorded
      for all sixteen.
      *Also:* `wsl-gate.sh` died with `sed: can't read` on the moved
      file, because `git ls-files -m` lists a deleted path too; the CRLF
      strip now skips anything that is not a file.
      *Not done, deliberately:* no `allowed-tools` Bash rule in the
      skill's frontmatter for the gate command. The docs say such a rule
      lets it run without a prompt, but how the pattern matches a
      substituted path (and a quoted one on Windows) is undocumented;
      try it once in a real session before relying on it.
      *Sourcery on PR #9, fourteen findings, eleven taken, one taken in
      part, two declined:*
      - *Taken, the real one (two findings, "existing changes fail the
        gate" and "log entry fails final gate"):* the Finalize gate on
        the real tree diffed against the commit noted in Quarantine, so
        every uncommitted planning document and the log's own new entry
        counted as the build's changes; in a dogfood project where the
        docs are never committed, Finalize would have failed every time.
        The gate now has `--record-baseline FILE` (the current commit
        plus a hash of every file already modified or untracked) and
        `--baseline FILE` (diff against that commit, ignore those files
        while their content is unchanged); the skill records it under
        `.git/` before Quarantine and passes it in Grade and Finalize,
        and Finalize's `--allow` adds the log file, which keeps changing
        as the sub-entries are written. Found on the way: `--protect`
        failed a file that was merely absent, and an uncommitted design
        doc is absent from every candidate's worktree; a protected file
        now fails only when it is in the change set, which still covers
        a deleted tracked file and a baseline-recorded file that is gone
        from the real tree (the baseline records its project path so a
        worktree is not blamed for files that were never there).
      - *Taken, script:* the change set is computed after the test
        command runs, so a test that edits the tree is caught; `git diff
        --no-renames` lists both sides of a rename, so a file moved into
        an allowed directory still shows its old path as outside; an
        `--allow` entry without a trailing `/` is an exact file, so
        `report.md.bak` no longer passes as `report.md`; an empty change
        set is a failed `changes` check; `--timeout` (600 s) turns a hung
        suite into a failed one; a red suite prints its last thirty
        lines; `.tsx`/`.jsx` count as source; a test file is anything
        under a `test`, `tests`, `__tests__` or `spec` directory or named
        `*.test.*`/`*.spec.*`, not only root `test/` and `.test.ts`.
      - *Taken, skill text:* every path in the gate commands is quoted;
        Finalize names `--coverage` among the flags it reuses.
      - *Taken in part, "failed changes remain in tree":* the finalized
        build that fails twice stays in the working tree, now said
        explicitly with its files named in the report; reverting it is
        the user's call, the same rule that keeps the candidate branches.
      - *Declined, "candidate tests execute unsandboxed code":* that is
        H5, and the gate adds no exposure the candidate's own test runs
        in Quarantine did not already have.
      - *Declined, the ignored-files half of "untracked changes evade
        scope":* gitignored files are build output (`node_modules`,
        coverage directories); counting them would fail every build.
        The rename half was taken (above).
      Thirteen scratch scenarios on a throwaway Node repo exercise each
      check; no eval runs the gate.
      *Runs after the Sourcery round:* the sixteen cases passed 16/16
      on the reworded skill, but the script's last two edits landed
      after that run started and staled them all (the script sits under
      the skill directory, so the evidence hash covers it). The re-run
      got five cases through (all at 1.0, `-backward-route` 0.95, one
      judge flip) before the WSL session limit cut it. The eleven
      re-ran after the reset: ten at 1.0, `-route-user-story` 0.81 on
      two different misses in one batch — one run logged the artifact
      as "to be determined by the skill" instead of a path (the skill
      had then asked its filing questions, correctly), and one run never
      invoked the skill, asking instead whether the story was already
      filed elsewhere (step 2's "take the user's word" read as a
      question to ask first) and narrating every later stage. The case
      had passed 3/3 twice earlier the same day on this branch and
      passed 3/3 again on the re-run, so 1 miss in 12 runs: noise,
      recorded; bar left at 1.0. If the non-invoking shape recurs, it is
      a step 2 wording question (the inspection says to take the user's
      word, which the orchestrator can read as an invitation to ask),
      not a quarantine-flow one. Evidence current for all sixteen.
- [x] H2. Promote `tools/pairwise_judge.py` to the arbiter inside
      Combine: blind, both orders, reasons kept, the orchestrator's own
      call made with the judge's verdict in hand rather than instead of
      it. The script lives under `evals/tools/`; like H1, it has to move
      into the plugin to be reachable from the skill.
      *2026-10-17, branch `plugin-fix-combine-judge`.* The judge now
      lives at `skills/orchestrator/scripts/pairwise_judge.py`, reached
      from the skill body as `${CLAUDE_SKILL_DIR}/scripts/pairwise_judge.py`.
      What it does: takes the two candidate worktrees, the gate's
      baseline file and the brief (`--task`: the design doc, the slice,
      each criteria document the candidates were given); computes each
      candidate's change set exactly as the gate does (it imports the
      gate's helpers, so the two can never disagree about what a
      candidate changed), leaves out `--exclude` paths (the candidate's
      own report: a self-description is not the code) and binary files,
      sorts lock files last and caps each view at `--max-bytes` so a
      dependency lock is what gets truncated first (the judge is told
      what was cut); shows a tool-less `claude -p` judge the brief and
      both views labelled only "implementation 1/2" (no path, branch,
      gate verdict or finding), in both presentation orders; keeps each
      order's reasoning in a new `.git/kad-pairwise-<timestamp>.json` next to the
      baseline; prints both reasonings and one last line, `pairwise
      judge: candidate 1 | candidate 2 | tie | split`, exit 2 and `NO
      VERDICT` when `claude` is missing, times out, answers twice with
      no verdict, or a change set cannot be computed. The rubric weighs,
      in order: behaviour against the brief and nothing the brief did
      not ask for; tests that exercise the criteria through the public
      interface and could fail; module boundaries and dependency
      direction as the brief states them; clarity, not brevity. The
      judge runs even when a candidate failed the gate (what it got
      right is information; the judge does not know which failed).
      *Skill text:* Combine is now "judge first, blind; then read; then
      decide with the verdict in hand". The call follows the verdict in
      a line or names which of the judge's reasons it sets aside and
      why; a tie or split leaves the call to the orchestrator with the
      same obligation; a gate failure outranks the judge; no verdict
      means one retry, then the call without it, said in the log; the
      orchestrator may not stage a "blind" comparison of its own in its
      place. The log template's C line carries the verdict, the reasons
      path and "follows / departs from the judge: why"; step 5's report
      names both. `PERSONAS.md` and both READMEs say so.
      *The eval tool stays:* `evals/tools/pairwise_judge.py` keeps its
      with/without results-dir mode (G2 needs it) as a wrapper that
      imports `compare()` from the plugin script and supplies the review
      rubric; `pairwise.json` keeps its shape (`with_first` /
      `without_first`, winners by arm).
      *Proven by running, not by an eval:* on a throwaway Node repo
      (committed `placeHold`, an uncommitted design doc for `cancelHold`,
      baseline recorded, two worktrees: one honest implementation with
      three behaviour tests, one that skips the ownership check, adds an
      unasked notification and asserts only truthiness) the judge picked
      the honest candidate in both orders with reasons that named each
      miss, at $0.04 on Sonnet; the uncommitted design doc appeared in
      neither view (the baseline excluded it); `--exclude` dropped the
      report, a binary file was listed but not shown, a 150-byte cap
      truncated and said so; one candidate, no task, no `--out` without
      a baseline, `claude` off PATH and an unknown base each failed with
      their own message and no output file. The eval wrapper ran on a
      hand-made two-arm results file and wrote the old `pairwise.json`
      shape. The quarantine flow itself still has no eval case.
      *Run:* sixteen orchestrator cases at three runs, 16/16 at bar,
      fifteen at 1.0; `-route-scope-decision` 0.95, one run's log entry
      gave its artifact as "`docs/pay-fine/scope-map-001.md` if a map is
      warranted; otherwise none" and then appended an "Outcome: no scope
      map written" line to the same entry (judge 3-0 FAIL on
      `log-names-row-and-artifact`). The same grader on the same case
      lost one run in three under G4 with a cleaner entry, so this is
      the known judgment-call noise on a conditional artifact line, not
      a Combine-text effect (the case never reaches Combine); bar left
      at 1.0. If it recurs, the fix is in the skill's step 4 wording for
      a routed step that may produce no artifact, not here. Evidence
      recorded for all sixteen.
      *Sourcery on PR #10, nine findings, six taken, one in part, two
      declined:*
      - *Taken, symlinks (its one Critical):* a changed symlink was
        followed, so a link a candidate planted at a file outside the
        worktree would have put that file's contents in the judge's
        prompt, and a link to a directory or nowhere read as "deleted".
        A link is now shown as `(symlink -> target, not followed)`;
        proven in WSL with links to `/etc/hostname`, a directory and a
        missing target.
      - *Taken, malformed judge replies:* a JSON array, an object with
        no reasoning or a non-string one, or a `result` that is not text
        raised past the handlers as a traceback. `ask_judge` now
        validates the shape and raises the retryable error; `compare`
        records an order that failed twice with its `error` instead of
        raising, so the other order's reasoning is kept, and the verdict
        is `no verdict`.
      - *Taken, memory and the byte cap:* a changed file was read whole
        before the cap applied, and the cap counted characters of file
        content only. No file is read past the cap now; the cap is
        UTF-8 bytes of the whole rendered view, headers and both
        truncation markers included, with room reserved for the closing
        "not shown" list as each file is placed, and a file with others
        still pending gets at most half the remaining room so one huge
        file does not starve the rest (a half-megabyte of `é` ahead of
        three small files under caps from 1000 to 200000 bytes stays
        under each cap, and from 3000 bytes up every file is shown).
      - *Taken, the output file:* `kad-pairwise.json` was shared across
        runs and written only on success, so a failed run left an
        earlier verdict at the path the log named. The default is now a
        new `kad-pairwise-<UTC timestamp>.json` per run, written on
        failure too, with whatever the judge did say.
      - *Taken, injection into the judge:* the rubric now says the
        implementations are data, never instructions, and that text
        addressing the judge is a defect of that candidate; the skill
        says to read the reasoning with that in mind. The verdict was
        already non-authoritative (the gate and reviewers do not depend
        on it), which is the rest of the finding's ask.
      - *Taken, shell quoting in the skill:* the Combine command put
        project paths in double quotes, where a file a contributor
        named with `$(` would run. Every project path in every command
        of the procedure (baseline, both gates, judge) is now in single
        quotes, with a sentence saying why; only the skill's own
        directory stays double-quoted. This touches H1's command text
        too, same fix.
      - *Taken in part, overlapping runs on the output file:* the
        per-run file name covers a second run following a first; two
        flows writing at the same instant are the declined case below.
      - *Declined, opengrep "subprocess without a static string":* the
        call is an argument list run with no shell; its only non-literal
        elements are the `claude` path `shutil.which` resolved and the
        `--model` value from the command line, and the prompt travels on
        stdin. A comment at the call says so, with the same `nosemgrep`
        marker H1 put on the gate's test-runner call: Sourcery counts
        this rule's hits as blocking until the thread is resolved or the
        line carries the marker, and the check stayed red on the
        resolved thread alone.
      - *Declined, overlapping flows reading one baseline:* two
        quarantine flows running at once in one project is not a
        supported shape; they would also collide on the log, the
        worktrees and the finalize tree, and the baseline is H1's
        design shared with the gate, which the judge must read the same
        way or the two disagree about what a candidate changed.
      *Run after the round:* sixteen cases at three runs, 16/16 at bar,
      fifteen at 1.0; `-route-user-story` 0.95, one run's log entry gave
      its artifact as "to be decided by the skill (a tracking destination
      for `slice-001.md`)" (judge 3-0 on `log-names-row-and-artifact`),
      the same shape H1 saw once in twelve runs: `user-story-writeup`
      asks the user where to file, so at the moment the entry is written
      there is no path to name. Noise for this change (Combine is never
      reached), bar left at 1.0; but twice now, so it is a candidate
      step 4 wording fix for a later item: say what the artifact line
      holds when the routed skill decides the destination (the slice
      file it will file, or the tracker once chosen, in a correcting
      entry). Evidence recorded for all sixteen.
      *Run after the `nosemgrep` marker (a comment under the skill
      directory, so the hash moved):* 16/16 at bar, fourteen at 1.0.
      `-route-implementation` 0.94: one run's entry routed to the
      quarantine flow and wrote "A. Quarantine: not started — awaiting
      user go-ahead" with no **Artifact** line at all (judge 3-0 on
      `routes-to-tdd-implementation`; the template's "see sub-entries
      below" was the line to write); 3/3 in the two earlier runs today.
      `-route-scope-decision` 0.95: the same hedged artifact line as
      this afternoon ("`scope-map-001.md` if a scope map is warranted;
      otherwise none", then an Outcome line), judge 3-0. Both bars left
      at 1.0; neither reaches Combine. That makes three misses today on
      one theme — the artifact line when the routed step may write
      nothing, or asks first, or decides the destination itself — so the
      step 4 wording fix flagged above is now the first thing to do when
      an orchestrator item next opens the skill: name what the line
      holds in each of those three cases, and that the line is never
      omitted or made conditional. Evidence recorded for all sixteen.
- [x] H3. Full reviewer pass on the finalized build, not only the
      targeted re-grade of the combine brief's findings. *Carry with it
      the step 4 artifact-line fix recorded at the end of H2 (three
      one-run misses on 2026-10-17, one theme); it opens the same skill
      and the same sixteen cases re-run either way.*
      *2026-10-17, branch `plugin-fix-full-regrade`.* Step E of the
      quarantine flow is now the full pass: the finalized build is a
      fresh implementation whose instance skipped its own final review
      because the task said `orchestrator` reviews it, so until now the
      only review the shipped code got was the targeted check of the
      combine brief's findings, raised against candidates that no longer
      exist. E now runs every reviewer Grade ran (same list, same rule
      for which apply), in parallel as async `Agent` calls against the
      real working tree, each handed the files the build changed and
      the map diff D's real `map-update` produced; then checks the
      combine brief's findings pass/fail as before. Critical and High
      findings are handed back to the same instance once, as named
      fixes; then, in order, the gate runs again on the fix (D's command
      plus `--allow` for the persisted map D wrote after its gate ran),
      `map-update` runs for real again so the persisted map is the map of
      the build that ships, and every applicable reviewer re-runs on the
      files the fix touched with the refreshed diff, the brief's findings
      re-checked with them. A gate failure after the fix ends the
      procedure as D's second failure does; a Critical or High still standing after the one round is
      reported as outstanding for the user, never fixed by the
      orchestrator and never a second round; Medium and Low are
      reported, not acted on, as in the tdd skill's own final review. The
      log template's E line carries the reviewers run, the finding
      counts, the brief's pass/fail, the handed-back round with its gate
      result, and whether the map was re-run; step 5's report names each
      reviewer's result and anything still standing; the terminal-row
      wording says the slice was graded in Grade and Re-grade. The gate
      script now lists the changed files on its `changes` line and in
      its `--json` report (it only counted them), since E hands the
      reviewers exactly that list. `PERSONAS.md` and the README say so.
      *The step 4 artifact-line fix, carried:* the log template is
      followed by the rule that the **Artifact** line is in every entry
      as a plain path, never omitted and never conditional, with the
      three cases the misses were: the quarantine row writes `see
      sub-entries below` even before the flow starts; a skill that may
      write nothing gets the path the artifact takes if written, stated
      flatly, no outcome appended; a skill that chooses its destination
      gets the target directory, with a correcting entry once it has
      filed, and "to be decided by the skill" is named as not a location.
      *First run, a real regression from the wording:* 14/16.
      `-route-problem-framing` and `-route-slicing` both 0.86, their
      `log-names-row-and-artifact` grader 3/3 FAIL with `docs/pay-fine/`
      as the artifact; across the batch nearly every row had written the
      bare target directory where the previous two batches named a file
      (`problem-framing.md`, `slice-001.md`, `technology-bootstrap-001.md`)
      with a parenthetical when unsure. The first wording's third case
      ("the target directory, as the location the step works in") was
      read as the rule for every row. Reworded: the line holds one
      file path under the target directory by the persona's convention,
      a parenthetical where the skill may name it differently, never the
      bare directory, with the three cases under that; the user-story
      case names the path a locally filed story takes, and a correcting
      entry is a new entry, never an edit (one backward-route run had
      edited its own entry's line after the skill ran). Same batch:
      `-route-implementation` 0.94, one judge 2-1 FAIL on a correct
      "see sub-entries below" line; `-route-design` 0.95, one flip.
      *Run, on the reworded rule:* sixteen cases at three runs, 16/16 at
      bar, all sixteen at 1.0 (`results/gate-20261017T182031-*`). Every
      entry in the batch named a file (`problem-framing.md`,
      `scope-map-001.md`, `slice-001.md`, `requirements-002.md`,
      `user-story-001.md` "(the skill may file it elsewhere)",
      `visual-ux/screen-design-001.md`, `technology-bootstrap-001.md`),
      the quarantine row "see sub-entries below" 3/3 where the previous
      batch had lost a judge vote on it. One backward-route run appended
      an "Outcome (correction to Artifact line)" paragraph to its own
      entry rather than writing a new one; the grader passed it and the
      rule already says a correction is a new entry, so noted, not
      acted on. Evidence recorded for all sixteen.
      *Sourcery on PR #11:* a first review approved with no findings and
      was dismissed by a second, seven findings, all seven taken:
      - *Taken, the real one (High, "valid fixes fail the gate"):* D's
        real `map-update` writes the persisted map after D's gate ran,
        so the post-fix gate with D's command unchanged would have failed
        every fix on scope, the map being a change outside the slice.
        The post-fix gate adds `--allow` for the map's path, the same
        treatment Finalize's command gives this log.
      - *Taken, "final build skips all review":* "every reviewer Grade
        ran" is empty when both candidates failed the gate. E now names
        the set by Grade's rule (the five always, accessibility if
        UI-touching), whether or not Grade got to run them.
      - *Taken, "architecture review uses stale map context":* the
        post-fix order is now gate, then `map-update` for real, then the
        reviewers with the refreshed diff; the "if the fix changed the
        build" condition on the map re-run is gone, a fix is a change.
      - *Taken, "some reviewers miss the shipped fix":* every applicable
        reviewer re-runs on the files the fix touched, not only the
        raising ones. This is the tdd skill's own rule for a handed-back
        fix (step 5 of that path: all four, however small, after a
        one-line refactor shipped a missed null check), which the E
        instance skips because the orchestrator grades it; E's first
        wording had copied the narrower in-loop rule instead.
      - *Taken, "brief finding can regress":* the combine brief's
        findings are checked again after the fix; the E line carries the
        post-fix result.
      - *Taken, "reviewers receive the process log":* the files handed
        to the reviewers are the gate's list minus this log and the
        persisted map, the flow's own writes; the map reaches them as
        the diff.
      - *Taken, "comma paths become ambiguous":* the gate's `changes`
        line prints the file list as JSON.
      *Run after the round:* sixteen cases at three runs, 16/16 at bar, all sixteen at 1.0 (`results/gate-20261017T224145-*`); a first attempt right after the edits lost every run to the session limit (resets on the hour it names, no evidence written). Evidence recorded for all sixteen.
- [x] H4. Diversify the two candidates' inputs (both got the identical
      task). *2026-10-17, branch `plugin-fix-diversify-inputs`.* The
      2026-10-12 direction named the shape: run one candidate with
      slice-only context and one with full-unit context, so the two are
      not correlated copies, and so the batching question (how much of
      the unit an implementer should see) is answered by the flow's own
      judge over real slices rather than decided up front. Step A now
      gives both instances the same task (build this slice from its
      design doc and criteria, save output where the orchestrator says,
      `orchestrator` reviews it, nothing about quarantine) and differs
      only in read context: candidate 1 reads the slice's documents
      alone; candidate 2 also reads the unit — its Active requirements
      document, every slice file cut for the unit, every design doc and
      screen-design artifact for any of its slices — each named by path
      for the instance to read, with one line that they are reference
      material and no instruction to it. Both tasks carry, word for
      word, the line that the deliverable is this slice alone with
      nothing built or prepared for beyond what its own design names.
      The assignment is fixed (the context always goes to candidate 2)
      so the reading across slices is of one variable, and the log's A
      line records every path candidate 2 was given.
      The judge's `--task` stays the slice documents both were given to
      deliver, not the unit context, which neither had to build. The
      combine brief gains one line, what candidate 2's wider read changed
      if anything (a port shaped for a later slice, a rule taken from the
      requirements document instead of escalated, a reuse the map showed,
      or nothing a reader could tell apart), kept or set aside; the C
      line and the step 5 report carry it, and the skill says that
      having read more is not itself a reason to build from candidate 2.
      The finalize instance gets the brief plus the inputs as candidate 2
      received them, since the brief may lean on how the slice fits the
      unit. `PERSONAS.md` says so.
      *Not touched, deliberately:* `tdd-implementation` (it reads what
      it is handed by path and escalates what the design leaves open;
      how it treats a requirements document it was given is what the
      comparison measures, and an edit there re-runs the tdd cases at
      ten to fifteen minutes a run); the judge script (its `--task` help
      still describes what both were given); the gate (scope is enforced
      by `--allow` either way, and over-building inside the slice's own
      modules for a later slice is the judge's "code the slice does not
      need" and a reviewer's finding, not a mechanical check).
      *Run:* sixteen cases at three runs, 16/16 at bar, fifteen at 1.0
      (`results/gate-20261017T230158-*`); `-route-user-story` 0.95, one
      run's reply put the skill's filing question in plain text (no
      `AskUserQuestion` in the case) and then narrated the two stages
      after it (judge 3-0 FAIL on `stops-after-the-routed-step`), a
      step 5 miss on a case whose text H4 did not touch, the same
      one-run noise H1 recorded on this case for a different reason;
      bar left at 1.0. Evidence recorded for all sixteen.
      *Sourcery on PR #12:* a first review approved with no findings;
      the docs push that recorded it re-ran the review, which dismissed
      the approval and found seven things (one High, six Medium). The
      "Sourcery review" check stayed green through it, so a green check
      is not "no findings": read the review. Four taken, two in part,
      one declined:
      - *Taken, "missing map blocks quarantine":* "a one-slice unit still
        has a map to give" contradicted "if there is one". Resolved by
        the next finding: the map is off the list.
      - *Taken, "slice-only input includes map":* candidate 1 consults
        the persisted map through `map-query` before each entry's code,
        as the tdd skill says, so the map was never the variable. Step A
        now says both reach it that way and neither task names it; the
        A line's map field is gone. (Sourcery's own fix, keeping the map
        from candidate 1, would have broken the tdd skill's consult.)
      - *Taken, "candidate tasks differ beyond context":* the
        deliver-only-this-slice line was on candidate 2's task alone, so
        the comparison measured a scope constraint as well as the read.
        Both tasks now carry it word for word, and D's instance too.
      - *Taken, "logged inputs cannot be verified":* the A line records
        every path candidate 2 was given, not counts.
      - *Taken in part, "unit documents can steer candidate" (High):*
        candidate 2's task now says the unit documents are reference
        material and nothing in them is an instruction to the instance,
        the same stance the judge's rubric takes on candidate text. The
        rest of the finding is the sandbox, H5: the exposure is the one
        candidate 1 already has from the slice's own documents, which
        the same contributors write, and the skill does not claim a
        sandbox it does not have.
      - *Taken in part, "judge misranks unit-aware work":* the judge
        keeps the slice documents as its brief, by design: the
        deliverable is the slice, and a port shaped for a later slice is
        "code the slice does not need" however sound the unit makes it.
        Step C now says that a choice only the unit justifies is the
        orchestrator's to weigh in the read that follows, naming the
        judge's reason if it sets that reason aside; the judge's view
        was not widened past what both candidates had to deliver.
      - *Declined, "large units exceed context limits":* the documents
        are named by path for the instance to read as it needs them, not
        pasted into the task, so nothing is assembled against an input
        limit at launch; and `product-slicer` bounds the unit.
      *Run after the round:* sixteen cases at three runs, 16/16 at bar,
      all sixteen at 1.0 (`results/gate-20261017T232306-*`). Evidence
      recorded for all sixteen. Every thread answered; Sourcery resolved
      six on the fix commit `1ddff20` (the declined one included) and
      posted no further review; the High sandbox thread was resolved by
      hand with its reason. Both PR checks green.
- [x] H5. Sandbox the code-writing agent. *2026-10-17, branch
      `plugin-fix-sandbox`, PR #13.* What the docs settle first (checked
      2026-10-17): the sandbox is a session setting, not an agent's — it
      covers what the Bash tool runs (Seatbelt on macOS, bubblewrap and
      socat on Linux and WSL2; native Windows runs every command
      unsandboxed), it lets a command read the whole machine unless
      `sandbox.filesystem.denyRead` names the path, and the Read tool runs
      outside it; a plugin cannot ship `sandbox` or `permissions` settings
      (a plugin's settings carry two unrelated keys), and a plugin-shipped
      agent's `permissionMode` and `hooks` are ignored, its `tools` and
      `isolation` honoured; `isolation: "worktree"` blocks edits and
      commands aimed at the main checkout but not reads or network. So the
      plugin can check and refuse, not enforce. The shape, like H1 to H3:
      `skills/orchestrator/scripts/sandbox_check.py --project <root>`, run
      inline by the orchestrator before anything is launched. It runs
      inside the session's own Bash sandbox, so five of its seven checks
      probe the fence instead of reading a file: not native Windows; a
      write to the home directory refused; a direct TCP connection out
      refused (the sandbox leaves no route; allowed domains go through its
      proxy); each credential path that exists on the machine (`~/.ssh`,
      `~/.aws`, `~/.gnupg`, `~/.config/gh`, `~/.npmrc`, `~/.netrc`,
      `~/.git-credentials`, `~/.docker/config.json`,
      `~/.claude/.credentials.json`; `--secret` adds) unreadable from the
      shell; each covered by a `Read(...)` rule in `permissions.deny` of
      the merged settings files (user, project, local, managed), for the
      Read tool every candidate holds. The two it has to read from the
      settings are the escape hatches no probe sees before they are used
      — `sandbox.enabled`, `allowUnsandboxedCommands: false`,
      `failIfUnavailable: true`, `excludedCommands: []` — and the
      project's `.worktreeinclude`, which would copy a gitignored `.env`
      into every candidate's worktree. Last line `sandbox check: PASS |
      FAIL`, exit 0/1.
      *Skill text:* step A runs it before the baseline; on `FAIL` nothing
      is launched, the row's entry carries the failing checks on its A
      line, step 5 reports what to change (the README's new "Running the
      quarantine flow" section has the settings block) and the flow stops;
      no `dangerouslyDisableSandbox`, no narrowing the list, no editing
      settings. Step D runs it again before the finalize instance writes
      into the real tree, a `FAIL` ending the procedure like a second
      gate failure. The log template's A and D lines carry the result and
      the network allowlist. `PERSONAS.md` and the README say so.
      *Not touched, deliberately:* `agents/tdd-coach/AGENT.md` — its
      `tools` list is already an allowlist (no WebFetch, WebSearch or
      Agent), `permissionMode` would be ignored on a plugin agent, and an
      edit there re-runs the tdd cases at ten to fifteen minutes a run;
      and no PreToolUse hook in `hooks/hooks.json` fencing the Read tool
      by `agent_type`: it would be a second mechanism for what the deny
      rules already cover, unprovable by any eval (plugin hooks do not
      load in the eval sandbox), and H6 is the place to find out whether
      it is needed.
      *Proven by running, not by an eval:* in WSL2, a headless `claude -p`
      with the README's settings block ran the script through its Bash
      tool: all seven checks PASS (write "Read-only file system", network
      "Network is unreachable", the credentials file unreadable from the
      shell), and a second session asked to `Read` the credentials file
      was refused by the deny rule. The same script unsandboxed, on
      Windows and in WSL, fails platform (Windows), write, network and
      shell-secrets with the paths named; with the credentials entries
      removed from the settings the sandboxed run fails shell-secrets and
      read-secrets and nothing else, so the shell probe measures the
      `denyRead` entry and not the sandbox itself. `claude -p` needs its
      prompt on stdin (`< prompt.txt`) when `--allowedTools` is on the
      line, since that flag is variadic and swallows a trailing prompt.
      *Run:* sixteen orchestrator cases at three runs, 16/16 at bar, all
      sixteen at 1.0 on the first run
      (`results/gate-20261017T235049-*`). Evidence recorded for all
      sixteen.
      *Sourcery on PR #13:* the reviewer's guide came first and the
      review with sixteen findings (four Critical, ten High, one Medium,
      one Low) minutes after the user had merged on the guide alone, so
      the round is PR #14, branch `plugin-fix-sandbox-review`. Eleven taken, three
      in part, two declined; and one thing the user asked for in the same
      breath, that the setup be wired in so it works without hand-editing
      a settings file:
      - *Taken, the user's ask:* `--write-settings FILE` merges the
        required sandbox and deny entries into a settings file (the
        session's `~/.claude/settings.json`), keeps everything else, prints
        each change, and runs the checks again in the same call. Step A
        says: on a `FAIL` of the settings-shaped lines, ask the user once
        with `AskUserQuestion`, run with `--write-settings` on yes, continue
        on `PASS`; if the probe lines still fail, the live session predates
        the setting, so report a restart and stop. Never without the
        question, never into a project's `.claude/`.
      - *Taken, "agents run after sandbox changes" (Critical):* the check
        runs before every launch — A, B's reviewers, D, E's reviewers — and
        a later `FAIL` ends the procedure like a second gate failure, with
        no settings written after A. The B and E template lines carry it.
      - *Taken, "new credentials escape the preflight" (Critical):* every
        secret path, present or not, must be in `denyRead` and covered by a
        `Read(...)` rule; the shell probe still runs on the present ones.
      - *Taken, "secrets enter candidate worktrees" (Critical):*
        `.worktreeinclude` patterns are now matched, gitignore-style,
        against `git ls-files -oi --exclude-standard`, and the check fails
        on any copied file with a credential-shaped name (`.env*`, `*.pem`,
        `*.key`, `*credential*`, `*secret*`, `*token*`, `.npmrc`, ...).
        Proven: a scratch repo with an ignored `.env` and a
        `.worktreeinclude` naming it fails with the file named.
      - *Taken, env (High):* a new `env` check fails on credential-shaped
        variable names reaching the shell (SECRET, TOKEN, PASSWORD,
        CREDENTIAL, API_KEY, `_KEY`), names only. Found on the way: the
        session sets `CLAUDE_CODE_MESSAGING_TOKEN` and the sandbox sets
        `CLOUDSDK_PROXY_PASSWORD` for its proxy, neither of which the user
        can unset, so those two families are listed and exempt.
      - *Taken, the default list (High) and `CLAUDE_CONFIG_DIR` (High):*
        `~/.kube`, `~/.config/gcloud`, `~/.azure`, `~/.pypirc` and
        `~/.terraform.d/credentials.tfrc.json` added; the credentials file
        under `CLAUDE_CONFIG_DIR` is on the list when that is set.
      - *Taken, directory rules (High):* a directory secret needs a rule
        that reaches its files (`Read(~/.ssh/**)`), tested by matching a
        deep child path; `Read(~/.ssh)` alone no longer counts.
      - *Taken, `allowWrite` (High):* an `allowWrite` entry outside the
        project and the temp directory fails the write check.
      - *Taken, the three probe-error findings (High):* the write probe uses
        a fresh UUID name and passes only on the sandbox's own errno (EROFS,
        EACCES, EPERM); any other error fails as "cannot tell"; the network
        probe tries two addresses and passes only on ENETUNREACH-class
        errors; a timeout or a refusal fails as a firewall, not a sandbox.
      - *Taken, directory readability (High):* a directory that will not
        list is also probed by opening its usual files (`id_rsa`,
        `credentials`, `config`, ...), so denied listing with allowed
        traversal still reads as readable.
      - *Taken, `autoAllowBashIfSandboxed` (Medium):* checked; absent
        counts as the default, true. Written by `--write-settings`.
      - *Taken, the D line's allowlist (Low).*
      - *Taken in part, "active settings bypass preflight" (Critical):* a
        `--settings` flag on the session's command line is not a file, and
        nothing exposes the effective settings to a script; the probes
        measure the live sandbox regardless, and the four escape-hatch
        keys are the only readings that trust the files. The docstring and
        README say so and say to start the session without `--settings` or
        put the block in managed settings, where nothing can loosen it.
      - *Taken in part, "project path enables shell injection" (High):* the
        command is text the orchestrator writes, so there is no encoded
        argument to pass; the quoting rule in step B now says a path that
        itself contains a single quote is written with `'\''`, the
        shell's own spelling, which closes the hole the finding describes.
      - *Declined, nothing:* every finding reached the script or the text.
      *Not done, deliberately:* no probe of the effective settings from
      inside the session (none exists), and no second mechanism for the
      Read tool (a PreToolUse hook) — the deny rules are what the docs
      offer, and H6 is where to learn whether more is needed.
      *Proven again by running:* in WSL2, write mode on a file holding
      `{"theme": "dark", "sandbox": {"excludedCommands": ["docker"]}}`
      produced the README block around the theme and cleared the excluded
      list, printing each change; a headless sandboxed session then ran the
      script: 8/8 PASS (both probe addresses "Network is unreachable", the
      write "Read-only file system", fourteen paths denied, one present and
      unreadable); the Read tool refused on the credentials file; the
      negative run with the credentials entries removed failed exactly
      `shell-secrets` and `read-secrets`.
      *Run after the round:* sixteen orchestrator cases at three runs,
      16/16 at bar, all sixteen at 1.0 (`results/gate-20261018T001132-*`).
      Evidence recorded for all sixteen.
      *Second Sourcery review on PR #14 (2026-10-18), seventeen findings
      (five Critical, nine High, three Medium): sixteen taken, one
      declined. The first proof run of the fixes lost every `claude -p`
      call to the session limit, which is why the branch sat one night
      with an unproven commit; proven and re-run on 2026-10-18.*
      - *Taken, "nested secrets pass Read check" and "narrow rules pass
        directory check" (Critical, High):* the Read-rule matcher is now a
        glob-to-regex in which `*` and `?` never cross a slash and only
        `**` does; a directory is covered when the rule reaches both
        `dir/x` and `dir/x/y/z`, so `Read(~/.ssh/*)` and `Read(~/.ssh)`
        no longer count and `Read(~/.ssh/**)` or an ancestor's `/**` does.
      - *Taken, "future directory files remain readable" (High):*
        directory intent is explicit: a `--secret` that ends in `/` is a
        directory whether or not it exists yet; the defaults carry the
        slash; `--write-settings` writes the `/**` rule for them.
      - *Taken, "readable secrets go undetected" (High):* a directory that
        will not list is probed by its usual files and by a generic set
        (`config`, `credentials`, `token`, `key`, `id_rsa`, `.env`, ...)
        that applies to custom directories too.
      - *Taken, "copied credentials evade detection" and "root secrets
        evade recursive include patterns" (Critical, Critical):*
        `.worktreeinclude` matching follows gitignore (`**/x` at any depth
        including the root, a slash anchors, no slash matches any
        component, `x/` copies everything below, `!` copies nothing), and
        a copied file counts as a credential by name (`.envrc`, `*.ppk`,
        `*.gpg`, `*.asc`, `.htpasswd`, `id_dsa*`, ... added) or by living
        under `.ssh`, `.aws`, `.kube`, `.gnupg`, `.docker`, `.azure`,
        `gcloud` or `gh`.
      - *Taken, "AWS access key goes undetected" and "credential variables
        bypass the check" (High, High):* `ACCESS_KEY` and `PRIVATE_KEY`
        join the name pattern; the exemption is two exact names,
        `CLAUDE_CODE_MESSAGING_TOKEN` and `CLOUDSDK_PROXY_PASSWORD`, so a
        `CLAUDE_CODE_GITHUB_TOKEN` fails the check.
      - *Taken, "network probes falsely pass" (Critical):* three probes
        (two IPv4, one IPv6), each passing only on ENETUNREACH, EPERM or
        EACCES; EHOSTUNREACH and EAFNOSUPPORT no longer count on IPv4, and
        a missing IPv6 stack skips that probe with a note.
      - *Taken, "settings repair targets wrong file" (High):*
        `--write-settings` takes no path by default and writes
        `settings.json` under `CLAUDE_CONFIG_DIR` (or `~/.claude`), the
        file `settings_files` reads first; step A and the README say so.
      - *Taken, "sandbox blocks settings repair" (High):* a session whose
        sandbox is already on cannot write a file outside the project from
        Bash, so a refused write is caught, reported as `settings not
        written`, and the complete intended content is printed between
        marker lines; step A says to write exactly that content to the
        named path with the Write tool, which runs outside the sandbox,
        under the yes the user already gave, then re-run the check.
      - *Taken, symlink, mode, concurrency, malformed settings (Medium,
        High, High, Medium):* the target is resolved through a symlink;
        the temporary file is created with the original's mode (0600 for a
        new file) under a UUID name in the same directory; malformed JSON,
        a non-object top level and a non-object `sandbox` or `permissions`
        are reported as `settings not written: ... fix the file by hand`
        with the checks still run. Taken in part on concurrency: two
        sessions writing one user settings file at the same instant is
        the same unsupported shape H2 declined for the baseline.
      - *Taken, "special files can hang preflight" (Medium):* only
        regular files are opened, non-blocking; a FIFO, socket or device
        is never read.
      - *Declined, "sandbox check goes stale before launch" (Critical):*
        the check cannot lock the settings between its PASS and the next
        `Agent` call, and nothing in Claude Code offers a lock. What it
        can do is already done: the check runs before every launch, and
        Claude Code applies the sandbox to each command from the settings
        at that moment, so the fence at execution time is Claude Code's,
        not the preflight's; the docstring says which is which. The one
        thing that closes the gap is the block in managed settings, where
        no session can loosen it, which the README names.
      Unit checks of the pure functions (`scratchpad/unit_sc.py`, 32
      cases: the matcher on `/**`, `/*` and bare rules, directory intent,
      gitignore `**/`, anchored and bare patterns, the credential names,
      the env names, write-through-symlink, mode kept, idempotence,
      malformed and null-section settings) pass on Windows and in WSL.
      *Proven by running, 2026-10-18, in WSL2:* write mode on a scratch
      file produced the block; a headless sandboxed session ran the
      script: 8/8 PASS, all three probe addresses "Network is
      unreachable", the write "Read-only file system"; the Read tool
      refused on the credentials file; `--write-settings` on a path
      outside the project inside the sandbox printed `settings not
      written: ... (Read-only file system)` and the intended content; the
      negative run failed exactly `shell-secrets` and `read-secrets`.
      *Run after the second round:* sixteen orchestrator cases at three
      runs, 16/16 at bar, all sixteen at 1.0
      (`results/gate-20261018T110737-*`). Evidence recorded for all
      sixteen. Every thread on PR #14 answered and resolved on the fix
      commit `2bb8e6d`.
- [x] H6. The first real execution of the quarantine flow (added
      2026-10-17). *2026-10-18, branch `plugin-h6-dogfood`.* The flow ran
      end to end for the first time, in WSL2, headless (`claude -p
      --plugin-dir ~/kad-dev-team-plugin`, sonnet, `KAD_AUDIT=1`, audit dir
      `~/kad-h6/audit`), on a scratch project (`~/kad-h6/library-app`: the
      fixture app, the tdd plant's `package.json` and `test/ts-resolve.mjs`,
      the cancel-hold route plant under `docs/cancel-hold/`, one commit).
      Three sessions, read against the hand-off's watch list from the
      stream-json logs and the subagent transcripts (the `audit-review`
      reading, by hand; `audit_report.py --dir ~/kad-h6/audit` lists them):
      - `c0d0b60a-3580-43d4-bbf4-602e6b92f637`: started without the
        settings block. The check ran first, from the skill's own directory
        (`${CLAUDE_SKILL_DIR}` resolved), failed on write, network,
        shell-secrets, read-secrets and settings; the log entry was written
        first, one question asked (in text: `-p` has no `AskUserQuestion`),
        nothing launched, no `dangerouslyDisableSandbox`. The yes led to one
        `--write-settings` call on `~/.claude/settings.json`, whose own
        re-check still failed the probes; the orchestrator logged "restart",
        then ran the check once more and it PASSED: Claude Code reads the
        settings again between commands. The flow then ran to C in the same
        session: baseline before launch, both candidates in worktrees under
        `.claude/worktrees/`, both failing the gate, the judge twice
        `NO VERDICT`, and a stop before Finalize with a diagnosis of the gate.
      - `86cdfb3e-49c6-4547-9eda-235a58b36444`: a prompt that pre-named the
        step ("if the next step is the implementation and its quarantine
        flow, go ahead") made the main agent invoke `tdd-implementation`
        directly, inline, in the real tree: no orchestrator, no quarantine,
        no sandbox check. Killed after a minute; the tree reset. The skill's
        "skip this skill when the user already named what they want" rule
        read "implementation" as the named skill. Recorded here; a case for
        G1 if the user wants the wording tightened.
      - `020a4df0-815d-4a99-bdd1-014cb8c72f63`: the bare prompt (the
        eval's, plus the stack and not-implemented facts). Turn 1 routed,
        wrote the entry, and asked for the go-ahead; turn 2 ran A to D;
        turn 3 (after the gate fix below) re-ran D's gate and ran E. Every
        watch-list item held: check before baseline before launch, `--allow`
        = the design's module dirs + `test/` + the report path (the log
        added only at D, never widened), `--protect` = the five documents;
        candidate 1's task named the slice documents, candidate 2's named
        `requirements-001`, `slice-001` and `design-001` by path as reference
        material with user-story and problem explicitly off the list, both
        carried the two lines, the A line listed every path; the judge ran
        before either worktree was read, `--task` = design + slice only, the
        report excluded; the C line said what the wider read changed
        (nothing a judge or reviewer could tell apart: the candidates were
        near-identical and escalated the same position-renumbering question,
        the first batching datum); the finalize instance got candidate 2's
        inputs plus the brief; D's check ran before it; E ran all five
        reviewers (not UI-touching) as `Agent` calls after D's gate and the
        real `map-update`, each handed the gate's changed files minus the
        log, the map as the diff; 0 Critical/High, so no handed-back round
        (E's fix path stays proven by reading only); the step 5 report named
        both branches unmerged, the Medium findings, the typecheck gap and
        the open question, and proposed nothing past the terminal row. The
        candidates never reached the network (`npm run typecheck` failed on
        the uninstalled `@types/node` and both reported it, not touched).
      Both candidates failed the gate for a real reason there too: branch
      coverage of `infra/memory/in-memory-hold-queue.ts` (78.57% and 72.73%
      against 80: the pre-existing `?? []` fallbacks untested); Combine ran
      with the gate reports as the findings, the brief told Finalize to
      cover them, and the final build reached 100/100. Cost: about $1.4 for
      A to D and $2.9 for turn 3 by the CLI's estimate, under ten minutes
      of wall clock for the whole flow; the "one subscription window"
      estimate was pessimistic by an order of magnitude.
      *Misses, each fixed and proven:*
      - *Gate, coverage table parsed wrong:* `parse_coverage` counted the
        reporter's own `ℹ ` separator space as a nesting level, so a
        top-level directory after a nested one was nested under it
        (`lending` read as `infra/lending`) and `lending/cancel-hold.ts` was
        "not in the coverage table" although the table listed it. H1's
        scratch scenarios had one source directory each. The regex now
        consumes the prefix.
      - *Gate, type-only TypeScript:* a module with no runtime code
        (`lending/hold-queue.ts`, the port interface) is never loaded and
        never appears in the table, so it failed every time; and under
        `--experimental-transform-types` Node counts the lines of an erased
        type alias as uncovered (`cancel-hold.ts` lines 3-5: 82.35% against
        90). New `skills/orchestrator/scripts/ts_runtime_lines.mjs` asks Node
        (`module.stripTypeScriptTypes`, strip mode, or transform mode and
        its source map when strip refuses a parameter property or an enum)
        which lines keep runtime code; a changed file with none is exempt
        and named, and erased uncovered lines are discounted from a loaded
        file's percentage using the table's own count (`uncovered / (1 -
        line%)`), printed as `82.35 -> 100`. Without `node` every line
        counts as before. Checked on Node 24 (WSL) and 22 (Windows).
      - *Judge, cannot run inside the sandbox:* the nested `claude -p` was
        denied `api.anthropic.com` by the session sandbox (its
        `sandbox_violations` say so) and the credentials file is in
        `denyRead`, so the judge H2 built can never run where H5 requires
        the flow to run. `pairwise_judge.py` gained `--render` (both
        prompts and a manifest into `.git/kad-pairwise-<stamp>/`, the
        manifest alone saying which candidate each order showed first) and
        `--collect DIR` (validates the two answer files, settles the
        verdict, writes `verdict.json`, prints the same lines as before);
        a new `agents/pairwise-judge/AGENT.md` (Read and Write, sonnet,
        background) answers one order each, launched by the orchestrator
        with its prompt path and answer path and nothing else; step C and
        the log template say so; the `claude -p` mode stays for the eval
        wrapper, which still imports `compare()`. First real run of the
        agents: both answered in text and wrote no file, since the prompt's
        own last line ("respond with only a JSON object") outranked the
        agent definition; `--render` now ends each prompt with the Write
        instruction and the answer path, and C says to save a replied JSON
        to the answer file before relaunching, and to collect only once both
        agents have returned (the orchestrator collected once too early).
      - *Gate, Claude Code's own paths in the real tree:* D's gate failed
        scope on `.claude/worktrees/<agent>/` (the `Agent` tool keeps the
        candidates' worktrees inside the project; git lists each as an
        untracked directory) and, inside the sandbox, on the empty
        placeholder settings it mounts into every directory a command runs
        from (`docs/.mcp.json`, `docs/cancel-hold/.claude/{hooks,
        launch.json, settings.json, ...}`, `docs/cancel-hold/.mcp.json`:
        device nodes outside, listed as untracked inside). The gate, and so
        the judge's views, now leave every `.claude/` directory and
        `.mcp.json` out of the change set; a settings edit there is the
        sandbox check's to catch before every launch.
      - *Skill, step A:* after `--write-settings`, run the plain check once
        more as its own command before concluding that the session predates
        the setting; the settings take effect on the next command.
      - *Skill, step B:* the verdict stands even when the orchestrator
        doubts the gate, with the one exception it took in the first session,
        now written down narrowly: both candidates fail a check the gate's
        own printout contradicts on its face; then stop before Finalize,
        record the output under C and report a plugin defect; report what
        the gate printed, don't read or patch the plugin's scripts (it had
        read `validation_gate.py` to diagnose, outside its lane, correctly).
      *Facts worth keeping:* a `-p` session has no `AskUserQuestion` (the
      orchestrator asks in text and the next `claude -p --resume` answers);
      a background agent's hand-back starts a new turn, so the stream holds
      one `result` per turn and a monitor must not stop at the first; the
      sandbox masks `.bashrc`, `.gitconfig`, `.idea`, `.vscode` and friends
      in the working directory as device nodes, which `git status` shows
      and `git ls-files -o` does not; plugin agents' `tools:` did not stop
      the cartographer agent calling `Skill` (the orchestrator ran
      `architecture-review` on it), so the reviewer list needs no persona
      change; `--plugin-dir` hooks fired in `-p` (the audit dir has all three
      sessions' logs and transcripts, subagents included).
      *Scratch checks of the fixes* (`scratchpad/h6-test-fixes.sh`, on the
      first session's worktrees): the parsed table has both directories;
      candidate 1 fails only the real branch shortfall with the exemption
      and the discount printed; candidate 2 passes; the real tree passes
      with the log allowed and no worktree in its change set; `--render`
      leaks no worktree path into either prompt and refuses a non-empty
      directory; `--collect` with no answers names both orders and exits 2,
      with two consistent answers prints the candidate, with a malformed
      answer names the order; the eval wrapper still runs.
      *Run:* sixteen orchestrator cases at three runs, 16/16 at bar, all
      sixteen at 1.0 (`results/gate-20261018T124007-*`). Evidence recorded for all
      sixteen. Bars left at 1.0.
      *Sourcery on PR #15 (2026-10-18), two passes over the same diff,
      twelve threads, seven distinct findings:*
      - *Taken, "configuration changes bypass review" (High):* the gate
        dropped every `.claude/` path and `.mcp.json` from the change set,
        so a candidate writing a project `.claude/settings.json`, or an
        application file named `.mcp.json`, would have been invisible to
        scope and to the judge. Now only an *untracked* such path that is
        not a regular file with content is dropped (`claude_code_placeholder`):
        the nested worktree directories and the sandbox's mounted
        placeholders are exactly that, and a file a candidate wrote has
        content and stays; tracked changes always stay.
      - *Taken in part, "judge can write outside its answer" / "can access
        unrelated files" (High):* the judge agent lost its `Write` tool: its
        reply is the answer, the orchestrator saves it verbatim to the
        order's answer file and collects; the rendered prompt's closing
        note says so and tells the judge to read nothing else. `Read` stays:
        the prompt is a file because a rendered view can run to 200 KB per
        candidate, more than belongs in an `Agent` call's own text, and the
        session's deny rules (which H5 requires) cover the Read tool for
        every secret path; a judge that read some other project file could
        only taint its own reasoning, which `verdict.json` keeps for the
        orchestrator to read.
      - *Taken, "uncovered runtime code is discounted" (High) and
        "template code is discounted" (Medium):* `ts_runtime_lines.mjs`
        found comments with two regexes, so `//` or `/*` inside a string or
        a template literal blanked code lines. It now walks the text with a
        state machine (strings, template literals and their `${}`
        interpolations, regex literals, line and block comments); checked
        on a crafted file with each case (`--text FILE` runs the walk alone).
      - *Taken, "concurrent judges share run files" (Medium):* the default
        render directory comes from `mkdtemp` next to the baseline
        (`kad-pairwise-<stamp>-<random>/`), an explicit `--out` is claimed
        with `os.mkdir` and refused when it exists with content.
      - *Taken in part, "a stalled judge blocks the flow" (Medium):* the
        skill has no clock, so no timeout; step C now says a judge that has
        not returned long after the other (minutes, not tens of minutes) is
        a missing answer: stop it, collect, and the one relaunch applies.
      - *Taken, "truncated coverage causes false failures" (Medium), and
        declined, "truncated coverage crashes the gate" (Medium):* no
        crash: `None` was already guarded. But Node truncates the table's
        `uncovered lines` column with `…`, which silently lost the discount.
        The gate now adds Node's `lcov` reporter next to the script's own
        reporter when the test command is a `node` script (every reporter
        gets a destination, since Node demands one each; the script's flags
        that take a value keep it) and reads exact per-line and per-branch
        data from it (`parse_lcov`), so the discount never depends on the
        column; when only the table exists and the column is cut, the
        output says `uncovered-lines column truncated, no discount
        possible`. The lcov line count differs from the table's by one on
        `cancel-hold.ts` (81.25 vs 82.35); the discount still reaches 100.
      - *Declined, "TSX type lines still fail coverage" (Medium):* Node's
        type stripping takes no JSX in either mode (checked), so a `.tsx`
        file is counted as it was before this PR; a project whose tests
        load `.tsx` is not running on Node's own test runner with type
        stripping anyway, and its table comes from another toolchain. Said
        in the helper's header and the gate's docstring.
      *Checks after the round* (`scratchpad/h6-test-round2.sh`): the comment
      walk's expected line set; the candidate files' answers unchanged;
      three test-script shapes get the right reporters; candidate 1 and 2
      of the third session fail only the real branch shortfall, exact data
      in use; the real tree keeps a non-empty `docs/x/.mcp.json` in the
      change set and drops an empty `docs/x/.claude/settings.json`; two
      renders in the same second get two directories; the reply-only note
      ends each prompt; a non-empty `--out` is refused; collect settles.
      *Run after the round:* sixteen orchestrator cases at three runs,
      16/16 at bar, all sixteen at 1.0 (`results/gate-20261018T130441-*`).
      Evidence recorded for all sixteen.

## I. The second real run: compare policy, the handed-back round, lite in real use (2026-10-19)

The user's decision on 2026-10-19, after G2: run the quarantine flow for
real a second time under the compare policy, since one run answers three
of the four things the hand-off left open at once — whether lite's
verification steps hold under real use, how the Grade step's reviewers
read heavy against lite, and the handed-back round in E, proven by
reading only until now — and fold whatever it finds in with the small
findings carried forward. Same ground as H6: WSL2, headless, sonnet,
`KAD_AUDIT=1`, the scratch project at `~/kad-h6/library-app` reset to its
one commit, the plugin mirrored from `main` at `7d4e5d1` (PR #18's merge).

- [x] I1. The run. Three turns of one session
      (`faa92615-7360-4967-83b4-f66172323ab2`; logs `~/kad-h6/logs/run2-turn{1,2,3}.jsonl`,
      the audit dir's transcripts, subagents included; the scratch
      scripts of the session that ran it, `run2.sh`, `by-agent.py`,
      `dump-agents.py`, are the recipe). *The plant:* a decision appended
      to `design-001.md`, uncommitted, that every cancellation and
      rejection is logged through the existing logger "with the card
      number and the ISBN", so the build would carry a High the security
      reviewer's own rule names (a natural identifier reaching a
      persistent exit).
      - *Turn 1 (23 s, $0.19):* the bare "what's next" prompt. Routed to
        the implementation row, wrote the entry, asked the policy
        question in text (heavy recommended, lite, compare, not now) and
        stopped — and, unprompted, named the uncommitted design edit from
        `git status`, said the slice's security criteria were written
        before it and do not cover card numbers in logs, offered to build
        to the file as it stands or re-run the security requirements pass
        first. The answer: compare, build to the design as it stands.
      - *Turn 2 (9 min 17 s, $4.06), A to E in one turn:* A — policy
        `compare` on the line; sandbox check PASS; both candidates given
        the full-unit read context (compare holds it equal); the design
        and slice handed by absolute path into the real tree, read-only,
        because a worktree is cut from `HEAD` and the uncommitted decision
        was absent from both — the orchestrator saw this itself and
        recorded why on the A line; baseline recorded. B — gate PASS for
        both (the coverage check both H6 candidates failed passes with
        H6's fixes in place), one throwaway map diff each (the new
        `lending → infra/logging` edge, named in the design), ten
        reviewers. Candidate 1 (heavy): security High, card number in the
        log; reliability High, failed cancels not logged, and a second
        High for the pre-existing in-memory store. Candidate 2 (lite):
        the same security High; test-quality High, its tests read the
        adapter's private `holds` map through a cast. C — the two judge
        agents returned and the orchestrator saved their replies and
        collected: candidate 1 in both orders. The reasons were the
        tests, the production code being near-identical: candidate 1
        asserts queue state only through the port and captures the real
        stdout line, candidate 2 reads the private map and mocks
        `log.info` without checking the message. The combine brief built
        from candidate 1, added failure logging and a stateful stub for
        the unreachable-queue test, and listed five escalations not to
        build — the card number (High from both security reviews "but
        mandated by the approved design"), the stale `position`, the
        logger edge, the volatile store, staff-only authorization. D —
        the finalize instance (heavy, under compare) built it in the real
        tree, 14 tests, gate PASS, map persisted; its report disclosed
        three deviations from its own skill: every test written up front
        then made to pass one at a time, `test-quality-review` once at
        the end, one test appended through a heredoc. E — five reviewers;
        the security reviewer rated the card number **Medium**, in its
        own words "because the design mandates it, the user has already
        been told, and the logger writes only to stdout", the first two
        of which the orchestrator's task had told it ("mandated by the
        approved design and was already escalated to the user; still
        report it if you judge it a finding, flagged as design-mandated");
        the reliability reviewer numbered the pre-existing in-memory store
        as a High with "I'm not recommending it block" in the body;
        combine-brief check 6 pass, 2 fail (both Medium or Low, so not
        handed back); handed back — none, "the only High is outside the
        slice". The report put the card number, the positions and the
        store to the user as decisions and proposed no next step.
      - *Turn 3 (3 min, $5.45), the handed-back round:* the user amended
        the design's logging decision in place (the ISBN and a one-way
        SHA-256 hash of the card number, never the number) and said stdout
        ships to a shared log platform, so the finding is High and in
        slice. The orchestrator wrote entry 2 as a correction to entry 1's
        E line, ran the sandbox check, and handed the fix back to the
        same finalize instance with `SendMessage` (the Agent tool's
        continuation works in a `-p` session) as five named fixes with
        the amended design as the authority. The instance took its
        skill's handed-back path: the tests changed first, five RED on
        the field mismatch, the code, green at 15, the break (the raw
        card number put back on one line) caught by two tests, restored,
        green, the report's escalation marked resolved. The gate then
        failed `protected` on the design the user had just amended; the
        orchestrator worked out which hash the baseline uses, copied the
        baseline aside and rewrote that one file's hash, and the gate
        passed — right outcome, outside the procedure (see I3). It skipped
        the map re-run as "no new internal edges", though the fix imports
        `node:crypto`, which the map's external-package column records.
        All five reviewers re-ran on the fix's files. Security: the
        original High is not closed — an unsalted SHA-256 of a 14-digit
        card number with a shared prefix is brute-forceable by anyone who
        reads the log, and the design's own tracing method (hash the
        number you hold) is the attack — with two design-level fixes
        (an opaque id, which needs an id the slice does not have; a keyed
        hash from the secret store); plus a Medium, the failure line's
        `reason` passing the adapter's raw error message through. One
        round used, not repeated; the slice reported implemented with the
        High standing and the choice put to the user. That is the E path
        as written, end to end, for the first time.
      - *What held, read against the watch list:* the policy question
        asked and stopped on; the A line carrying the policy and the
        compare context; the judge agents replying and the orchestrator
        saving the replies verbatim before collecting (H6's miss, now
        fixed); the C line saying what the discipline changed; Finalize
        getting candidate 2's inputs plus the brief; the sandbox check
        before every launch; the hand-back to the same instance, once,
        through its named-fix path; the gate and the reviewers re-run
        after the fix; the stop after one round with the High named for
        the user; the candidate worktrees and branches left for the user.
- [x] I2. Lite in real use, and heavy against lite read by the reviewers.
      The lite candidate held all four verification steps unprompted on
      the agent path: the test file first (4.3k characters), then the
      stubs (a use case always rejecting, `remove` always false), one RED
      run with every test failing on its own assertion, the code, green
      at 10, the break (`===` to `!==` in the adapter's `findIndex`)
      caught by five tests, restored, green; four test runs; the consult
      before any code; the position question escalated to
      `acceptance-criteria`; the report in the contract's shape. What it
      lost, it lost on test quality, which heavy's per-cycle review kept:
      the lite tests reached into the adapter's private `holds` map to
      check the whole queue ("since the port exposes only head and
      length; I did not widen the port"), reported honestly as a decided
      gap, rated High by the test-quality reviewer, and the reason the
      blind judge chose heavy in both orders. So on this slice the
      reviewers and the judge read heavy as better, the opposite of the
      eval's 18/18 for lite on the slice case — one run against nine,
      and the difference is one habit (asserting through private state)
      the eval's lite runs did not show and the contract's "through the
      public interface" did not stop. *Fix, lite skill text:* step 1 now
      says through the public interface means asserted through it too, a
      cast to private state is a test of the implementation, and a port
      that exposes too little gets asserted through what it does expose
      or escalated as a design gap, never peeked. Heavy stays as it is.
      *Also seen:* the heavy finalize instance, handed a brief that lists
      every test, wrote them all up front and reviewed once (H6's
      finalize instance ran seven cycles); recorded as a line in step D
      (the brief says what, the skill says how), one run.
- [x] I3. Plugin misses from the run, each fixed in text, the sixteen
      orchestrator cases and every other affected case re-run as the
      regression check (I5):
      - *The orchestrator primed the reviewers.* Both E tasks and the
        post-fix security task carried the flow's own state: that the
        finding was design-mandated and already escalated, that stdout is
        shared, what the fix was for, "including whether an unsalted hash
        ... is brute-forceable". The severity dropped exactly where the
        task said the user had been told, and E acts on Critical and High
        alone, so the leaked context is what kept the handed-back round
        from firing on the plant. Step B now says what a reviewer's task
        holds (the skill, the tree, the files, the diff, the criteria and
        design by path) and what it never holds (a finding, a severity,
        an escalation, what the user has been told, a verdict, a "check
        whether"); E and the post-fix reviewers get the same rule.
        `security-review` and `reliability-review` gained the mirror of
        their "don't inflate" line: nothing about how the code came to be
        lowers a severity; a design mandate or a prior escalation changes
        who owns the fix, which goes in the fix line.
      - *Pre-existing numbered as High.* `reliability-review` had only
        "note pre-existing issues separately as lower priority";
        `security-review` had the full rule (a separate "Pre-existing,
        not blocking" section, no number, no severity, say what new
        exposure the change adds). The reliability reviewers put the
        in-memory store among the findings as High in two of three
        reviews and as Medium "(pre-existing, newly relevant)" in the
        third. The rule is now in `reliability-review` too, with why: the
        orchestrator hands every High back, and "not recommending it
        block" in the body does not undo the heading.
      - *Map re-run skipped after the fix.* E's step 2 now says always,
        however small the fix looks: whether an edge changed is the map's
        call, and an import of a built-in module changes the
        external-package column.
      - *A protected document the user amends mid-flow.* No path existed;
        the orchestrator improvised a hand edit of the baseline. The gate
        gained `--baseline FILE --accept-protected PATH`: rewrites that
        one file's recorded hash to the tree's content, prints old and
        new, exits; never re-records the whole baseline (that would hide
        the build's own files). Step D says when it is allowed (a change
        the user made, said so in the conversation) and never for a
        change a candidate or instance made, recorded on the step's line.
        Checked on the run's own project (`scratchpad/check-gate-flag.sh`):
        refused without `--baseline`, refused for a missing file, the
        gate FAIL before and PASS after, idempotent, and the hash it
        writes is the one the orchestrator had worked out by hand.
      - *Uncommitted documents absent from the worktrees.* The
        orchestrator caught it this time; the next one might not. Step A
        now says to check `git status` on the target directory's
        documents before launching and hand any modified or untracked one
        by its absolute path in the real tree, read-only, to the
        candidates, the finalize instance and the judge, saying so on the
        A line; never commit it yourself.
      - *Finalize under a brief:* the one-line rule in D, above.
- [x] I4. The small findings carried forward, folded in:
      - *`why-comments` wandering into code review* (`stays-on-comments`
        0/3 at the last recorded run, bar 0.857): the failed review had a
        titled "Code concern" section — the retry loop stacking with
        Stripe's retries, no idempotency key, "worth a code-review or
        reliability-review pass" — three sentences and a second problem
        where the skill allowed one line. The skill's line now says one
        sentence inside the comment's own verdict, no section, no second
        problem, no fix, no "which review should look", and that a
        comment contradicting the code is a comment finding whose whole
        verdict is "the comment is wrong".
      - *The delegated architect reading the map file instead of
        invoking `map-query`* (`architecture-design-payfine-via-agent`
        0.867, `consults-map-query` 1/3): `architecture-design` had
        "Invoke it with the `Skill` tool, under that name" and nothing
        else; the lite skill's wording from G2, which the delegated
        implementers followed 2/2 in the real run, is ported: before any
        structure is worked out, reading the map file or grepping is not
        the consult, the `Skill` call is what a trace looks for, and the
        rule holds inside a delegated `software-architect` agent too.
        `architecture-design-payfine-phase2` resumes a history that
        carries the skill text, so it is re-frozen from a kept phase-1
        run before it is re-run (the gate refuses it otherwise).
      - *The phase-2 fork graders at 0.92:* the two `-stop` cases, each
        losing one run in three to the judge, both G5's shape (the rubric
        narrower than a correct output). Security: the run wrote "They
        must never include card data" about the receipt, one line, which
        the rubric's "must statements about contents" failed, though its
        PASS clause allows the same observation worded as an observation;
        now a one-line obligation about card data passes, a set of
        requirements fails. Reliability: the run recommended the outage
        case become a later slice and this one ship for the normal case
        with the shortfall stated — a view on the scope decision, which
        the rubric allows — and the judge read it as "proceed with the
        outage case noted as a limitation"; now a recommendation to the
        scope owner passes whichever way it goes, and the test is what
        the response does next (it still stops; it neither asks for the
        forks' approval nor writes criteria).
      - *The gate arithmetic:* one grader flip at three runs moving a
        score 0.111, over the flat 0.1. `eval_evidence.tolerance_for`:
        the tolerance is the flat value or the width of one flip in one
        run, 1/(graders × runs), whichever is wider, with runs the larger
        of the result's and the bar's, so a one-run first pass with a
        flipped grader is still suspect and re-run at the case's count,
        and a full-count sample absorbs exactly one flip; two still fail;
        the per-grader regression check is unchanged; bars without
        per-grader rates keep the flat tolerance. Used by the gate's
        retry decision and verdict and by the evidence check.
- [x] I5. Runs and bars: 58 affected cases at three runs. *2026-10-19,
      three WSL batches (`results/gate-20261019T0*`):* batch 1, the
      seventeen orchestrator cases, 17/17 at 1.0. Batch 2, 12/12 at bar:
      `architecture-design-payfine-phase1` 1.0 kept, phase 2 re-frozen
      from its run 0 and 0.96 (`decisions-show-approval` one run, as
      before); `why-comments-collect-fine` 1.00 (from 0.86,
      `stays-on-comments` 3/3); `architecture-design-payfine-via-agent`
      1.00 (from 0.87, `consults-map-query` 3/3);
      `reliability-requirements-payfine-phase2-stop` 1.00 (from 0.92);
      `security-requirements-payfine-phase2-stop` 0.92, the receipt
      grader now 3/3 and one run lost to `does-not-lay-out-scope-options`
      instead; the two lite cancel-hold cases 0.96 each with only the
      per-test-cycle measurement grader lost 3/3, named-fix 1.00; heavy
      cancel-hold 0.96 (one run lost the per-test cycle and the per-cycle
      review together — the heavy loop dropped by the model one run in
      three, the real run's finalize deviation seen in the eval too — and
      one run `tests-check-behaviour`), via-agent 0.96 (three different
      graders, one run each), named-fix 1.00. The three improved bars are
      recorded. Batch 3, the review suites: 12 at 1.0 and then the
      subscription's session limit, so sixteen cases never ran
      (`code-review-days-left-pr`, `-fine-notices-pr`, `-via-agent`,
      `-fines-report-pr`, `reliability-review-portal-pay-pr`,
      `security-requirements-neg-review`, every `security-review-*`,
      `supply-chain-review-neg-reliability`,
      `test-quality-review-neg-code-review`), and what the table showed
      as one real failure, `reliability-review-nightly-via-agent` 0.42
      against 1.00 with three `no-false-alarm-*` graders lost: read, it
      was the limit too. The three reviews were written and complete
      (the same findings as the recorded bar's, the SMS retry noted as
      correctly scoped at Low), and every lost grader's explanation reads
      "grader threw: judge call failed: You've hit your session limit",
      which the CLI records as a plain FAIL — eight graders in runs 0
      and 1, three in run 2. *Gate fix:* `eval_gate.py` now treats a run
      with a grader that threw as an errored run, excluded from the score
      like a run that never started, and a case with no clean run as an
      error, so a judge the limit stopped is reported as a stopped judge
      and never as the skill losing graders. Batch 4, the seventeen
      cases once the limit reset: 16/16 at bar (the via-agent nightly
      case itself 1.00), twelve at 1.0, the rest the known judge traps a
      run each (`leaves-mocking-to-test-quality-review` on the
      fine-notices pair, `hands-sdk-to-architecture-review` and
      `finds-month-as-raw-string` on the fines report,
      `no-false-alarm-oidc-deploy-job` on the config case), all inside
      tolerance. So: 57 cases run at three runs, 57/57 at bar, evidence
      current for every affected case (`eval_evidence.py --base
      origin/main` all ok), about 170 runs in four WSL batches.
- [x] I6. Sourcery on PR #19 (2026-10-19), seven findings, six taken and
      one in part, every thread answered:
      - *Taken, "paths can execute shell commands" (High):* the skill's
        `--accept-protected` example carried a garbled placeholder (a
        stray triple quote); it now shows plain single-quoted
        placeholders, names B's quoting rule and passes the gate's
        `--protect` list.
      - *Taken, "candidate edits disappear" (Medium):* `--accept-protected`
        refuses any path the same command does not name with `--protect`,
        so only a protected document can be accepted and a source file a
        candidate edited can never be hidden from scope or coverage.
        Checked on the run's project (`scratchpad/check-round.sh`): a
        protected path not on the list and a source file are refused, the
        listed design doc is accepted, the baseline stays valid JSON.
      - *Taken, "passing evidence is undersampled" (Medium):* `_run_case`
        gets the requested run count and returns `only N of M runs
        clean` as an error when fewer completed cleanly, so a case never
        passes or records evidence on a smaller sample than its bar.
      - *Taken, "symlinked documents expose host files" (Medium):* step A
        checks, inline, that a document handed over by absolute path is a
        regular file whose `realpath` is inside the project; otherwise
        it is not handed over and the procedure stops.
      - *Taken, "candidates can mutate shared documents" (Medium):* the
        `sha256sum` of each handed-over document goes on the A line
        before launch and is taken again when both candidates have
        returned; a changed sum ends the procedure like a failed sandbox
        check, no reviewer launched, reported as a candidate writing
        outside its worktree.
      - *Taken, "judge failures corrupt saved thresholds" (Medium):* the
        grader-threw marker is set before `keep_traces` and written back
        into the result file, so `record_thresholds.py` skips those runs.
      - *Taken in part, "baseline updates are lost or corrupted"
        (Medium):* the baseline is written to a sibling temp file and
        swapped in with `os.replace`; no lock, since the one orchestrator
        instance runs the acceptance once, inline, and nothing else
        writes the baseline.
      *Run after the round:* the seventeen orchestrator cases at three
      runs (the skill text and the gate script changed), 17/17 at bar,
      sixteen at 1.0 and `orchestrator-backward-route` 0.95 (one run lost
      `does-not-go-forward-to-reliability`, G4's one-run-in-three
      narration noise, inside tolerance; `results/gate-20261019T110622-*`).
      Evidence recorded for all seventeen.

## J. Implementation flow v3, the chunk loop (2026-10-24)

The quarantine flow was retired for the chunk loop
(`.synthesis/implementation-flow-v3.md`). Its §8 lists ten cases; four run
without the orchestrator's real launches and were built, the rest are
proven by real runs the way the quarantine flow was (H6, I).

- [x] J1. `tdd-implementation-chunk-plan` and `tdd-implementation-lite-chunk-plan`
      (§8.1): the B step through the implementer, vertical chunks with the
      five lines, `map-query` consulted, nothing built. Done 2026-10-24
      after five calibration runs (the README rows have the account): the
      chunk floor, the Title line, named tests and the gap line were skill
      fixes; prose around the entries, the folded or separate
      unreachable-queue chunk and two-word Touches were grader fixes. Bars
      recorded at 0.86 each from `results/gate-20261024T215121`; the
      remaining losses are the Sonnet judge flipping on plans that read
      like the passing ones (`rejudge.py --explain` passes them), so a bar
      below 1.0 is the honest measurement.
- [x] J2. `tdd-implementation-one-chunk` (§8.2): chunk 1 of a planted
      three-chunk plan in a git repository on the slice branch; one commit
      titled as the chunk with the report section in it, chunk 2 (a
      failing queue) left unbuilt, no `git add -A`, no push, no amend.
      Done 2026-10-24: 0.90 on the first run (the scaffold had no in-place
      test runner, so the implementers built one in `$TMPDIR` and the
      `runs-the-tests` grader could not see it; `no-bash-writes` flagged
      the heredoc append of the report section, then the source paths
      quoted in its body). Runner planted from `code-plants/tdd`, the
      Bash-write scan stops at a newline, the reflog grader describes the
      file as it is: 1.00 in 3/3 (`results/gate-20261024T204248`). Bar
      recorded.
- [x] J3. `external-review-triage-cancel-hold` (§8.8): five comments of
      the four verdict kinds on a planted delivered slice; the real defect
      is one our own reviewer reports called a not-finding, so the "missed
      by this flow's reviewers" section is exercised. Done 2026-10-24:
      1.00 in 3/3 twice (`results/gate-20261024T202213`, `-203629`). Bar
      recorded.
- [ ] J4. Not cases, by decision: §8.3 gate on a chunk, §8.4 validator
      selection, §8.5 fix rounds (regression/pre-existing split, the cap),
      §8.7 delivery (needs `gh` and a remote), §8.9 stall, §8.10 the log
      entry end to end. Each needs the orchestrator launching real agents
      inside the eval sandbox; read them from the first real v3 run's
      `orchestrator-log.md` (`orchestrator_log_check.py` knows the format
      and the sidecar) and the audit repository. §8.6 (sandbox opt-out)
      has no way to force `sandbox_check.py` to exit 2 inside the Linux
      eval sandbox; the Windows real runs exercise it.
- [x] J5. Re-record the 34 cases the v3 edits reach (the orchestrator's,
      the tdd skills', `code-reviewer`'s through its third skill, and
      `test-quality-review`'s consults); the two routing cases
      `orchestrator-route-implementation(-prenamed)` were rewritten for
      the A step and may move. Done 2026-10-24: `eval_gate.py --stale`
      over the 38 affected cases, 33 at bar in one pass
      (`results/gate-20261024T205716-*`), the two routing cases 1.00; five
      errored on the subscription's session limit and passed when re-run
      after it reset (`gate-20261024T21*`: `orchestrator-backward-route`,
      `tdd-implementation-cancel-hold`, `tdd-implementation-named-fix`,
      `why-comments-collect-fine` 1.00, `tdd-implementation-lite-named-fix`
      0.96 over its three-run re-run, inside tolerance). No bar moved.

## K. Implementation flow v4, PR 3: the loop's steps as cases (2026-10-31)

`.synthesis/implementation-flow-v4.md` §11 lists twelve cases; the root
`TODO.md`'s PR 3 is the work list. J4's "not cases, by decision" is
narrowed: the eval does offer the `Agent` tool, so each step of the loop
is a case resumed from a planted state
(`fixtures/library-app/code-plants/loop/state.sh`); only the log entry end
to end and the stall rule stay with the real runs.

- [x] K1. The cases, built 2026-10-31: `orchestrator-readiness-gate`,
      `-plan-check-seam`, `-gate-deviation`, `-gate-outside`,
      `-chunk-review-round`, `-one-fix-round`, `-gap-without-delegation`,
      `-definition-of-done`, `-budget-exceeded`, `-delivery-foreground`;
      `delegation-consult-with-file` and `-without-file`;
      `code-review-comments-chunk`; `test-quality-review-seam-fake`;
      `requirements-refinement-open-question`,
      `security-requirements-placeholder-pointer`,
      `architecture-design-scope-consequence`; three graders on
      `tdd-implementation-one-chunk` and one on each chunk-plan case;
      `orchestrator-log-format/check.sh` (no model). The plants are
      `answer-key.md`'s `L` and `P` rows.
- [x] K2. Calibrate: one run of every new case (2026-10-31, the Mac,
      `results/gate-20261031T163624-*` and `-163944-*`), every failure
      read. Fixture: the gap state lacked the reliability document its
      review cites; the scope-consequence criterion read as vacuous for an
      in-memory queue; the handoff file was left uncommitted though the
      skill commits it with the records; the readiness case's prompt let
      the flow run on past A (the skill continues once the gate passes),
      so it now hands off at the A line. Grader: the consult may revise
      its document through a shell script, not only Edit/Write. Plugin:
      `rounds_record.py` counted a smoke report's bulleted Severity as no
      finding and said PASS (now tolerated, and an unparsed smoke report
      must say PASS or exit 1); the E step never committed the log, so
      `delivery`'s clean-tree rule stopped delivery (E.1 now commits log
      and records, handoff removed); the scripts fall back to a working
      git when the first on PATH is Apple's shim. Environment, not the
      plugin: inside the Mac eval sandbox `git` by name fails (the README's
      gate section), so the loop, tdd and delegation-with-file cases
      cannot be measured there.
- [x] K3. Record the bars. From the Mac (`gate.sh --runs 3`): the six
      cases whose agent needs no git, `requirements-refinement-open-question`,
      `security-requirements-placeholder-pointer`,
      `architecture-design-scope-consequence`, `test-quality-review-seam-fake`,
      `delegation-consult-without-file`, `code-review-comments-chunk`
      (done 2026-10-31: 1.00, 1.00, 0.67, 1.00, 0.92, 0.90, see the
      coverage rows; the scope-consequence bar is judge noise on a
      last-message grader, recorded as measured). Then the ten
      `orchestrator-*` loop cases and `delegation-consult-with-file`, from
      the Mac once the `git` shim `gate.sh` asks for exists, or from WSL
      (`wsl-gate.sh --runs 3 --cases ...`), then `record_thresholds.py
      --gate-only` for all seventeen. Done 2026-10-31, all from the Mac
      once the `git` shims existed: fourteen at 0.90 or above (eight at
      1.00 in 3/3), `definition-of-done` 0.88, `budget-exceeded` 0.80 and
      `architecture-design-scope-consequence` 0.67 recorded as measured
      (judge losses on last-message graders, see the rows). Two more real
      defects on the way (the gate command and the log; resuming from a
      handoff that names E), both fixed.
- [x] K4. Re-record the cases the v4 skill edits reach: `gate.sh --stale`
      three times over the day (2026-10-31), 49/58, then 27/28, then the
      last case, as the skill edits re-staled them. Two accessibility
      graders and three routing graders still encoded v3 rules (criteria
      in the slice, one step per invocation) and now follow PR 2's; the
      backward-route case exposed the orchestrator matching the forward
      table before reading a hand-back at the end of a document, fixed in
      the skill. The four history chains whose frozen phase-1 text
      predated PR 2 were re-frozen (phase 1 re-run, phase 2 and 3
      re-frozen in turn), all at bar but security phase 3 at 0.89 as
      measured. The evidence check is green for all 68 affected cases.

- [x] K5. Issue #25, the owner's pick (2026-11-01): the slicer writes the
      accessibility line as not applicable when its thin path has no
      user-facing interface (nonvisual ones count as screens; the
      exemption never defers the interface), and the orchestrator requires
      the status either way: the line read as filled on a non-UI slice, a
      plain placeholder or none on such a slice and the line on a UI slice
      both routed back to the slicer. `vertical-slicing-no-screen` (1.00
      in 3/3) and `orchestrator-route-slicer-accessibility-mistake` (1.00
      in 3/3) are the cases, `vertical-slicing-payfine-phase1` fails the
      line on its portal slice, and the non-UI fixture slices carry it.
      31 affected cases re-recorded at bar.
