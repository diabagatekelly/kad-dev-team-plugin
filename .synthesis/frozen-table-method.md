# Completeness tables: the method (frozen 2026-11-19, before the project 3 run)

You are building requirement-completeness tables for one slice of a project, from its planning documents and the real documentation of every external system it depends on. You see no code. Every cell gets a stable id and exactly one tag:
DECIDED (quote the plan, with document and line), PLAN SILENT, CONTRADICTS DOCS (the plan decides it but the external documentation says otherwise; cite both), IMPOSSIBLE (say why), or SAME AS <cell id>.
Cite a URL for every external fact. When the documentation is silent or unclear, say so; never guess a code, a field or a timing.

Scope: the slice named in your task. Earlier slices' documents are context: build rows for what this slice adds or changes, and for older behaviour only where this slice's changes reach it.

## Table 1. External system dossier
For every external system the slice touches (a provider's API, the OS's secret store, the database, the file system, the browser, the local server): every call or operation the slice needs; its inputs, outputs and the fields used; its side effects (what exists afterwards on the other side); its documented errors with exact codes; documented timings, readiness signals, pagination and limits; whether a retry is safe and what happens when the reply is lost after it acted. Then list every statement of the plan (numbers, statuses, codes, assumptions, anything marked "to verify") that agrees with, contradicts, or is not covered by the documentation.

## Table 2. State x event
For every lasting thing the plan names (each record, connection, attempt, job or setting with a life of its own, and the app process itself): rows are every state; columns are every event that can reach the app: each owner action (including repeating it, and reloading or reopening the page), each reply and each failure of each external call from Table 1, the app stopping and restarting, a second running copy of the app, each dependency being unavailable, and time passing (expiries, deadlines).

## Table 3. Failure modes of every external call
For each call in Table 1: success; failed before reaching the other side; took effect on the other side but the reply was lost; each documented error; a malformed or unexpected reply; slow; partial (part of the work done, then a failure).

## Table 4. Input partitions
For every value the app takes from outside (each field it reads from an external reply, each owner input, each configuration or environment value): valid; each boundary value; empty; missing or null; wrong type or malformed; out of range; too long; duplicated; refers to something that does not exist; special characters and encodings.

## Table 5. Lifecycle of every owner action and long operation
Done twice quickly; started while another is in progress; interrupted by the app stopping; run by two copies of the app at once; abandoned midway; retried after each kind of failure.

## Summary
Counts of cells per table, with PLAN SILENT and CONTRADICTS DOCS counts. Then the 15 PLAN SILENT or CONTRADICTS DOCS cells most likely to become bugs a user meets, ranked, each with one line on what the user would see.
