# Deterministic code-quality tooling survey

Compiled 2026-11-12 for the review-balance proposal that came out of the issue #33 fix review (`~/.claude/kad-audit/reviews/2026-11-12.md`, findings 9 and 10): which checks a tool can make, so the model reviewers are kept for judgement and the cold read for behaviour. Researched by one agent against live registry and documentation pages; nothing was installed or run. Section (d) lists what was not verified, and every adoption needs a trial run on the fixture first.

Checked on the first project after the survey came back: its lint already resolves `typescript` 6.0.3 for typescript-eslint while `tsc` is 7.0.2 (pnpm installed the 6.x peer), so type-aware ESLint rules can run there today without an alias.

Two points the survey raises for the plugin's own design:

- **The screen-change check.** The loop drives the app through Claude in Chrome, whose screenshots are not byte-stable. A pixel diff needs a scripted browser (Playwright as a library with pixelmatch, inside the project's own test runner) and baselines per operating system, because rendering differs between macOS, WSL and Linux CI.
- **Stack neutrality.** The plugin names the categories; `technology-bootstrap` picks the tool for the project's language. The TypeScript and Python picks are in (a) and (b).


## How to read this

- **Version, release date and license** in every table come from live registry queries made on 2026-11-12: the npm registry (`https://registry.npmjs.org/<package>`, human page `https://www.npmjs.com/package/<package>`), PyPI (`https://pypi.org/pypi/<package>/json`, human page `https://pypi.org/project/<package>/`) and the GitHub releases API (`https://api.github.com/repos/<owner>/<repo>/releases/latest`). The date is the publish date of the `latest` tag. Peer-dependency ranges quoted below come from the same registry records.
- **"Free for private repo"** is "yes" for every locally run open-source tool unless stated. Hosted services are called out.
- **Run cost** figures are rough estimates for a small project (tens of files). They were not measured here.
- **Network**: "no" means the tool runs offline once installed. Installation itself always needs the registry.
- Claims marked **unverified** were not confirmed against a primary source in this pass. Section (d) at the end collects them.

## Two stack findings that change the recommendations

1. **TypeScript 7.0 ships without a programmatic API.** Microsoft's announcement says "While TypeScript 7.0 is here, it does not ship with an API" and "We expect TypeScript 7.1 to ship with a new (and different) API". It recommends running side by side with TypeScript 6 through the `@typescript/typescript6` package and npm aliases. Source: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/. TypeScript 7.1 is in beta (announced 2026-10-20, stable tentatively late November 2026): https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/, https://infoq.com/news/2026/11/typescript-7-1-beta.
2. **typescript-eslint does not support TypeScript 7.** `typescript-eslint` 8.72.2 (2026-11-09) declares peer `typescript: >=4.8.4 <6.1.0`. The maintainers closed the support request with "typescript-eslint isn't compatible with TS 7 at this time, because there is no TS 7 API at this time": https://github.com/typescript-eslint/typescript-eslint/issues/12518 (tracked in #10940). Any tool that imports the `typescript` package API is in the same position: typedoc (peer up to `6.0.x`), madge (peer `^5.4.4`), ts-prune, ts-unused-exports, dependency-cruiser's TypeScript parsing (its 18.1.0 notes say 7.1.0 is the first 7.x it expects to support: https://newreleases.io/project/npm/dependency-cruiser/release/18.1.0), Stryker's typescript-checker. Tools that bundle their own TypeScript (api-extractor bundles 6.0.3, eslint-plugin-sonarjs depends on `>=5 <6.1.0`, @arethetypeswrong/core bundles 5.6) or do not use it (knip 6 uses oxc-parser, oxlint, Biome, jscpd, fta) are unaffected.

Consequence for the consumer's stack (ESLint 10 + typescript-eslint 8 + TypeScript 7): the ESLint side must already be resolving `typescript` to a 6.x build (alias), or typed linting is not actually running. Every "type-aware ESLint rule" recommendation below needs either that alias or the oxlint type-aware engine, which is built on TypeScript 7.

---

## 1. Lint rule sets beyond "recommended"

### 1a. typescript-eslint presets and type-aware rules (TS/JS)

| Tool | What it catches | License | Latest (date) | Stack notes | Cost | Network |
|---|---|---|---|---|---|---|
| typescript-eslint `strictTypeChecked` + `stylisticTypeChecked` | Unawaited promises (`no-floating-promises`, `no-misused-promises`, `await-thenable`, `require-await`), unsafe `any` flow (`no-unsafe-assignment/call/member-access/return/argument`), non-exhaustive switches (`switch-exhaustiveness-check`), dead conditions (`no-unnecessary-condition`), `only-throw-error`, `restrict-template-expressions`, `no-base-to-string`, `no-confusing-void-expression`, `prefer-nullish-coalescing` | MIT | 8.72.2 (2026-11-09) | Flat config, ESLint `^8.57 \|\| ^9 \|\| ^10`. **TypeScript peer `<6.1.0`: needs TS 6 alias on a TS 7 project.** Typed rules need `parserOptions.projectService`. | Typed lint roughly doubles to 10x lint time; seconds on a small repo | no |
| ESLint core options | `linterOptions.reportUnusedDisableDirectives`, `reportUnusedInlineConfigs`; core rules `no-await-in-loop`, `no-promise-executor-return`, `require-atomic-updates` (race-prone assignments after `await`), `no-constructor-return`, `no-unreachable-loop`, `eqeqeq`, `no-param-reassign` | MIT | eslint 10.14.0 (2026-10-30) | Native | none extra | no |

Preset names and rule names are from typescript-eslint's documentation (https://typescript-eslint.io/users/configs/); the rule list was not re-fetched in this pass.

### 1b. ESLint plugins worth considering (TS/JS)

All confirmed present on npm on 2026-11-12. "E10" = peer range includes ESLint 10.

| Plugin | What it adds | License | Latest (date) | ESLint 10 / TS notes |
|---|---|---|---|---|
| eslint-plugin-sonarjs | Bug and code-smell rules from SonarJS: cognitive complexity, identical branches, duplicated strings, collapsible ifs, weak crypto, etc. | LGPL-3.0-only | 4.2.2 (2026-09-28) | E10 yes. Bundles its own `typescript >=5 <6.1.0`, so not blocked by TS 7. |
| eslint-plugin-unicorn | 100+ opinionated correctness and modernisation rules (`prefer-node-protocol`, `no-array-for-each`, `error-message`, `no-useless-undefined`, `prefer-top-level-await`) | MIT | 79.0.0 (2026-10-23) | Requires ESLint `>=10.4`, Node `>=22`. |
| eslint-plugin-promise | Promise hygiene without type info (`catch-or-return`, `no-nesting`, `param-names`, `no-return-wrap`) | ISC | 7.3.0 (2026-04-27) | E10 yes. Largely superseded by typed rules when those run. |
| eslint-plugin-n | Node rules: unsupported Node APIs for the `engines` range, missing/extraneous imports, deprecated APIs, `no-process-exit`, `prefer-node-protocol` | MIT | 18.5.0 (2026-10-18) | ESLint `>=8.57.1`; TS peer `>=5.0.0`. |
| eslint-plugin-regexp | Regex correctness and ReDoS-prone patterns (`no-super-linear-backtracking`, `no-dupe-disjunctions`) | MIT | 3.3.3 (2026-11-01) | ESLint `>=9.38`. |
| eslint-plugin-security | Node security heuristics (non-literal `fs` paths, `child_process`, `eval`, object injection, timing attacks). Noisy. | Apache-2.0 | 4.2.1 (2026-10-30) | No peer declared; maintained by eslint-community. |
| eslint-plugin-no-unsanitized | `innerHTML`, `insertAdjacentHTML`, `document.write` with unsanitised input (DOM XSS) | MPL-2.0 | 4.1.5 (2026-02-19) | ESLint `^9 \|\| ^10`. Relevant to a plain HTML/JS page. |
| eslint-plugin-import-x | Import correctness and structure: `no-cycle`, `no-unresolved`, `no-extraneous-dependencies`, `no-duplicates`, `no-self-import`, `no-restricted-paths` | MIT | 4.18.1 (2026-11-09) | E10 yes. |
| eslint-plugin-import | Same family, original | MIT | 2.32.0 (2025-06-20) | Peer stops at ESLint `^9`: **not ESLint 10**. |
| eslint-plugin-jsdoc | JSDoc presence and correctness (`require-jsdoc`, `check-param-names`, `informative-docs`) | BSD-3-Clause | 65.4.5 (2026-11-06) | E10 yes. Node `^22.22.2 \|\| >=24.15.0`. |
| @eslint-community/eslint-plugin-eslint-comments | `eslint-disable` hygiene: `require-description`, `no-unlimited-disable`, `no-unused-disable` | MIT | 4.8.1 (2026-09-12) | E10 yes. |
| eslint-plugin-no-secrets | High-entropy strings and known token patterns in source | MIT | 2.3.3 (2026-03-01) | ESLint `>=5`. |
| eslint-plugin-perfectionist | Deterministic sorting (imports, object keys, union members); autofix | MIT | 5.13.0 (2026-10-20) | E10 yes. |
| eslint-plugin-functional | Immutability and no-mutation rules; typed | MIT | 10.0.1 (2026-09-16) | ESLint `^9 \|\| ^10`; needs type info (TS 6 alias). |
| eslint-plugin-erasable-syntax-only | Flags enums, namespaces, parameter properties, i.e. syntax Node type stripping cannot run | MIT | 0.7.2 (2026-09-20) | ESLint `>=9`. Overlaps `erasableSyntaxOnly` in tsconfig. |
| eslint-plugin-de-morgan, eslint-plugin-depend, @stylistic/eslint-plugin, eslint-plugin-unused-imports, eslint-plugin-no-barrel-files, eslint-plugin-check-file | Boolean simplification; bloated/replaceable dependencies; formatting rules removed from core; autofix unused imports; barrel files; file naming | MIT / ISC / Apache-2.0 | 2.3.0 (2026-10-23); 1.5.0 (2026-03-03); 5.10.0 (2026-03-06); 4.4.1 (2026-02-09); 2.3.0 (2026-10-20); 3.3.2 (2026-07-18) | All accept ESLint 9 or 10 by peer range. |
| eslint-plugin-no-only-tests | Committed `.only` in tests | MIT | 3.4.0 (2026-04-29) | Runner-agnostic; works for `node:test` `it.only`/`{ only: true }` patterns by name match (unverified for the options form). |
| @eslint/json, @eslint/markdown, @eslint/css, eslint-plugin-yml, eslint-plugin-jsonc, eslint-plugin-package-json, @html-eslint/eslint-plugin | Lint JSON, Markdown, CSS, YAML, package.json and HTML inside the same ESLint run | Apache-2.0 / MIT | 2.1.1 (2026-10-06); 8.0.3 (2026-07-01); 2.0.1 (2026-10-15); 3.10.0 (2026-11-04); 3.4.2 (2026-08-22); 1.14.0 (2026-11-03); 0.68.0 (2026-11-07) | All flat-config native. Lets one ESLint run cover non-JS files without a second tool. |

Overlaps:
- **import vs import-x**: pick import-x; import has not released since 2025-06 and does not declare ESLint 10.
- **promise vs typed rules**: when `no-floating-promises`/`no-misused-promises` run, eslint-plugin-promise adds little.
- **sonarjs vs unicorn**: they barely overlap; sonarjs is bug/smell-oriented, unicorn is style/modernisation. If only one, sonarjs gives more review-relevant findings.
- **security vs Semgrep**: eslint-plugin-security is cheap but noisy; Semgrep/Opengrep rules are more precise. Keep `no-unsanitized` either way.

Ready-made strict bundles, for reference: `eslint-config-love` 158.0.0 (2026-10-02, ESLint `^10`), `neostandard` 0.14.1 (2026-10-13), `@antfu/eslint-config` 10.0.0 (2026-10-23), `eslint-config-xo` 7.0.0 (2026-10-23, TS `>=6`).

### 1c. Newer fast linters

| Tool | What it covers | License | Latest (date) | Versus ESLint | Network |
|---|---|---|---|---|---|
| oxlint (+ `oxlint-tsgolint`) | Rust linter with ports of ESLint core, typescript-eslint, unicorn, import, jsdoc, promise, n, and more. **Type-aware mode is stable since 2026-07-22**: `oxlint --type-aware` with `oxlint-tsgolint@7`, built on TypeScript 7.0.2; 59 of typescript-eslint's 61 type-aware rules; `--type-check` also reports compiler diagnostics from the same program. Benchmarks claim 12 to 18x faster than ESLint + typescript-eslint. | MIT | oxlint 1.93.0 (2026-11-09); oxlint-tsgolint 7.0.2007 (2026-11-12) | Covers: speed, and typed linting on TS 7 today. Lacks: full ESLint plugin ecosystem (sonarjs, regexp, boundaries, custom rules in JS are limited), and the two unported typed rules. `eslint-plugin-oxlint` (1.93.0) turns off the ESLint rules oxlint already runs so both can coexist. | no |
| Biome | Formatter + linter in one binary for JS/TS/JSON/CSS (HTML support is newer). Has its own Rust type inference, so some type-aware rules (`noFloatingPromises`) run without the TypeScript compiler. | MIT OR Apache-2.0 | 2.6.7 (2026-11-11) | Covers: one tool for format + lint, very fast, `--changed`/`--staged` modes. Lacks: its type inference is a subset of TypeScript's (maintainers say so; known false negatives), `noFloatingPromises` is listed in the nursery group on the rule page, no ESLint plugin ecosystem. | no |
| deno lint | Deno's built-in linter, usable on plain JS/TS files | MIT | deno 2.9.8 (2026-10-21) | Covers roughly ESLint + typescript-eslint "recommended". No type-aware rules (Deno's docs point to typescript-eslint for that); plugin API sees one file at a time. Needs the Deno binary. Not worth adding to a Node project. | no |
| Others seen | `@rslint/core` 0.10.1 (2026-11-10, a typescript-go based linter), `quick-lint-js` 3.2.0 (2024-03-04, stale) | MIT / GPL-3.0 | as stated | Not evaluated (unverified). | no |

Sources: https://oxc.rs/blog/2026-07-22-type-aware-linting-stable, https://oxc.rs/docs/guide/usage/linter/type-aware.html, https://biomejs.dev/blog/vercel-partners-biome-type-inference, https://next.biomejs.dev/linter/rules/no-floating-promises, https://docs.deno.com/runtime/lint_and_format/.

Pick: keep ESLint as the rule host (plugins, suppressions file, custom rules). For typed rules on a TS 7 project, **oxlint `--type-aware` is the only engine built on TS 7 today**; the alternative is ESLint typed linting through the TS 6 alias. Biome's typed rules are not a substitute yet.

### 1d. Python equivalents

| Tool | What it catches | License | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|
| Ruff (extended rule selection) | Re-implements flake8-bugbear (`B`), bandit (`S`), simplify (`SIM`), pyupgrade (`UP`), pylint subsets (`PL`), mccabe (`C90`), pytest-style (`PT`), async (`ASYNC`), unused arguments (`ARG`), commented-out code (`ERA`), pydocstyle (`D`), print statements (`T20`), `RUF`. Also formats. | MIT | 0.17.5 (2026-11-12) | Default selection is only `E4, E7, E9, F`; everything above is opt-in. | under 1 s | no |
| Pylint | Deeper cross-module inference checks, design metrics (`R09xx`), duplicate code | GPL-2.0-or-later | 4.1.3 (2026-10-11) | Slow; use for what Ruff lacks. | tens of seconds | no |
| flake8 + flake8-bugbear, wemake-python-styleguide | Legacy plugin ecosystem; wemake is the strictest ruleset | MIT | 7.5.0 (2026-10-28); 26.11.9 (2026-11-09); 1.8.1 (2026-09-12) | Ruff covers most. | seconds | no |
| mypy / pyright / basedpyright | Type checking; basedpyright adds stricter defaults and a baseline file | MIT | mypy 2.4.1 (2026-10-28); pyright 1.1.414 (2026-09-10); basedpyright 1.40.2 (2026-10-04) | See section 6. | seconds | no |
| ty, pyrefly | New Rust type checkers (Astral, Meta) | MIT | ty 0.0.101 (2026-11-11); pyrefly 1.4.1 (2026-11-05) | ty is still 0.0.x. | sub-second | no |

Pick: Ruff with a wide `select`, plus one type checker. Add Pylint only for `duplicate-code` and design checks.

---

## 2. Complexity and maintainability metrics

| Tool | What it reports | Ecosystem | License | Latest (date) | Reports or fails | Stack notes | Cost | Network |
|---|---|---|---|---|---|---|---|---|
| ESLint core rules `complexity`, `max-depth`, `max-lines`, `max-lines-per-function`, `max-params`, `max-statements`, `max-nested-callbacks` | Cyclomatic complexity, nesting, length, parameter count | TS/JS | MIT | eslint 10.14.0 | Fails by default. To report only: set to `warn` and read `--format json`. | Native. `complexity` has a `variant: "modified"` option. | none extra | no |
| `sonarjs/cognitive-complexity` (eslint-plugin-sonarjs) | Cognitive complexity per function | TS/JS | LGPL-3.0-only | 4.2.2 (2026-09-28) | Same as above | ESLint 10 ok | none extra | no |
| fta-cli (Fast TypeScript Analyzer) | Per-file score combining cyclomatic complexity, Halstead metrics and line count; JSON output; `--score-cap` to fail | TS/JS | MIT | 3.1.0 (2026-10-07) | Both | Rust + SWC parser; does not use the `typescript` package | under 1 s | no |
| eslintcc | Ranks files/functions A to F from ESLint complexity rules | TS/JS | MIT | 0.8.3 (2024-06-07) | Report | Stale (2024); ESLint 10 unverified | seconds | no |
| cognitive-complexity-ts | Cognitive complexity report as JSON/HTML | TS | GPL-3.0 | 0.8.2 (2026-05-22) | Report | Uses the TypeScript API (TS 7 unverified) | seconds | no |
| complexity-report, plato, typhonjs-escomplex, ts-complex | Older maintainability-index tools | JS | MIT/MPL | 2016 to 2018 | Report | **Dead.** Do not use. | n/a | no |
| radon / xenon | Cyclomatic complexity, maintainability index, Halstead, raw LOC; xenon fails on thresholds | Python | MIT | radon 6.0.1 (2023-03-26); xenon 0.9.3 (2024-10-21) | radon reports, xenon fails | Low activity but works | under 1 s | no |
| complexipy | Cognitive complexity (Rust) | Python | MIT | 8.3.0 (2026-10-27) | Both | Active | under 1 s | no |
| Ruff `C901`, `PLR0911/0912/0913/0915/0917`, `PLR1702` | McCabe complexity, too many returns/branches/arguments/statements/nesting | Python | MIT | 0.17.5 | Fails (or baseline) | Already in Ruff | none extra | no |
| wily | Tracks complexity metrics across git history | Python | Apache | 1.25.0 (2023-10-11) | Report | Stale | seconds | no |
| lizard | Cyclomatic complexity, function length, parameter count for ~20 languages including TypeScript, JavaScript and Python; warnings list or XML/CSV | Agnostic | MIT | 1.26.0 (2026-11-10) | Both (`-C`, `-L`, `-a` thresholds; `-w` warnings only) | Own tokenizer, no compiler dependency | under 1 s | no |
| scc | Line counts plus a rough complexity estimate per file and language | Agnostic | MIT | v4.1.0 (2026-09-07) | Report | Single Go binary | under 1 s | no |
| SonarQube | Cognitive/cyclomatic complexity, maintainability rating | Agnostic | see section 13 | | Both | Needs a server | minutes | yes (server) |

Pick: ESLint core rules plus `sonarjs/cognitive-complexity` for gating in TS (no new process). For a stack-neutral **report**, lizard is the one tool that covers TS and Python with the same thresholds; fta is the best maintained TS-only reporter. There is no maintained maintainability-index tool for TypeScript; fta's score is the closest.

---

## 3. Duplication / copy-paste detection

| Tool | What it catches | Ecosystem | License | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| jscpd | Token-based clone detection across 150+ formats; `--threshold` percent gate; JSON/HTML/SARIF reports; `--min-tokens`, `--min-lines` | Agnostic (Node CLI) | MIT | 5.4.3 (2026-11-08) | Own tokenizer; no TypeScript dependency. Works on TS, JS, Python, CSS, HTML, Markdown. | seconds | no |
| `sonarjs/no-identical-functions`, `sonarjs/no-duplicate-string`, `sonarjs/no-all-duplicated-branches` | Small-scale duplication inside a file | TS/JS | LGPL-3.0-only | 4.2.2 | In ESLint | none extra | no |
| Pylint `duplicate-code` (R0801) | Similar lines across Python modules | Python | GPL-2.0-or-later | 4.1.3 | `--disable=all --enable=duplicate-code` | seconds | no |
| PMD CPD | Token-based clone detection, many languages including TypeScript, JavaScript and Python | Agnostic (JVM) | BSD-style | 7.29.0 (2026-10-30) | Needs Java | seconds | no |
| SonarQube duplication | Duplicated blocks and density on new code | Agnostic | section 13 | | Server | minutes | yes |

Pick: jscpd. It is one process for every language the plugin sees and has a percentage threshold and a machine-readable report; PMD CPD adds a JVM for the same result.

---

## 4. Dead code

| Tool | What it catches | Ecosystem | License | Latest (date) | Stack notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| knip | Unused files, exports, exported types, enum members, dependencies, devDependencies, unlisted dependencies, unresolved imports, duplicate exports. JSON reporter, `--production` mode, plugins for ~100 tools. | TS/JS | ISC | 6.45.1 (2026-11-11) | v6 parses with `oxc-parser` and resolves with `oxc-resolver`, so it does not need the TypeScript API. v6 removed the `classMembers` issue type. https://knip.dev/blog/knip-v6 | 1 to 5 s | no |
| ts-prune | Unused exports | TS | MIT | 0.10.3 (2021-12-12) | Maintenance mode; README points to knip. Do not adopt. | | no |
| unimported, depcheck, tsr | Unused files / dependencies / exports | TS/JS | MIT/Apache | 2023 to 2025 | **All three repositories are archived** (GitHub API, 2026-11-12). | | no |
| ts-unused-exports | Unused exports | TS | MIT | 11.0.1 (2024-11-25) | Uses the TypeScript API; stale. | | no |
| TypeScript `noUnusedLocals`, `noUnusedParameters`; `@typescript-eslint/no-unused-vars`; `no-unused-private-class-members` (core) | Unused locals, parameters, private members inside a file | TS | Apache / MIT | | Already available | none extra | no |
| eslint-plugin-depend, `@e18e/cli` | Dependencies with lighter or native replacements | TS/JS | MIT | 1.5.0 (2026-03-03); 0.7.0 (2026-06-01) | Advisory | seconds | no |
| vulture | Unused functions, classes, variables, imports, unreachable code; confidence score; whitelist file | Python | MIT | 2.16 (2026-03-25) | | under 1 s | no |
| deadcode | Same goal, with `--fix` | Python | AGPL-3.0 | 2.6.1 (2026-11-11) | License may matter for some users | under 1 s | no |
| deptry | Unused, missing, transitive and misplaced dependencies against `pyproject.toml` | Python | MIT | 0.25.1 (2026-03-18) | | under 1 s | no |
| fawltydeps, creosote, unimport | Undeclared/unused deps; unused deps; unused imports | Python | MIT | 0.20.0 (2025-06-05); 5.2.0 (2026-03-28); 1.5.0 (2026-10-02) | Overlap deptry and Ruff `F401` | under 1 s | no |
| Ruff `F401`, `F811`, `F841`, `ERA001`, `ARG` | Unused imports, redefinitions, unused locals, commented-out code, unused arguments | Python | MIT | 0.17.5 | | none extra | no |

Pick: knip for TS (the only maintained whole-project tool, and independent of the TS 7 API gap); vulture + deptry for Python. No maintained deterministic tool finds unused **public class members** in TS now that knip dropped it.

---

## 5. Architecture and dependency rules

| Tool | What it enforces | Ecosystem | License | Latest (date) | Graph output | Stack notes | Cost | Network |
|---|---|---|---|---|---|---|---|---|
| dependency-cruiser | Forbidden/allowed/required dependency rules by path regex, cycles, orphans, dev-dependency use in production code, reachability; baseline file for known violations | TS/JS | MIT | 18.7.2 (2026-11-02) | DOT, Mermaid, JSON, HTML, metrics (instability) | Parses TS through the installed `typescript` package. **Its 18.1.0 notes say TypeScript 7.1.0 will be the first 7.x it supports**, so on TS 7.0 it needs TS 6 resolvable (alias). Node `^22\|\|^24\|\|>=26`. | 1 to 5 s | no |
| eslint-plugin-boundaries | Element types by folder, allowed import directions between them, private files, entry points | TS/JS | MIT | 7.4.3 (2026-11-12) | No | Peer `eslint >=6`; works at the import-statement level, so no TypeScript API dependency of its own | none extra | no |
| eslint-plugin-import-x `no-cycle`, `no-restricted-paths`, `no-internal-modules`; core `no-restricted-imports` | Cycles, zone restrictions, forbidden modules | TS/JS | MIT | 4.18.1 (2026-11-09) | No | ESLint 10 ok. `no-cycle` is the slowest import rule. | seconds | no |
| madge | Cycles, orphans, graph image | TS/JS | MIT | 8.0.0 (2024-08-05) | DOT/SVG (needs Graphviz for images) | Stale; TS peer `^5.4.4` | seconds | no |
| skott | Graph, cycles, unused files/deps, web viewer | TS/JS | MIT | 0.35.12 (2026-09-11) | JSON, Mermaid, web app | Depends on `typescript ^5.9` and typescript-estree itself | seconds | no |
| dpdm | Circular dependency detector | TS/JS | MIT | 4.3.0 (2026-07-29) | Tree/JSON | Uses TypeScript API (TS 7 unverified) | seconds | no |
| archunit (TS), arch-unit-ts, tsarch | Architecture assertions written as unit tests (layers, cycles, naming, metrics) | TS | MIT / Apache-2.0 | archunit 2.5.4 (2026-09-13); arch-unit-ts 1.0.12 (2026-07-03); tsarch 5.4.1 (2024-12-23) | PlantUML checks (tsarch) | Runner compatibility with `node:test` unverified | scales with project size | no |
| `@softarc/sheriff-core`, eslint-plugin-project-structure, steiger, good-fences | Module boundary and folder-structure rules | TS | MIT | 0.20.0 (2026-09-29); 3.14.6 (2026-11-05); 0.10.0 (2026-11-09); good-fences 1.2.0 (2023-03-07, stale) | No | Niche; steiger is Feature-Sliced-Design specific | seconds | no |
| `@nx/enforce-module-boundaries` | Tag-based boundaries | TS (Nx workspaces) | MIT | @nx/eslint-plugin 24.0.6 (2026-11-10) | Nx graph | Requires Nx | | no |
| import-linter | Contracts: layers, forbidden, independence, acyclic siblings | Python | BSD-2-Clause | 2.16 (2026-11-06) | Via grimp | Active | 1 to 5 s | no |
| tach | Module boundaries and public interfaces, dependency graph, Rust core | Python | MIT | 0.35.3 (2026-10-06) | DOT/Mermaid, web | Active | under 1 s | no |
| pytestarch | Architecture rules as pytest tests | Python | Apache-2.0 | 5.1.1 (2026-11-08) | Matplotlib graph | Active | seconds | no |
| pydeps, grimp | Graph images; import graph library | Python | BSD-2-Clause | 3.0.9 (2026-10-01); 3.19 (2026-11-06) | SVG (Graphviz) / API | Active | seconds | no |
| pycycle | Cycles | Python | MIT | 0.0.8 (2017) | | Dead | | no |

Pick (TS): dependency-cruiser is the stronger tool (rules + graph + baseline in one), but it is blocked on the TS 7 API until 7.1 unless TS 6 is aliased; eslint-plugin-boundaries plus `import-x/no-cycle` runs inside the existing ESLint pass with no such dependency. Use boundaries now, dependency-cruiser for the graph once 7.1 support lands. Pick (Python): import-linter for contracts; tach if a graph and interface enforcement are wanted in one tool.

---

## 6. Type-system strictness

### Compiler flags beyond `strict` (TypeScript)

TypeScript 7 changed defaults: `strict` is now on by default, `noUncheckedSideEffectImports` is on, `types` defaults to `[]`, `module` defaults to `esnext` (https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/). Flags still off by default that are worth enabling (names from the TSConfig reference, https://www.typescriptlang.org/tsconfig/; not re-fetched in this pass):

| Flag | What it catches |
|---|---|
| `noUncheckedIndexedAccess` | `arr[i]` and `record[key]` typed as possibly `undefined` |
| `exactOptionalPropertyTypes` | Assigning `undefined` to an optional property that did not declare it |
| `noImplicitOverride` | Overriding a base member without `override` |
| `noImplicitReturns` | Code paths that fall off the end of a function |
| `noFallthroughCasesInSwitch` | Switch case fallthrough |
| `noPropertyAccessFromIndexSignature` | Dot access on index-signature keys (typo guard) |
| `noUnusedLocals`, `noUnusedParameters` | Unused declarations |
| `allowUnreachableCode: false`, `allowUnusedLabels: false` | Unreachable code and stray labels as errors |
| `erasableSyntaxOnly` | Enums, namespaces, parameter properties, i.e. syntax Node type stripping cannot execute |
| `verbatimModuleSyntax` | Type imports must be written as `import type`; needed for type stripping and ESM correctness |
| `isolatedModules`, `isolatedDeclarations` | Per-file transpile safety; explicit types on exports |

Cost: zero new dependencies; part of the existing typecheck.

### Tools

| Tool | What it measures or checks | Ecosystem | License | Latest (date) | Stack notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| type-coverage | Percentage of identifiers whose type is not `any`; `--at-least`, `--strict`, `--detail` | TS | MIT | 2.31.2 (2026-11-04) | `type-coverage-core` peer lists `typescript: 2 \|\| 3 \|\| 4 \|\| 5 \|\| 6 \|\| 7`, but TS 7.0 has no API; whether it really runs on 7.0 is **unverified** | seconds | no |
| typescript-coverage-report | HTML report on top of type-coverage | TS | MIT | 2.1.2 (2026-09-28) | Peer `typescript: 2..6` (no 7) | seconds | no |
| `@typescript-eslint/no-explicit-any`, `no-unsafe-*` | Same goal as a gate rather than a percentage | TS | MIT | 8.72.2 | TS 6 alias or oxlint type-aware | none extra | no |
| @microsoft/api-extractor | API report file (`*.api.md`) checked into git so any public-surface change shows in the diff; d.ts rollup; missing release tags | TS | MIT | 7.60.1 (2026-10-30) | Bundles `typescript 6.0.3`, so runs regardless of the project compiler; analyses emitted `.d.ts` | 5 to 20 s | no |
| publint | package.json `exports`/`main`/`types`/`files` mistakes | TS/JS | MIT | 0.3.25 (2026-10-01) | Only relevant to a published package | under 1 s | no |
| @arethetypeswrong/cli | Whether published types resolve under every module-resolution mode | TS/JS | MIT | 0.18.5 (2026-07-09) | Bundles its own TypeScript; only for published packages | seconds | no |
| tsd, expect-type, tstyche | Tests for types | TS | MIT / Apache-2.0 | tsd 0.33.0 (2025-08-05); expect-type 1.4.0 (2026-06-25); tstyche 7.2.5 (2026-09-10) | expect-type is compile-time only (works with any compiler) | seconds | no |
| mypy `--strict` | Strict typing gate; `--html-report`/`--linecount-report` for typed-line coverage; `disallow_any_*` | Python | MIT | 2.4.1 (2026-10-28) | | seconds | no |
| pyright / basedpyright strict | `typeCheckingMode: strict`; `--verifytypes <pkg>` reports public-API type completeness; basedpyright adds `reportAny` and a baseline file | Python | MIT | 1.1.414 (2026-09-10); 1.40.2 (2026-10-04) | pyright's PyPI wrapper downloads Node on first run | seconds | no after first run |
| griffe (`griffe check`) | Breaking changes in a Python package's public API between two git refs | Python | ISC | 2.4.1 (2026-10-22) | | seconds | no |
| pyroma, validate-pyproject, check-manifest, twine check | Packaging metadata checks | Python | MIT / MPL | 5.0.1 (2025-12-09); 0.27 (2026-10-22); 0.51 (2025-10-15); 7.0.0 (2026-07-27) | Python analogue of publint | under 1 s | no |

Pick: compiler flags first (free). type-coverage only if a number is wanted for the report; the `no-unsafe-*` rules are the stronger gate. api-extractor only when a package has a public surface; for an application, knip's unused-export report is the cheaper signal.

---

## 7. Test quality

### Mutation testing

| Tool | What it catches | Ecosystem | License | Latest (date) | Stack notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| StrykerJS (`@stryker-mutator/core`) + `@stryker-mutator/tap-runner` | Tests that pass when the code is wrong (surviving mutants) | TS/JS | Apache-2.0 | 10.1.1 (2026-10-23), Node `>=22` | See below | Scales with (mutants x per-file test time); minutes to hours | no |
| mutmut | Same | Python | BSD-3-Clause | 3.8.1 (2026-10-28) | Active; pytest | Minutes to hours | no |
| cosmic-ray | Same, with distributed workers and operator filters | Python | MIT-style | 8.9.0 (2026-11-10) | Active | Minutes to hours | no |
| poodle | Same, newer | Python | MIT | 1.4.0 (2026-10-31) | Active | Minutes to hours | no |
| mutatest, pytest-mutagen | Same | Python | MIT | 2022; 2020 | Dead | | no |

**Stryker and `node --test`:** there is **no dedicated node:test runner package** (`@stryker-mutator/node-test-runner` returns 404 on npm). The supported route is the **TAP runner**, whose docs name "the build-in node test runner" as a source of TAP output; since v9 its default `nodeArgs` are `["--test-reporter=tap", "-r", "{{hookFile}}", "{{testFile}}"]`. Limits stated in the docs: a "test" is always a whole test file, each test file runs in its own process, coverage is recorded per test file, static mutants cannot be detected, and you must handle TypeScript yourself (examples use `--import tsx` or a `buildCommand`). Source: https://stryker-mutator.io/docs/stryker-js/tap-runner/. The generic command runner also works with any test command but gives no per-test information.

**Stryker and type stripping:** the docs do not mention Node's built-in type stripping. In principle the TAP runner just spawns `node` on each test file, and Node 24 strips types by default, so `.ts` tests should run with no loader; Stryker's instrumenter mutates `.ts` sources in a sandbox copy. This combination is **unverified**; no issue or doc confirming or denying it was found. Risks to test: the sandbox copy must keep relative `.ts` import specifiers working, and instrumented code must stay erasable-syntax-only.

**Stryker and TypeScript 7:** `@stryker-mutator/typescript-checker` (peer `typescript >=3.6`) uses the compiler API to discard mutants that do not type-check; with no API in 7.0 it needs TS 6 resolvable. Without the checker Stryker still works; type-invalid mutants then show as killed or runtime errors and cost time. Unverified in practice.

**Incremental and changed-lines modes:** `--incremental` stores `reports/stryker-incremental.json` and reuses a mutant's result when neither the mutant nor the tests covering it changed; with the TAP runner any change in a test file invalidates all tests in that file. There is no git-diff (`--since`) mode, but `--mutate` accepts line ranges (`--mutate src/app.js:5-7`), so a wrapper can pass the changed files/lines from `git diff`. Source: https://stryker-mutator.io/docs/stryker-js/incremental/.

Alternatives for JS: none maintained that matter. Stryker is the only serious JS mutation tool.

### Property-based testing, flake detection, test smells

| Tool | What it catches | Ecosystem | License | Latest (date) | Stack notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| fast-check | Counterexamples found by generated inputs, with shrinking and a replayable seed; model-based testing; async `scheduler` for interleavings | TS/JS | MIT | 4.10.2 (2026-09-19) | Runner-agnostic: `fc.assert` inside a `node:test` test | Scales with `numRuns` (default 100) | no |
| Hypothesis | Same; stateful testing; example database | Python | MPL-2.0 | 6.170.15 (2026-11-06) | pytest | Scales with examples | no |
| `node --test-randomize` / `--test-random-seed` | Order-dependent tests (shared state). Prints the seed. Added in v24.16.0. Cannot combine with `--watch` or `--test-rerun-failures`. | Node | MIT | Node 24.22.3 docs | Built in | Same as a test run | no |
| `node --test-rerun-failures <file>` | Re-runs only failed tests using a state file (v24.7.0). Useful to detect flakes: a test that passes on rerun is flaky. | Node | | | Built in | | no |
| Repeated runs | No `--repeat` flag in the `node --test` CLI flag list. Loop the command N times in the gate script, with different seeds. | Node | | | | N x suite time | no |
| pytest-randomly, pytest-random-order | Random test order with a seed | Python | MIT | 5.1.0 (2026-11-08); 1.2.0 (2025-06-22) | | none | no |
| pytest-repeat, pytest-flakefinder, pytest-rerunfailures, flaky | Repeat N times; rerun on failure | Python | MPL / Apache | 0.9.4 (2025-04-07); 1.1.0 (2022); 16.7 (2026-09-17); 3.8.1 (2024) | | N x suite time | no |
| eslint-plugin-no-only-tests | Committed `.only` | TS/JS | MIT | 3.4.0 (2026-04-29) | | none extra | no |
| eslint-plugin-node-test | Lint rules for `node:test` | TS/JS | MIT | 0.1.1 (2024-05-21) | Tiny, stale. There is **no maintained test-smell linter for `node:test`**; eslint-plugin-jest (29.17.0), @vitest/eslint-plugin (1.6.28) and eslint-plugin-mocha (12.0.2) are runner-specific. | | no |
| `no-restricted-syntax` / `no-restricted-properties` (core) | Hand-written bans: `test.skip`, `assert.ok(true)`, `setTimeout` in tests, `Math.random`, `Date.now` | TS/JS | MIT | | The practical substitute for a test-smell plugin on `node:test` | none extra | no |
| Ruff `PT` (flake8-pytest-style), pytest-deadfixtures | pytest style problems; unused fixtures | Python | MIT | 0.17.5; 4.0.0 (2026-10-29) | | none extra | no |

Node flag details: https://nodejs.org/docs/latest-v24.x/api/cli.html.

### Coverage

| Tool | What it adds | Ecosystem | License | Latest (date) | Stack notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| Node built-in coverage | `--experimental-test-coverage` with `--test-coverage-lines/branches/functions=<pct>` thresholds (added v22.8.0, still marked experimental), `--test-coverage-include/exclude` globs, `lcov` reporter | Node | MIT | Node 24 | Thresholds read as whole-run percentages; the docs describe no per-file threshold | small overhead | no |
| c8 | V8 coverage with `--check-coverage`, `--per-file`, `--100`, branch thresholds, all Istanbul reporters | TS/JS | ISC | 12.0.0 (2026-07-14) | Wraps any command: `c8 node --test`. Source-map handling with type-stripped `.ts` is fine in principle because stripping preserves positions (unverified). | small overhead | no |
| monocart-coverage-reports | V8 coverage reports with better branch/byte accuracy, merges, many formats | TS/JS | MIT | 3.2.1 (2026-11-08) | Node `>=22.15` | small | no |
| nyc | Istanbul instrumentation | JS | ISC | 18.0.0 (2026-02-22) | Needs instrumentation; c8 is simpler on Node | | no |
| diff-cover (`diff-cover`, `diff-quality`) | **Coverage of changed lines only**: compares a coverage report (Cobertura, Clover, JaCoCo XML, or **lcov**) with `git diff`; `--fail-under`. `diff-quality` does the same for linter violations. | Agnostic (Python CLI) | Apache-2.0 | 11.0.1 (2026-11-04) | Feed it Node's or c8's `lcov.info`. No confirmation found that Node's own lcov reporter output is accepted; lcov is a standard format (unverified). | under 1 s | no (needs git history) |
| JS-native diff coverage | `@connectis/diff-test-coverage` 1.5.3 (2019), `coverage-diff` 3.2.0 (2023), `diff-cover-js` (v0.1.0) | JS | MIT | stale or immature | Not recommended | | no |
| coverage.py + pytest-cov | Line and branch coverage (`--cov-branch`), `--cov-fail-under`, contexts (which test covered which line) | Python | Apache-2.0 / MIT | 7.17.3 (2026-11-12); 7.1.0 (2026-03-21) | | small | no |
| Codecov / Coveralls patch coverage | Hosted diff coverage on PRs | Agnostic | SaaS | | Needs account, upload, network | | yes |

Pick: keep the built-in thresholds and add **diff-cover** on the lcov output for changed-lines coverage (the plugin already ships Python, and the same tool then serves Python projects). Add c8 only if per-file thresholds are wanted.

### Snapshot and contract testing

| Tool | What it does | Ecosystem | License | Latest (date) | Notes | Network |
|---|---|---|---|---|---|---|
| `node:test` snapshots (`t.assert.snapshot`, `--test-update-snapshots`) | Snapshot assertions; non-experimental since v23.4.0 / v22.13.0 | Node | MIT | built in | | no |
| syrupy, inline-snapshot | Snapshot testing for pytest | Python | MIT | 7.0.0 (2026-11-11); 0.36.2 (2026-11-09) | | no |
| Pact (`@pact-foundation/pact`, `pact-python`) | Consumer-driven contract tests | Both | MIT | 17.1.4 (2026-09-07); 4.2.0 (2026-10-23) | Only meaningful with two services; a broker is optional | no (local files) |
| Schemathesis | Property-based tests generated from an OpenAPI/GraphQL schema | Agnostic (Python CLI) | MIT | 4.33.4 (2026-11-12) | Needs the app running and a schema | local only |

---

## 8. Concurrency, races and resource leaks (Node)

| Tool / technique | What it catches | License | Latest (date) | Practicality | Cost | Network |
|---|---|---|---|---|---|---|
| Typed lint: `no-floating-promises`, `no-misused-promises`, `require-atomic-updates`, `no-await-in-loop`, `promise/catch-or-return` | The static part: promises nobody awaits, async callbacks where sync is expected, read-modify-write across an `await` | MIT | section 1 | **High.** Cheapest real win for async bugs. | lint time | no |
| Not using `--test-force-exit`, plus `--test-timeout` | A leaked handle (server, timer, socket) keeps the test process alive, so the run hangs and the timeout fails it. `--test-force-exit` hides exactly this. | Node | built in | **High.** A convention, not a tool. node:test has no `detectOpenHandles` equivalent. | none | no |
| why-is-node-running | Lists the handles keeping the process alive, with creation stacks (uses async_hooks) | MIT | 3.2.3 (2026-10-09) | **High** as a diagnostic: `node --import why-is-node-running/include --test`, then signal the hung process | negligible | no |
| wtfnode | Same idea | ISC | 0.10.1 (2025-10-05) | Works; less active | | no |
| `process.getActiveResourcesInfo()` assertion in a global teardown | Fails the run if handles remain after tests | Node | built in | Medium. Hand-written; needs an allow-list. Unverified pattern. | none | no |
| fast-check `fc.scheduler()` | Deterministic exploration of promise resolution orders for code that takes its async dependencies as parameters; failing order is shrunk and replayable | MIT | 4.10.2 | **Medium-high** for specific units (caches, queues, debounced saves, locks). Requires wrapping the async calls with the scheduler. https://fast-check.dev/docs/advanced/race-conditions/ | scales with runs | no |
| memlab | Heap-snapshot leak detection for browser pages and Node | MIT | 2.0.6 (2026-10-29) | Medium-low for a small local app; scenario files and Chromium | minutes | no |
| Heap growth test (`--expose-gc`, loop, compare `process.memoryUsage()`) | Gross memory leaks | Node | built in | Medium; flaky thresholds | seconds | no |
| Jazzer.js (`@jazzer.js/core`) | Coverage-guided fuzzing (libFuzzer) for parsers and decoders | Apache-2.0 | 4.0.0 (2026-04-15) | Medium for parsing/crypto file formats; native addon, ESM support limited (unverified) | open-ended (time-boxed) | no |
| clinic.js | Event-loop and I/O profiling | MIT | 13.0.0 (2023-06-28) | Stale | | no |
| leaked-handles | Handle leak printing | none | 5.2.0 (2015) | Dead | | no |
| Deterministic simulation packages: `determined` 0.4.1 (2026-07-30), `crashlab` 1.0.0 (2026-03-31), `simnodejs` 0.1.1-alpha (2026-03-24), `flake-monster` 0.4.6 (2026-02-22, seeded await-delay injection) | Virtual time, seeded scheduling, replayable interleavings | MIT | as stated | **Low**: all young, small user bases; not evaluated beyond existence (unverified) | | no |
| Research race detectors: NodeRacer, Node.fz, NodeRT (ISSTA 2023), delay-injection detector (ECOOP 2025) | Event races by schedule fuzzing or instrumentation | academic | n/a | **Not practical**: research prototypes, not packaged. https://github.com/andreendo/noderacer, https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2025.9 | | |
| Model checkers (TLA+, Alloy, P) | Design-level protocol errors | various | | Low for this scale; they check a model, not the code | | no |
| Python: `pytest-asyncio` debug mode / `PYTHONASYNCIODEBUG=1`, `-W error::ResourceWarning`, pyleak 0.2.0 (2026-01-29), pytest-timeout, Ruff `ASYNC`, pytest-memray 1.11.0 | Never-awaited coroutines, unclosed files/sockets, leaked tasks/threads, blocking calls in async code, memory limits per test | Apache / MIT | as stated | High for the warnings-as-errors settings (free) | none | no |

Summary: there is no ThreadSanitizer-like race detector for Node that is production-ready. The deterministic options that work are static (typed promise rules), structural (no force-exit, timeouts, randomised order) and targeted property tests with fast-check's scheduler.

---

## 9. Security

### SAST

| Tool | What it catches | Ecosystem | License / cost | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| Semgrep Community Edition | Pattern and intra-file taint rules for JS/TS, Python and ~30 languages; SARIF; `--baseline-commit` to report only new findings | Agnostic | Engine LGPL-2.1; Semgrep-maintained rules under the Semgrep Rules License v1.0 (internal use allowed; restricted for competing/SaaS use). Free, no login. | 1.185.0 (2026-11-10) | Cross-file taint is a paid (Pro) feature. Registry rule packs (`p/...`, `auto`) are fetched from the network; a vendored rules directory with `--metrics=off` runs offline (unverified in this pass). No native Windows binary historically; fine under WSL. https://semgrep.dev/docs/faq/comparisons/opengrep | 10 to 60 s | only to fetch rules |
| Opengrep | Fork of Semgrep CE that keeps taint and other features in the open engine | Agnostic | LGPL-2.1, free | v1.33.1 (2026-10-29) | Uses Semgrep-format rules; its own rules license not checked. https://github.com/opengrep/opengrep | 10 to 60 s | only to fetch rules |
| CodeQL | Deep data-flow queries (JS/TS, Python, Actions workflows) | Agnostic | **Free only for public repos / research.** Private repos need GitHub Code Security (reported at $30 per active committer per month). https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-cli | CLI v2.27.4 (2026-11-02) | Slow database build; not for a local sandbox gate | minutes | no for CLI; yes for Actions upload |
| eslint-plugin-security, eslint-plugin-no-unsanitized, @microsoft/eslint-plugin-sdl | Lint-level security rules | TS/JS | Apache / MPL / MIT | 4.2.1; 4.1.5; sdl 1.1.0 (2025-02-18, peer ESLint `^9` only) | Cheap, in ESLint | none extra | no |
| Bandit / Ruff `S` | Python security anti-patterns | Python | Apache-2.0 / MIT | bandit 1.9.4 (2026-02-25) | Ruff `S` re-implements most of Bandit | under 1 s | no |
| Pyre/Pysa | Python taint analysis | Python | MIT | pyre-check 0.10.0 (2026-08-06) | Heavy setup | minutes | no |
| Snyk Code, SonarQube, GitHub Code Quality | Hosted SAST | Agnostic | SaaS, accounts | snyk CLI 1.1308.4 (2026-11-04) | Network and account | | yes |

Pick: Opengrep or Semgrep CE with a vendored rule set; CodeQL only if the repository is public or already licensed.

### Secrets

| Tool | What it catches | License | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|
| gitleaks | Secrets in the working tree, staged diff, or git history; baseline file; SARIF | MIT | v8.30.1 (2026-03-21) | Single Go binary; `gitleaks git`, `gitleaks dir`, `protect --staged` | 1 to 5 s | no |
| betterleaks | Successor project by the gitleaks author | MIT | no GitHub release found; pushed 2026-11-12 | Maturity unverified | | no |
| TruffleHog | Secrets with optional live verification against the provider | AGPL-3.0 | v3.99.9 (2026-11-12) | Verification calls the network; `--no-verification` to stay offline | seconds | optional |
| detect-secrets | Baseline-file workflow for new secrets only | Apache-2.0 | 1.5.0 (2024-05-06) | Stale | seconds | no |
| secretlint | Pluggable secret linter (Node) | MIT | 13.1.0 (2026-10-26) | No binary to install if Node is present | seconds | no |
| eslint-plugin-no-secrets | Entropy rule in ESLint | MIT | 2.3.3 (2026-03-01) | Source files only | none extra | no |
| GitHub secret scanning + push protection | Server-side | free on public repos; private needs Secret Protection (reported $19 per committer per month) | | | | yes |

Pick: gitleaks (binary, offline, baseline, scans history); secretlint if avoiding a non-npm binary matters more.

### Dependencies, licenses, lockfile, supply chain

| Tool | What it catches | Ecosystem | License / cost | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| `pnpm audit` / `npm audit` | Known advisories for the lockfile | JS | MIT | pnpm 12.18.0 is `latest` (2026-11-05) | Queries the registry advisory endpoint | 1 to 5 s | **yes** |
| OSV-Scanner | Known vulnerabilities from lockfiles (pnpm, npm, uv, Poetry, pip, etc.), SBOMs, containers; license scanning | Agnostic | Apache-2.0 | v2.7.1 (2026-11-09) | **Offline mode**: `--offline` with a pre-downloaded database (`--download-offline-databases`); https://google.github.io/osv-scanner/usage/offline-mode | seconds | yes, unless offline DB staged |
| pip-audit | Python dependency advisories (PyPI/OSV) | Python | Apache-2.0 | 2.10.1 (2026-06-10) | | seconds | yes |
| Safety | Same, vendor database | Python | MIT CLI; account for full DB | 3.8.1 (2026-05-29) | Needs login for current data | seconds | yes |
| Trivy, Grype (+Syft) | Vulnerabilities in filesystems, lockfiles and container images; Trivy also misconfig, secrets, licenses | Agnostic | Apache-2.0 | trivy v0.76.2 (2026-11-05); grype v0.121.3 (2026-11-09) | Download a vulnerability DB; can run offline with a cached DB (unverified in this pass). Only needed if images are built. | seconds to a minute | DB download |
| audit-ci, better-npm-audit | Allow-lists and thresholds around `npm audit` | JS | Apache / MIT | 7.1.0 (2024-07-03); 4.2.1 (2026-11-05) | pnpm support in better-npm-audit unverified | seconds | yes |
| pnpm supply-chain settings | `minimumReleaseAge` (delay new versions), `blockExoticSubdeps`, `allowBuilds` (replaces `onlyBuiltDependencies`, from 10.26), `trustPolicy: no-downgrade` | JS | MIT | pnpm 10.26+; reported as defaults in pnpm 11 | Configuration, not a scanner. https://pnpm.io/supply-chain-security | none | no |
| lockfile-lint | Lockfile hosts, HTTPS, integrity hashes, package-name/URL match | JS | Apache-2.0 | 5.1.0 (2026-10-09) | Supports npm and yarn lockfiles; **pnpm-lock.yaml support unverified** | under 1 s | no |
| Socket (`socket` CLI, GitHub app) and Socket Firewall (`sfw`) | Malicious-package behaviour (install scripts, network, obfuscation); `sfw` wraps the package manager and blocks known-malicious packages | JS, Python | SaaS. `sfw` free with no API key; CLI scan features need a token; free plan limits for private repos vary by source | socket 1.15.0 (2026-11-12); sfw 2.0.6 (2026-05-22) | https://docs.socket.dev/docs/socket-firewall-overview | seconds | **yes** |
| npm provenance / `npm audit signatures` | Registry signatures and build provenance attestations | JS | free | npm 12.2.2 | npm CLI feature; a pnpm equivalent command was not confirmed (unverified) | seconds | yes |
| `pnpm licenses list`, license-checker-rseidelsohn, license-compliance, license-report | License inventory and allow/deny lists | JS | MIT / BSD | 5.0.1 (2026-05-27); 4.0.0 (2026-07-30); 6.8.6 (2026-10-09) | license-checker-rseidelsohn reads `node_modules`; behaviour with pnpm's layout unverified. Original `license-checker` is dead (2019). | seconds | no |
| pip-licenses, liccheck, reuse | Python license inventory; policy check; REUSE compliance of the repo's own files | Python / agnostic | MIT / Apache | 5.5.5 (2026-03-28); 0.9.2 (2023-09-22); 6.3.0 (2026-10-30) | | seconds | no |
| @cyclonedx/cyclonedx-npm, cdxgen, Syft | SBOM generation | Agnostic | Apache-2.0 | 7.0.0 (2026-11-09); 12.9.1 (2026-11-06) | | seconds | no |
| OpenSSF Scorecard | Repository security posture (branch protection, pinned actions, etc.) | Agnostic | Apache-2.0 | v5.6.0 (2026-10-12) | Calls the GitHub API | a minute | yes |
| Dependency Review Action | Blocks PRs that add vulnerable dependencies | GitHub | free on public; private needs Code Security (unverified) | | Actions only | | yes |

Pick: OSV-Scanner over `pnpm audit` because it has an offline mode, covers Python lockfiles too, and has allow-list config; keep `pnpm audit` in GitHub Actions where the network is open. Set the pnpm supply-chain settings regardless (zero run cost).

### CI workflow and container linters

| Tool | What it catches | License | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|
| actionlint | Workflow syntax, expression type errors, bad `needs`, shellcheck on `run:` blocks | MIT | v1.7.12 (2026-03-30) | Single Go binary; also `actionlint-py` 1.7.12.25 on PyPI | under 1 s | no |
| zizmor | Workflow security: template injection, unpinned actions, excessive permissions, dangerous triggers, credential persistence | MIT | 1.32.0 (2026-11-02) | On PyPI and as a binary. Some audits query the GitHub API when a token is given; an offline flag exists (unverified in this pass). https://docs.zizmor.sh | 1 to 3 s | optional |
| pinact | Pins actions to commit SHAs and verifies them | MIT | v5.0.2 (2026-10-25) | Fix mode needs the GitHub API | seconds | yes for pinning |
| hadolint | Dockerfile lint (with shellcheck inside `RUN`) | GPL-3.0 | v2.15.1 (2026-07-31) | Only if a Dockerfile exists | under 1 s | no |
| Checkov | IaC misconfiguration (Terraform, Kubernetes, Dockerfile, Actions) | Apache-2.0 | 3.4.5 (2026-11-12) | Only if infrastructure code exists | seconds | optional |

Pick: both actionlint and zizmor; they do not overlap (correctness vs security).

---

## 10. Frontend / UI quality

### Visual regression

| Tool | What it does | License / cost | Latest (date) | Fully local and free | Notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| Playwright `expect(page).toHaveScreenshot()` | Screenshot comparison against committed baselines; `threshold`, `maxDiffPixels`; `--update-snapshots` | Apache-2.0 | @playwright/test 1.65.0 (2026-11-05) | **Yes** | Uses pixelmatch. Baseline file names include browser and platform (`-chromium-darwin.png`) because rendering differs by OS, so macOS, WSL and Linux CI each need their own baselines, or baselines are generated only in one environment (for example a container). Browser download needs network once. Uses its own runner, not `node:test`. https://playwright.dev/docs/test-snapshots | seconds per page | no after browser install |
| pixelmatch | Pixel diff library | ISC | 8.0.0 (2026-10-06) | Yes | Use with `playwright` (library) + `pngjs` inside `node:test` to avoid a second runner | ms | no |
| odiff (`odiff-bin`) | Fast native pixel diff CLI | MIT | 4.5.0 (2026-07-23) | Yes | Native binary per platform | ms | no |
| @blazediff/core | Faster pixelmatch-compatible diff | MIT | 2.0.0 (2026-11-05) | Yes | Newer | ms | no |
| looks-same, resemblejs | Perceptual diff libraries | MIT | 10.0.1 (2025-08-18); 5.0.0 (2023-06-06) | Yes | Lower activity | ms | no |
| reg-cli / reg-suit | Directory-to-directory image diff with an HTML report; reg-suit adds storage plugins and PR comments | MIT | reg-cli 0.19.0-rc3 (2026-09-07); reg-suit 0.14.5 (2025-08-26) | reg-cli yes; reg-suit expects S3/GCS | Low activity | seconds | reg-suit yes |
| BackstopJS | Config-driven screenshot scenarios with report | MIT | 6.3.25 (2024-09-07) | Yes | Stale (over two years) | seconds per scenario | no |
| Lost Pixel | Visual regression, OSS + platform | MIT | 3.22.0 (2024-11-14) | n/a | **Archived 2026-04-22; the team joined Figma and is sunsetting the product.** https://github.com/lost-pixel/lost-pixel | | |
| Argos | Hosted review UI for screenshots | SaaS; free Hobby tier reported at 5,000 screenshots/month | @argos-ci/cli 6.11.0 (2026-10-21) | No | Account and upload | | yes |
| Chromatic | Hosted, Storybook-centred | SaaS; free tier reported at 5,000 snapshots/month, Chrome only | 18.14.3 (2026-11-09) | No | Needs Storybook or Playwright integration | | yes |
| Percy, Happo | Hosted | SaaS | @percy/cli 1.32.12 (2026-10-21); happo 7.5.1 (2026-11-11) | No | | | yes |

Pricing figures are from secondary sources (https://argos-ci.com/blog/visual-testing-pricing); check vendor pages.

Pick: Playwright's built-in screenshot assertion for a fully local, free pixel diff; the hosted tools only add a review UI. The cross-OS baseline problem is the real cost, not the tool.

### Accessibility automation

| Tool | What it catches | License | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|
| axe-core, @axe-core/playwright, @axe-core/cli | WCAG rule violations detectable by machine (contrast, names, roles, labels, landmarks) on a rendered page | MPL-2.0 | 4.14.0 (2026-10-05 / 2026-10-15) | Needs real layout for contrast: run in a browser via Playwright. In happy-dom/jsdom most structural rules run but contrast does not (unverified for happy-dom). | 1 to 3 s per page | no |
| pa11y / pa11y-ci | CLI over a headless browser running HTML_CodeSniffer and/or axe; URL lists and thresholds | LGPL-3.0-only | 10.0.0 (2026-08-28); 5.0.0 (2026-10-05) | Needs Chromium | seconds per page | no |
| Lighthouse / Lighthouse CI (`@lhci/cli`) | Accessibility, performance, best-practices, SEO scores with assertions and budgets | Apache-2.0 | lighthouse 13.6.0 (2026-10-27); @lhci/cli 0.16.1 (2026-11-11) | Needs Chrome; `lhci autorun` works locally with filesystem output; the LHCI server and temporary public storage are optional. Performance scores vary run to run. | 15 to 60 s per page | no (if upload disabled) |
| IBM Equal Access `accessibility-checker` | IBM's rule engine, baselines, different rule set from axe | Apache-2.0 | 4.0.34 (2026-09-08) | Fetches its rule archive from a CDN by default (unverified whether it can be pinned offline) | seconds per page | likely yes |
| html-validate a11y rules, `@double-great/stylelint-a11y` | Static a11y checks in HTML and CSS (missing alt, label, focus outline removal, reduced-motion) | MIT | 11.21.1; 3.8.3 (2026-11-01) | No browser needed | under 1 s | no |
| `axe-playwright-python`, pytest-playwright | Python bindings | Apache / MPL | 0.1.8 (2026-07-24); 0.10.0 (2026-10-08) | | | no |

Pick: @axe-core/playwright in the same browser session as the screenshots; html-validate for the static part. Automated rules find a minority of accessibility problems; keyboard order, focus management and meaningful names still need a driven session.

### HTML and CSS linters, size and performance budgets

| Tool | What it catches | License | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|
| html-validate | Offline HTML validation: content model, duplicate ids, deprecated elements, a11y rules, custom element metadata | MIT | 11.21.1 (2026-11-12) | Node `^22.22 \|\| >=24.8` | under 1 s | no |
| @html-eslint/eslint-plugin | HTML rules inside ESLint (flat config) | MIT | 0.68.0 (2026-11-07) | Keeps one tool | none extra | no |
| markuplint | HTML linter with framework parsers | MIT | 5.6.0 (2026-11-12) | Node `>=24` | under 1 s | no |
| vnu-jar (Nu Html Checker) | The W3C validator, run locally | MIT | 26.11.9 (2026-11-09) | Needs Java | 1 to 3 s | no |
| HTMLHint | Older rule set | MIT | 1.9.2 (2026-03-05) | Less thorough than html-validate | under 1 s | no |
| Stylelint + stylelint-config-standard | CSS errors (unknown properties, invalid values, duplicate selectors, descending specificity) and conventions | MIT | 18.0.0 (2026-11-03); 41.0.0 (2026-11-03) | Node `^22.22.2 \|\| ^24.15.0 \|\| >=26`. Plugins: stylelint-order 8.1.3, stylelint-declaration-strict-value 1.13.0 (forces tokens/variables for colours), stylelint-no-unsupported-browser-features 8.1.2 | under 1 s | no |
| @eslint/css | CSS linting in ESLint | Apache-2.0 | 2.0.1 (2026-10-15) | Fewer rules than Stylelint | none extra | no |
| Biome | CSS lint and format | MIT/Apache | 2.6.7 | | | no |
| @projectwallace/css-code-quality | CSS complexity/maintainability score | MIT | 3.1.5 (2026-10-27) | Report | under 1 s | no |
| eslint-plugin-compat | Browser APIs not supported by the browserslist targets | MIT | 7.0.2 (2026-04-29) | ESLint `^9 \|\| ^10` | none extra | no |
| size-limit | Size (and optional load-time) budget per file or entry | MIT | 14.3.0 (2026-10-22) | With no bundler, use the `@size-limit/file` preset for plain file sizes | 1 to 5 s | no |
| bundlewatch | Size budgets with PR status | MIT | 1.2.0 (2026-11-05) | Status reporting uses its service | seconds | optional |
| bundlesize | Size budgets | MIT | 0.18.2 (2024-03-15) | Stale | | |
| Lighthouse CI budgets, sitespeed.io (43.0.0, 2026-11-12), unlighthouse (0.19.1) | Performance budgets (LCP, TBT, transfer size) | Apache / MIT | as stated | Timing metrics are noisy on shared runners; byte budgets are deterministic | 15 to 60 s per page | no |
| djlint | Lint/format HTML templates (Jinja, Django) | GPL-3.0-or-later | 1.50.0 (2026-11-11) | Python side | under 1 s | no |

Pick: html-validate + Stylelint (standard config) for a plain HTML/CSS page; for a no-bundler app a size budget is a few lines of script or size-limit's file preset.

---

## 11. Formatting and hygiene beyond Prettier

| Tool | What it catches | Ecosystem | License | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| cspell | Spelling in code and prose with code-aware dictionaries, per-project word list | Agnostic (Node) | MIT | 10.4.1 (2026-11-06) | Thorough; needs a word list to settle | 2 to 10 s | no |
| typos | Known-misspelling corrections (low false-positive), Rust binary | Agnostic | MIT OR Apache-2.0 | 1.52.2 (2026-11-11) | Also on PyPI | under 1 s | no |
| codespell | Same approach in Python | Agnostic | GPL-2.0-only | 2.4.3 (2026-07-15) | | 1 s | no |
| markdownlint-cli2 / markdownlint-cli | Markdown structure and style | Agnostic (Node) | MIT | 0.24.1 (2026-11-12); 0.50.0 (2026-10-24) | cli2 is the config-driven one | 1 s | no |
| @eslint/markdown | Markdown rules and linting of fenced code blocks in ESLint | TS/JS | MIT | 8.0.3 (2026-07-01) | | none extra | no |
| pymarkdownlnt, mdformat | Markdown lint / format | Python | MIT | 0.9.41 (2026-10-13); 1.0.0 (2025-10-16) | | 1 s | no |
| Vale | Prose style rules (word lists, style guides) | Agnostic | MIT | 3.26.0.1 on PyPI (2026-11-02) | Style packages downloaded with `vale sync` | 1 s | once |
| @commitlint/cli | Conventional-commit message rules | Agnostic (Node) | MIT | 21.2.4 (2026-10-18) | `--from/--to` for a PR range | under 1 s | no |
| commitizen (Python), gitlint | Same in Python | Python | MIT | 4.19.3 (2026-10-24); gitlint 0.19.1 (2023-03-10, stale) | | under 1 s | no |
| editorconfig-checker | Files obey `.editorconfig` (indent, EOL, final newline, charset) | Agnostic | MIT | 3.11.1 on PyPI (2026-08-10) | Go binary; `eclint` is dead (2018) | under 1 s | no |
| publint | package.json publish correctness | JS | MIT | 0.3.25 (2026-10-01) | Published packages only | under 1 s | no |
| sort-package-json | Canonical key order | JS | MIT | 4.1.0 (2026-10-15) | `--check` | under 1 s | no |
| syncpack | Version-range consistency across a monorepo | JS | MIT | 15.3.3 (2026-08-09) | Monorepos only; sherif 1.13.0 and @manypkg/cli 0.25.1 are alternatives | under 1 s | no |
| eslint-plugin-package-json, npm-package-json-lint | package.json rules | JS | MIT | 1.14.0 (2026-11-03); 11.0.1 (2026-10-31) | The ESLint plugin avoids another tool | none extra | no |
| installed-check, ls-engines | `engines` range agrees with dependencies' | JS | MIT | 11.0.0 (2026-08-03); 0.10.1 (2026-06-20) | | seconds | ls-engines yes |
| ShellCheck | Shell script bugs (quoting, unset variables, portability) | Agnostic | GPL-3.0 | v0.11.0 (2025-08-04) | Binary; `shellcheck-py` on PyPI | under 1 s | no |
| shfmt | Shell formatting | Agnostic | BSD-3-Clause | v3.14.1 (2026-09-06) | `shfmt-py` on PyPI | under 1 s | no |
| yamllint | YAML syntax, duplicate keys, truthy values, indentation | Agnostic | GPL-3.0-or-later | 1.38.0 (2026-01-13) | | under 1 s | no |
| eslint-plugin-yml, eslint-plugin-jsonc, @eslint/json | YAML/JSON in ESLint | JS | MIT / Apache | section 1 | | none extra | no |
| check-jsonschema | Validate YAML/JSON against schemas (workflows, dependabot, package.json) | Agnostic | Apache-2.0 | 0.39.0 (2026-10-26) | Built-in vendored schemas work offline; others are fetched | 1 s | optional |
| lychee | Dead links in Markdown/HTML, local files and remote URLs | Agnostic | Apache-2.0 | lychee-v0.24.2 (2026-05-01) | `--offline` checks only local/relative links | 1 s offline; longer online | optional |
| markdown-link-check, linkinator | Same in Node | Agnostic (Node) | ISC / MIT | 3.15.0 (2026-07-28); 8.1.0 (2026-08-29) | Remote checks are flaky by nature | varies | optional |
| ls-lint | File and directory naming | Agnostic | MIT | 2.3.2 (2026-10-17) | | under 1 s | no |
| dprint | Fast multi-language formatter | Agnostic | MIT | 0.64.3 (2026-10-23) | Plugins are downloaded WASM | under 1 s | once |
| Ruff format, Black, isort | Python formatting and import order | Python | MIT | ruff 0.17.5; black 26.10.1 (2026-10-10); isort 9.0.2 (2026-09-28) | Ruff covers both | under 1 s | no |

Overlaps: **typos vs cspell**: typos for a gate (almost no false positives, sub-second); cspell when full dictionary coverage is wanted and someone will maintain the word list. **lychee vs markdown-link-check**: lychee, for the offline mode and speed.

---

## 12. Documentation quality

| Tool | What it checks | Ecosystem | License | Latest (date) | Stack notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| eslint-plugin-jsdoc (`require-jsdoc` with `publicOnly`, `require-description`, `require-param`, `check-param-names`, `informative-docs`, `no-types` for TS) | Doc comment presence on exports and agreement between doc and signature | TS/JS | BSD-3-Clause | 65.4.5 (2026-11-06) | ESLint 10 ok. Gives a fail list, not a percentage. | none extra | no |
| eslint-plugin-tsdoc | TSDoc syntax validity | TS | MIT | 0.5.4 (2026-09-29) | Depends on `@typescript-eslint/utils ~8.56` | none extra | no |
| TypeDoc (`--validation`, `--treatWarningsAsErrors`) + typedoc-plugin-coverage | API docs extraction; warnings for undocumented exports and broken `{@link}`; coverage badge/percentage | TS | Apache-2.0 / MIT | 0.28.20 (2026-07-05); 4.0.3 (2026-04-13) | **TypeScript peer stops at `6.0.x`**: needs the TS 6 alias on a TS 7 project | 5 to 20 s | no |
| @microsoft/api-extractor + api-documenter | `ae-undocumented` and `ae-missing-release-tag` messages; API report | TS | MIT | 7.60.1; 7.30.20 (2026-10-30) | Bundles TS 6.0.3 | 5 to 20 s | no |
| typescript-docs-verifier | Compiles TypeScript code blocks in Markdown files | TS | Apache-2.0 | 3.0.2 (2026-03-02) | Uses the `typescript` API (TS 7 unverified) | seconds | no |
| @eslint/markdown processor | Lints fenced JS/TS blocks in Markdown | TS/JS | MIT | 8.0.3 | Syntax and lint only, no execution | none extra | no |
| markdown-doctest, embedme | Run JS blocks in Markdown; embed source files into README | JS | MIT | 1.1.0 (2020); 1.22.1 (2022) | Stale | | no |
| doc-detective | Executes documented procedures (shell commands, HTTP calls, browser steps) from Markdown and asserts results | Agnostic (Node) | AGPL-3.0-only | 4.43.0 (2026-11-09) | Heavy; license | scales with steps | depends on steps |
| runme | Runs shell blocks from Markdown files by name | Agnostic | Apache-2.0 | 3.17.0 (2026-07-13) | Go binary via npm | scales | no |
| cogapp | Regenerates generated sections in docs; `--check` fails if stale | Agnostic (Python) | MIT | 3.6.0 (2025-09-21) | Good for "README shows the real `--help` output" | under 1 s | no |
| byexample | Doctest-style execution of examples in many languages including shell and JavaScript | Agnostic (Python) | GPL-3.0 | 11.0.0 (2026-03-23) | | scales | no |
| interrogate, docstr-coverage | Docstring coverage percentage with `--fail-under` | Python | MIT | 1.7.0 (2024-04-07); 2.3.2 (2024-05-07) | Low activity but functional | under 1 s | no |
| Ruff `D` rules, pydoclint | Docstring presence/style; docstring vs signature agreement | Python | MIT | 0.17.5; 0.12.0 (2026-10-28) | pydocstyle (2023) and darglint (2021) are dead; these replace them | under 1 s | no |
| `pytest --doctest-modules`, `--doctest-glob`, xdoctest, pytest-markdown-docs, pytest-examples, Sphinx doctest | Execute examples in docstrings and Markdown | Python | MIT / Apache | xdoctest 1.3.2 (2026-03-27); pytest-markdown-docs 0.9.2 (2026-03-23); pytest-examples 0.0.18 (2025-05-06); phmdoctest 1.4.0 (2022, stale) | | scales with examples | no |

Gap: there is no maintained, lightweight tool that verifies "every command in the README exists in the manifest and runs" for a Node project. The practical deterministic check is a small script that extracts fenced `sh` blocks and compares `pnpm <script>` names against `package.json`; running them on a clean clone remains a smoke-run job.

---

## 13. Aggregators and platforms

| Tool | What it adds over running the tools yourself | License / cost | Latest (date) | Offline | Notes |
|---|---|---|---|---|---|
| SonarQube Community Build (self-hosted) | One rule engine across languages, cognitive complexity, duplication, quality gate on "new code", history dashboard | LGPL-3.0, free | 26.11.0 (2026-11-04) | Runs on your own server (Java + database). The scanner (`@sonar/scan` 5.1.0, 2026-11-09) needs that server. | Community Build has no branch/PR analysis (reported; not re-verified). A daemon: not suitable inside a sandboxed gate. |
| SonarQube Cloud | Same, hosted, PR decoration | Free plan: private projects up to 50k LOC; docs say free-plan analysis is limited to the main branch (sources conflict on PR analysis). https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/managing-subscription/subscription-plans | SaaS | No | Account, token, upload of source |
| eslint-plugin-sonarjs | The SonarJS rules without the platform | LGPL-3.0-only | 4.2.2 | Yes | The offline way to get most of Sonar's JS/TS value |
| Qlty (CLI + Cloud; successor to Code Climate Quality) | One CLI that installs and runs 70+ linters, plus its own complexity, duplication and "code smells" metrics, baselines, diff-aware mode | CLI is Fair Source (free including commercial use, not OSI open source); Cloud free tier lists unlimited private repos with limited analysis minutes. https://qlty.sh/blog/qlty-cli-is-fair-source, https://docs.qlty.sh/cloud/billing/plans | v0.668.0 (2026-11-06) | CLI runs locally; it downloads linter binaries on first use | Windows support unverified |
| Codacy | Hosted aggregation of open-source linters, PR comments, coverage | SaaS; free for public repos; private repos need a paid plan (sources conflict) | | No | Account |
| DeepSource | Hosted analyzers + autofix | SaaS; free plan for private repos ended 2026-03-23 per its changelog (https://deepsource.com/changelog/2026-02-23); Team plan paid | | No | Account |
| GitHub Code Quality | GitHub-native maintainability findings on PRs | GA 2026-06-16; reported at $10 per active committer per month plus usage. https://github.blog/changelog/2026-06-16-github-code-quality-is-now-generally-available/ | | No | GitHub only; includes AI features |
| MegaLinter | Docker image bundling ~100 linters with one config and consolidated reports | AGPL-3.0, free | v10.2.0 (2026-10-31) | Runs locally through Docker (`mega-linter-runner`); needs the Docker daemon and a multi-GB image | Slow start; fine in Actions, awkward in a sandbox |
| Super-Linter | Same idea from the GitHub side | MIT | v9.0.0 (2026-10-01) | Docker | |
| Trunk Code Quality (`trunk check`) | Hermetic installs of pinned linter versions, "hold the line" (only new issues), caching daemon | Proprietary CLI; free for public repos and for private repos up to 5 committers. https://docs.trunk.io/code-quality/overview/licensing | launcher 1.3.4 (2024-11-06); plugins v1.11.0 (2026-08-01) | Downloads tools; runs a local daemon | Launcher on npm is two years old; treat maintenance as uncertain |
| pre-commit | Hook manager with a huge registry of hooks, isolated environments per hook, `--from-ref/--to-ref` to run on changed files | MIT | 4.7.0 (2026-10-12) | Hooks are cloned from git on first run; `repo: local` hooks need no network | Python. `prek` 0.5.10 (2026-11-04, MIT) is a faster Rust reimplementation reading the same config. |
| lefthook | Fast Go hook runner, parallel commands, glob/staged-file filters | MIT | 2.2.2 (2026-10-13) | Yes | No hook registry: you call tools you already have |
| husky + lint-staged / nano-staged | Git hooks; run commands on staged files only | MIT | husky 9.1.7 (2024-11-18); lint-staged 17.6.0 (2026-09-26); nano-staged 1.0.2 (2026-04-08) | Yes | |
| Danger JS | Scripted PR rules (size, missing tests, changelog) posting PR comments | MIT | 14.1.0 (2026-10-26) | No (needs the PR API) | CI only |
| reviewdog | Posts any linter's output as PR review comments, filtered to the diff (`-filter-mode=added`/`diff_context`) | MIT | v0.21.3 (2026-11-07) | Has a local mode against `git diff` (`-diff`) | The simplest "only new findings" filter for arbitrary tools |

Pick: for a pipeline that already owns its gate script, an aggregator adds mostly installation management. reviewdog (or `diff-quality`) is the piece worth borrowing, for diff filtering. SonarQube's unique value is the new-code quality gate and history; eslint-plugin-sonarjs + jscpd + lizard reproduce most of the findings offline.

---

## 14. Diff-aware gating ("fail only on new problems")

| Technique / tool | How it works | Ecosystem | License | Latest (date) | Notes | Network |
|---|---|---|---|---|---|---|
| ESLint bulk suppressions | `eslint --suppress-all` (or `--suppress-rule X`) writes `eslint-suppressions.json` with per-file, per-rule counts; later runs fail only on violations beyond those counts; `--prune-suppressions` removes fixed ones; unused suppressions fail the run unless `--pass-on-unpruned-suppressions` | TS/JS | MIT | ESLint 10.14.0 | Only `error` rules. Built in since ESLint 9.24 (version from memory). https://eslint.org/docs/latest/use/suppressions | no |
| TypeScript error baselines | `tsc-baseline` stores current compiler errors and fails on new ones | TS | MIT | 2.1.0 (2026-08-30) | Parses `tsc` text output, so compiler-version independent in principle (unverified on TS 7) | no |
| Betterer | Generic ratchet: snapshot any test (ESLint rule counts, TS strictness, regex) and fail when it gets worse | TS/JS | MIT | `latest` tag is 6.0.0-alpha.1 (2024-12-01); repo last pushed 2026-07-11 | Low activity; alpha as latest. ESLint suppressions cover its main use. | no |
| eslint-formatter-ratchet, esplint | Per-rule count ratchets | TS/JS | MIT | 3.0.0 (2026-03-15); 0.10.2 (2023) | Superseded by suppressions | no |
| eslint-plugin-diff | Reports ESLint problems only on changed lines | TS/JS | MIT | 2.1.7 (2026-03-05) | Misses problems a change causes on untouched lines | no |
| lint-staged / nano-staged | Run tools on staged files | Agnostic | MIT | 17.6.0; 1.0.2 | File-level, not line-level | no |
| Biome `--changed` / `--staged`; oxlint | Lint only files changed versus the default branch | TS/JS | MIT | 2.6.7 | File-level | no |
| knip | No baseline file; use JSON reporter and compare counts, or fix to zero once | TS/JS | ISC | 6.45.1 | Unverified whether a baseline option exists in v6 | no |
| dependency-cruiser `--ignore-known` | Baseline of known violations (`depcruise-baseline`) | TS/JS | MIT | 18.7.2 | | no |
| jscpd `--threshold` | Percentage gate; ratchet by lowering the number | Agnostic | MIT | 5.4.3 | | no |
| Stryker `--incremental`, `--mutate file:lines`, `thresholds.break` | Reuse previous mutant results; restrict to changed lines; fail under a score | TS/JS | Apache-2.0 | 10.1.1 | Section 7 | no |
| diff-cover / diff-quality | Coverage on changed lines; `diff-quality --violations=<tool>` filters linter output (flake8, pylint, eslint, ruff via report files) to changed lines | Agnostic | Apache-2.0 | 11.0.1 (2026-11-04) | Works from report files, so any linter with a supported format | no |
| reviewdog `-filter-mode` | Filters any errorformat/SARIF/rdjson input to added lines or diff context | Agnostic | MIT | v0.21.3 | Local `-diff="git diff main"` mode | no for local mode |
| Semgrep `--baseline-commit` | Reports only findings not present at the baseline commit | Agnostic | LGPL-2.1 | 1.185.0 | | no |
| gitleaks `--baseline-path`, detect-secrets baseline | Known findings file | Agnostic | MIT | v8.30.1 | | no |
| Ruff | `--add-noqa` to suppress existing, then gate; `--diff`; no native baseline (unverified) | Python | MIT | 0.17.5 | | no |
| mypy-baseline; basedpyright baseline | Store existing type errors, fail on new | Python | MIT | 0.7.4 (2026-04-13); 1.40.2 | | no |
| Pylint | No native baseline; use diff-quality | Python | | | | no |
| SonarQube "new code" quality gate | Conditions on new-code coverage, duplication, issues | Agnostic | section 13 | | Server | yes |
| Trunk "hold the line", Qlty diff mode | Platform-level new-issues-only | Agnostic | section 13 | | | partly |
| Codecov patch status | Diff coverage | Agnostic | SaaS | | | yes |

Pick: ESLint's own suppressions file for lint ratchets, diff-cover for coverage, and reviewdog or diff-quality as the generic filter for everything else. A counts-in-a-JSON-file ratchet written in the gate script covers tools with no baseline (knip, jscpd, lizard).

---

## 15. Reliability-oriented checks

| Tool / technique | What it enables | Ecosystem | License | Latest (date) | Notes | Cost | Network |
|---|---|---|---|---|---|---|---|
| `node:test` `mock.timers` | Fake `setTimeout`/`setInterval`/`Date` | Node | MIT | built in | Stable status not re-checked (unverified) | none | no |
| @sinonjs/fake-timers / sinon | Fake clock with async tick helpers; stubs and spies | TS/JS | BSD-3-Clause | 15.4.0 (2026-05-05); sinon 22.1.0 (2026-07-20) | Runner-agnostic | none | no |
| `node:test` `mock.method` / `mock.module` | Fault injection by replacing a dependency with one that throws, rejects, or delays (`--experimental-test-module-mocks` for modules) | Node | MIT | built in | Module mocks still experimental | none | no |
| undici `MockAgent`, nock, msw | HTTP fault injection: errors, timeouts, slow or malformed responses | TS/JS | MIT | undici 8.12.4 (2026-11-05); nock 15.0.6 (2026-11-05); msw 3.0.5 (2026-11-11) | undici's MockAgent covers built-in `fetch` | none | no |
| memfs | In-memory `fs` for tests; can be wrapped to fail specific calls | TS/JS | Apache-2.0 | 4.80.1 (2026-11-12) | Injecting via dependency parameter is cleaner than patching `node:fs` under ESM | none | no |
| mock-fs | Patches `fs` bindings | JS | MIT | 5.5.0 (2025-02-06) | Fragile across Node versions | | no |
| Toxiproxy | TCP proxy injecting latency, resets, bandwidth limits | Agnostic | MIT | v2.13.0 (2026-10-14); `toxiproxy-node-client` 4.1.0 | **Needs a daemon.** For networked dependencies only. | seconds | local daemon |
| fast-check model-based + `fc.scheduler()` | Random operation sequences against a model, including "crash here" commands | TS/JS | MIT | 4.10.2 | The most practical way to test save/load state machines | scales with runs | no |
| Crash-consistency for file writes: fault-injecting `fs` wrapper | Hand-rolled wrapper around the store's file operations that throws or truncates at step N (after temp write, before `fsync`, before `rename`), then asserts the store reopens to old or new state, never a corrupt one | any | | | **No off-the-shelf Node library found.** Deterministic and cheap once written; enumerates every crash point. | seconds | no |
| Crash-consistency: process kill loop | Spawn a child doing writes, `SIGKILL` at random/seeded times, verify on reopen | any | | | Tests the application-level protocol, not OS page-cache loss | seconds to minutes | no |
| LazyFS | FUSE filesystem with its own page cache that can drop unsynced data and inject torn writes, simulating power loss | Linux | see repo | https://github.com/dsrhaslab/lazyfs (release status not checked) | **Linux only, needs FUSE**: usable in a Linux CI job, not in a macOS sandbox | minutes | no |
| CrashMonkey / ACE, ALICE, dm-flakey | Filesystem- and block-level crash testing | Linux | research | https://usenix.org/conference/osdi18/presentation/mohan | Aimed at filesystem developers; needs kernel modules or root. Not practical. | | |
| write-file-atomic | Library implementing temp-file + rename (the pattern to test, not a tester) | JS | ISC | 8.0.0 (2026-05-08) | | | no |
| OS matrix in CI | `strategy.matrix.os: [ubuntu-latest, macos-latest, windows-latest]` catches path separator, case-sensitivity, `rename`-over-open-file, line-ending and permission differences | GitHub Actions | | | Deterministic and cheap to add; Windows runners are slower and cost more minutes on private repos | 2 to 3x CI time | CI |
| Node version matrix | Same for runtime versions | | | | | | |
| Randomised order | `node --test --test-randomize` (v24.16.0+), seed printed; `--test-random-seed=<n>` to replay | Node | | | Section 7 | same as suite | no |
| Repeated runs | Shell loop of N runs with different seeds; `--test-rerun-failures` to isolate flakes; `--test-concurrency`, `--test-isolation=none` to vary scheduling | Node | | | No built-in repeat flag | N x suite | no |
| `--test-timeout`, `--test-shard` | Hung-test detection; splitting | Node | | | | | no |
| Python: time-machine, freezegun | Clock control | Python | MIT / Apache | 3.6.0 (2026-10-25); 1.5.5 (2025-08-09) | time-machine is faster and more complete | none | no |
| Python: pyfakefs, pytest-socket, pytest-timeout, responses, vcrpy, pytest-httpserver | Fake filesystem; block real network in tests; per-test timeouts; HTTP mocking and recording | Python | Apache / MIT | 6.3.2 (2026-11-03); 0.8.1 (2026-08-19); 2.4.0 (2025-05-05); 0.26.3 (2026-08-26); 9.4.2 (2026-11-02); 1.2.1 (2026-11-10) | | none | no |
| Python: pytest-randomly, pytest-repeat, pytest-xdist, Hypothesis stateful | Random order; repeats; parallel scheduling; state-machine tests | Python | MIT / MPL | section 7; xdist 3.8.0 (2025-07-01) | | | no |

---

## Additional categories found while surveying

- **Type-stripping compatibility.** `erasableSyntaxOnly` (tsconfig) and eslint-plugin-erasable-syntax-only catch syntax that Node's type stripping cannot run. Relevant because the project runs `.ts` directly.
- **Non-JS files inside ESLint.** @eslint/json, @eslint/markdown, @eslint/css, eslint-plugin-yml and @html-eslint let one linter process and one suppressions file cover JSON, Markdown, CSS, YAML and HTML.
- **Dependency hygiene.** eslint-plugin-depend and @e18e/cli (replaceable dependencies), installed-check (engines agreement), `pnpm dedupe --check`, `pnpm install --frozen-lockfile` (lockfile drift).
- **Schema validation of config files.** check-jsonschema for workflow files, dependabot config, `package.json`, `tsconfig.json`.
- **File and folder naming.** ls-lint, eslint-plugin-check-file.
- **SBOM generation.** cyclonedx-npm, cdxgen, Syft.
- **Repository posture.** OpenSSF Scorecard.
- **Python packaging checks.** validate-pyproject, twine check, pyroma, check-manifest.
- **Public API diffing.** api-extractor report (TS), griffe check (Python).

---

## (a) Top additions for the TypeScript stack, by value per unit of effort

Current gate: typecheck, ESLint + typescript-eslint "recommended", Prettier, tests with a coverage threshold, comment density, changed-files scope.

1. **Type-aware lint rules** (typescript-eslint `strictTypeChecked`, or `oxlint --type-aware` with `oxlint-tsgolint@7`). Catches unawaited promises, promises passed where a sync callback is expected, non-exhaustive switches, `any` leaking through calls and returns, conditions that are always true. First confirm how the project's ESLint resolves `typescript`: typescript-eslint's peer range stops below 6.1.0 and TS 7.0 has no API, so typed ESLint rules need the TS 6 alias; oxlint's engine is the one built on TS 7.
2. **Extra compiler flags**: `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`, `noPropertyAccessFromIndexSignature`, `erasableSyntaxOnly`, `verbatimModuleSyntax`. Catches undefined-from-index bugs, optional/undefined confusion, and syntax type stripping cannot run. No new dependency.
3. **knip**. Catches unused files, exports, types and dependencies, and imports of undeclared dependencies. Independent of the TS 7 API gap. One command, JSON output.
4. **Complexity and size limits in ESLint** (`complexity`, `max-depth`, `max-params`, `max-lines-per-function`, `sonarjs/cognitive-complexity`) plus the rest of eslint-plugin-sonarjs, introduced with `--suppress-all` so only new violations fail. Catches functions growing past review-able size and Sonar's bug patterns. The existing gate has nothing for complexity.
5. **Test-runner flags already in Node 24**: `--test-randomize` (order-dependent tests), `--test-coverage-branches` and `--test-coverage-functions` thresholds, `--test-timeout`, and never `--test-force-exit` (leaked handles then fail the run); `why-is-node-running` to diagnose. No new dependency except the diagnostic.
6. **gitleaks + actionlint + zizmor**. Catches committed secrets (including in history), broken workflow expressions, and workflow security holes (injection, unpinned actions, broad permissions). Three single binaries, sub-second to seconds, offline.
7. **jscpd** with a threshold and JSON report. Catches copy-paste across files in any language; nothing in the current gate measures duplication.
8. **Changed-lines coverage with diff-cover** on the lcov report. Catches new code shipped without tests while whole-project coverage stays above the threshold.
9. **Import-structure rules**: eslint-plugin-boundaries (layers, allowed directions) and `import-x/no-cycle`; dependency-cruiser for rules plus a graph once it supports TS 7.1. Catches wrong-direction imports and cycles mechanically, before a reviewer has to.
10. **Frontend static and rendered checks**: html-validate and Stylelint (static, sub-second), then @axe-core/playwright and Playwright `toHaveScreenshot()` in one browser session. Catches invalid HTML, CSS errors, machine-detectable accessibility failures and unintended visual changes. The screenshot baselines must be per-OS or produced in one fixed environment.
11. **Supply-chain settings and scan**: pnpm `minimumReleaseAge`, `blockExoticSubdeps`, `allowBuilds`; OSV-Scanner with a staged offline database (or `pnpm audit` in Actions). Catches known-vulnerable and freshly published malicious versions.
12. **fast-check**, then **Stryker (TAP runner, incremental, scoped with `--mutate` to changed files)**. fast-check finds edge-case inputs and, with its scheduler, async interleavings. Stryker finds assertions that do not constrain behaviour. Highest value for test quality but highest cost and setup risk (the type-stripping route is unverified), so run it per slice or nightly, not per commit.

Also cheap: typos, markdownlint-cli2, `eslint-comments/require-description`, `reportUnusedDisableDirectives`, eslint-plugin-no-unsanitized, eslint-plugin-regexp.

## (b) Top additions for a Python project

1. **Ruff with a wide rule selection** (`B`, `S`, `SIM`, `UP`, `C90`, `PL`, `PT`, `ASYNC`, `ARG`, `ERA`, `RUF`, `D` as wanted) and `ruff format --check`. Covers bugbear, bandit, complexity, pytest style and async mistakes in under a second.
2. **A strict type checker**: `mypy --strict` or pyright/basedpyright in strict mode (basedpyright has a baseline file for adoption).
3. **diff-cover** on `coverage.xml` with branch coverage on (`--cov-branch`). New lines must be covered.
4. **deptry + vulture**. Unused/missing/transitive dependencies; dead functions, classes and variables.
5. **import-linter** (or tach). Layer and independence contracts, forbidden imports.
6. **pytest plugins as defaults**: pytest-randomly (order dependence), pytest-timeout (hangs), pytest-socket (accidental network), `-W error` including `ResourceWarning` and asyncio debug mode (leaks, never-awaited coroutines).
7. **gitleaks, actionlint, zizmor** (shared with the TS list).
8. **pip-audit or OSV-Scanner** on the lockfile; `uv lock --check` / hash-pinned requirements for lockfile integrity.
9. **Hypothesis** for parsers, serializers and state machines.
10. **complexipy or xenon** thresholds (or Ruff's `C901`/`PLR09xx`) and **jscpd** for duplication.
11. **mutmut or cosmic-ray**, per slice or nightly.
12. **interrogate / Ruff `D` + pydoclint** for docstring coverage and signature agreement; `pytest --doctest-modules` so examples execute.

## (c) Where no good deterministic tool exists

A model reviewer or a driven run of the app is still needed for:

- **Naming, intent and readability.** Linters check form, not whether a name tells the truth or a comment explains why.
- **Whether an abstraction is premature or missing, and whether the module split matches the domain.** Tools enforce rules someone already wrote; they do not judge the design.
- **Semantic duplication.** Clone detectors match tokens; two different implementations of the same idea pass.
- **Code the change does not need** (unused options, flags nothing sets, impossible-case checks). knip finds unused exports, not unneeded behaviour.
- **Test meaningfulness beyond mutation score**: over-mocking, asserting implementation details, tests that mirror the code. There is also no maintained test-smell linter for `node:test`.
- **Acceptance criteria and product behaviour.** Whether the feature does what was asked needs the app driven end to end.
- **Async races and ordering bugs in real code.** No production-grade dynamic race detector for Node; the static rules and fast-check's scheduler cover only what they are pointed at.
- **Crash consistency of file writes.** No off-the-shelf Node tool; needs a hand-written fault-injecting wrapper or a kill loop, and true power-loss behaviour needs Linux-only LazyFS.
- **Most of accessibility.** Automated rules catch a minority of WCAG failures; keyboard order, focus management, announcements and meaningful labels need a driven session.
- **Visual and UX quality.** Pixel diffs detect change, not whether the new screen is right, readable or consistent with the design system.
- **Security logic**: authorization gaps, misuse of cryptography that is syntactically fine (key handling, nonce reuse across calls, what gets logged), threat-model questions. SAST finds patterns, not missing checks.
- **Error-handling quality**: whether failures degrade sensibly, messages are diagnosable, retries are on the right failure.
- **Documentation truth.** Tools check presence and syntax; whether the README's steps work on a clean clone needs the steps run.
- **Unused public class members in TypeScript.** knip v6 removed the check; nothing maintained replaces it.
- **Maintainability index for TypeScript.** The classic tools are dead; fta's score is a different composite.

## (d) Not verified in this pass

- **Stryker TAP runner with Node's built-in type stripping** (no loader, `.ts` tests and sources). Docs cover `tsx` and pre-compilation only. Needs a trial run.
- **Stryker's typescript-checker on TypeScript 7** (expected to need TS 6 resolvable; not confirmed).
- **type-coverage on TypeScript 7.0.** Peer range lists 7, but 7.0 has no API.
- **dependency-cruiser on TS 7.1 beta**, and whether its non-`tsc` parsers handle `.ts` without the TypeScript package.
- **Whether TypeScript 7.1 RC or stable has shipped.** Beta confirmed (2026-10-20); stable "late November" is tentative. typescript-eslint has given no date for 7.x support.
- **Which two type-aware rules oxlint-tsgolint lacks**, and oxlint's Windows/WSL binaries (assumed, not checked).
- **Biome**: the current group of `noFloatingPromises` (rule page showed nursery) and the list of other type-aware rules; state of HTML support.
- **Node**: that `--experimental-test-coverage` is still the required flag name in 24.x, that coverage thresholds are whole-run only, the stability level of `mock.timers`, and that Node's lcov reporter output is accepted by diff-cover.
- **c8 with type-stripped `.ts` files** (line mapping assumed correct because stripping preserves positions).
- **eslint-plugin-no-only-tests** detection of `node:test`'s `{ only: true }` option form.
- **axe-core under happy-dom** (which rules run without real layout).
- **Semgrep/Opengrep fully offline** with vendored rules and `--metrics=off`; Opengrep's rules license; Semgrep on native Windows.
- **zizmor's offline flag** and exactly which audits need the GitHub API.
- **lockfile-lint support for `pnpm-lock.yaml`**; license-checker-rseidelsohn against pnpm's `node_modules` layout; better-npm-audit with pnpm; a pnpm equivalent of `npm audit signatures`.
- **Trivy/Grype offline database workflow.**
- **IBM accessibility-checker offline** (rule archive fetch).
- **Pricing and plan limits** for SonarQube Cloud (PR analysis on the free plan: sources conflict), Codacy (free private repos: sources conflict), Socket (free-plan limits: sources conflict), Chromatic and Argos (figures from secondary sources), GitHub Code Security / Secret Protection / Code Quality (dollar figures from secondary sources). SonarQube Community Build's lack of branch/PR analysis was not re-checked.
- **Qlty CLI on Windows**; Trunk's maintenance state (launcher package last published 2024-11).
- **betterleaks** maturity (no release found through the API); **LazyFS** release state and license.
- **Deterministic-simulation npm packages** (`determined`, `crashlab`, `simnodejs`, `flake-monster`): existence and dates confirmed, quality not evaluated.
- **ESLint 10 compatibility of plugins that declare no peer range** (eslint-plugin-security, eslint-plugin-no-only-tests) or an open-ended one (`>=5`, `>=6`, `>=7`, `>=8`: no-secrets, boundaries, tsdoc, depend, playwright). Peer ranges quoted are what the registry declares, not test results.
- **Rule names and tsconfig flag names** for typescript-eslint presets, ESLint core rules, Ruff rule codes and TypeScript options are from documentation knowledge and were not re-fetched individually. The ESLint version that introduced bulk suppressions (9.24) is from memory.
- **Run-cost figures** throughout are estimates, not measurements.
- **GitHub API rate limit** stopped the last few repository lookups (dependency-cruiser's repo record; its npm record was used instead).

## Main sources

- Registries (queried 2026-11-12): https://registry.npmjs.org/, https://pypi.org/, https://api.github.com/
- TypeScript 7.0: https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/ ; 7.1 beta: https://devblogs.microsoft.com/typescript/announcing-typescript-7-1-beta/
- typescript-eslint and TS 7: https://github.com/typescript-eslint/typescript-eslint/issues/12518
- oxlint type-aware stable: https://oxc.rs/blog/2026-07-22-type-aware-linting-stable
- Biome type inference: https://biomejs.dev/blog/vercel-partners-biome-type-inference
- Deno lint: https://docs.deno.com/runtime/lint_and_format/
- Node 24 CLI flags: https://nodejs.org/docs/latest-v24.x/api/cli.html
- Stryker TAP runner: https://stryker-mutator.io/docs/stryker-js/tap-runner/ ; incremental: https://stryker-mutator.io/docs/stryker-js/incremental/
- ESLint suppressions: https://eslint.org/docs/latest/use/suppressions
- knip v6: https://knip.dev/blog/knip-v6
- dependency-cruiser 18.1.0 notes: https://newreleases.io/project/npm/dependency-cruiser/release/18.1.0
- Playwright snapshots: https://playwright.dev/docs/test-snapshots
- Lost Pixel archive notice: https://github.com/lost-pixel/lost-pixel
- OSV-Scanner offline: https://google.github.io/osv-scanner/usage/offline-mode
- pnpm supply chain: https://pnpm.io/supply-chain-security
- Semgrep vs Opengrep: https://semgrep.dev/docs/faq/comparisons/opengrep ; https://github.com/opengrep/opengrep
- CodeQL CLI licensing: https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-cli
- SonarQube Cloud plans: https://docs.sonarsource.com/sonarqube-cloud/administering-sonarcloud/managing-subscription/subscription-plans
- Qlty: https://qlty.sh/blog/qlty-cli-is-fair-source ; https://docs.qlty.sh/cloud/billing/plans
- DeepSource plan change: https://deepsource.com/changelog/2026-02-23
- Trunk licensing: https://docs.trunk.io/code-quality/overview/licensing
- Socket Firewall: https://docs.socket.dev/docs/socket-firewall-overview
- Visual testing pricing (vendor-authored): https://argos-ci.com/blog/visual-testing-pricing
- Node race-detection research: https://github.com/andreendo/noderacer ; https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ECOOP.2025.9
- Crash-consistency research: https://usenix.org/conference/osdi18/presentation/mohan ; https://github.com/dsrhaslab/lazyfs
- fast-check race conditions: https://fast-check.dev/docs/advanced/race-conditions/
