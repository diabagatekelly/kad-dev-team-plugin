#!/usr/bin/env bash
# Puts the repository a replay history was captured on under the run's
# working tree, so every hash the history names is a commit here.
#
# A replay case resumes the transcript of a real session (history.jsonl in
# the case's directory; evals/README.md, "Replay cases"). The loop's states
# (code-plants/loop/state.sh) write the day's date into the log and the
# handoff, so each build of `planned` has its own hashes, and the ones the
# captured runner already read and used (its base commit, its `git log`)
# would name nothing. capture.bundle holds the two branches as they were
# when the runner launched its builder (`planned`: the plan commit and the
# handoff commit, no chunk commit); orchestrator-log.md is the log as it
# stood then, uncommitted, with the open chunk-loop entry.
#
# Usage, from the run's working directory, after `state.sh planned`:
#   bash restore.sh
# Captured 2026-11-13 on kad 0.14.5 (Claude Code 2.1.323). Capture again,
# and replace all three files and the cases' history.jsonl together, when
# the fixture's planning set or the `planned` state changes.
set -euo pipefail
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
git fetch -q "$dir/capture.bundle" '+refs/heads/*:refs/capture/*'
git checkout -q --detach
git branch -qf main refs/capture/main
git branch -qf slice-001-cancel-hold refs/capture/slice-001-cancel-hold
git checkout -qf slice-001-cancel-hold
cp "$dir/orchestrator-log.md" docs/cancel-hold/orchestrator-log.md
