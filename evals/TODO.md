# Eval suite work list

From `AUDIT-2026-10-12.md`. Phases are ordered by dependency: each phase's
re-record depends on the previous phase's graders being right, so finish a
phase before running its evals. "Run" marks items that need a paid eval run
to close; everything else is a file edit. Keep the README playbook's rule:
read every failure before re-recording a bar.

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

Edits done 2026-10-15 on branch `eval-phase-f` (commit `61afee4`); the
runs are F10. The change reaches 58 cases: the 26 whose graders changed
outright, plus the 32 that hold a trap grader (F4) or copy the shared
UI slice (F1).

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
- [ ] F10. Run the changed cases, re-record. Run.
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

## G. Only after A–F

- [ ] G1. Harder plants and rejecting answers so scores leave the 1.0
      ceiling.
- [ ] G2. A lite variant of `tdd-implementation` as a second plugin dir,
      run through the same cases as a third arm.
- [ ] G3. Coverage items from the audit's section 8 that no case checks
      (stop-and-report paths, ADR hand-offs, consult calls).
