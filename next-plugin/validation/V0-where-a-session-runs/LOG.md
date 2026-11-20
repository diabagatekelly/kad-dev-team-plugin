# V0 trial log

## 2026-11-20, the Mac (macOS 27.2.1, Apple silicon, 10 cores, 24 GB)

| Step | By | Result |
|---|---|---|
| `vm.sh check` | script | `sbx` missing, Homebrew present |
| `vm.sh install --yes` | script, on the owner's word in the session | Docker Sandboxes 0.54.0 installed by Homebrew in 39 s; no admin password asked; runs on macOS 27 (the documentation names 14 or later) |
| `sbx ls` | script | refused: "not signed in to Docker" |
| `sbx login` | **the owner** (opens a browser) | done |

| `sbx policy init deny-all`, then five hosts allowed (the model's API and sign-in hosts, the code host, the package registry) | script | done; the tool refuses to list or create anything until a policy is chosen |
| `sbx create --clone --name v0-trial-1 claude .` on a clone of the fourth project's `light` build | script | VM up in 18 s with the image pull (5 s for the second VM); 10 cores, 11 GB, 20 GB disk, Debian arm64, user `agent` with sudo; the project is a clone inside the VM, the host's copy mounted read-only |
| Project toolchain (Node 24.22.2, pnpm by corepack) | script, one more host allowed for this VM only | 3 s; the image has no Node |
| `pnpm install --frozen-lockfile`, `pnpm test` | script | 2 s; 105 of 105 pass in 3.4 s (the comparison's report: 3.5 to 4.2 s on the host) |
| Pinned headless browser (`npx playwright install --with-deps chromium`), then `screens/capture.mjs` | script, four more hosts allowed for this VM, one of them removed again afterwards | install 11 s; 9 of 9 states captured in 8 s; no workaround |
| Mutation pass, 60 mutants | script | 573 s against 900 s on the host; the same verdict on all 60 (53 killed, 7 survive); one mutant hung to the 300 s limit where two did on the host; over the 58 that hung on neither, 269 s against 300 s |

### Controls checked so far

| Check | Result |
|---|---|
| A host outside the allowlist | refused (403 from the proxy), and listed in `sbx policy log` with the rule that decided |
| A redirect to a host outside the allowlist | refused, with "Approval required for <host>" |
| A rule removed | the host is refused again (the removal needs `--force`) |
| Going round the proxy (a direct connection, by name or by address) | no route |
| A rule scoped to one VM | not in force in the other (the host allowed for VM 1 is refused in VM 2) |
| VM 2 reaching VM 1 | no route, no ping |
| VM 1's files and installs in VM 2 | absent |
| The code host's token inside the VM | a placeholder: its hash differs from the host's token |

Found on the way: the agent's kit adds eight allowed hosts of its own
to every VM (the model's hosts, its download host, the image's package
mirror), not editable; a download host for a browser can be a shared
storage host (anyone's bucket), so it is allowed only for the install
and removed after.

### Waiting on the owner (the hand steps)

1. Signing the model in inside the VM.
2. A token for the code host, scoped to the one repository, typed into
   the tool's secret store (`sbx secret set`), for the push to a scratch
   branch. The quick route (`gh auth token`) would hand over a token
   that reaches every repository, which the bar's fourth line rules out.

Read from the installed tool's help, not yet tried: `sbx create --clone
claude .` runs the agent on a clone inside the VM and the host fetches
its commits from a remote named `sandbox-<name>`; `sbx exec`, `sbx cp`
and `sbx rm --force` cover run, copy out and destroy; `--no-input`
makes every command fail instead of prompting, which a launcher needs.
The documentation lists Windows 11 (`winget install -h Docker.sbx`, no
admin; the Windows Hypervisor Platform feature must be on) and Ubuntu
24.04 (KVM, the user in the `kvm` group) as supported, so one backend
may cover the three systems; neither is tried yet.
