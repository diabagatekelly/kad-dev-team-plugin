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

### A real session inside the VM

| Step | By | Result |
|---|---|---|
| Signing the model in inside the VM (`sbx run --name v0-trial-1`, `/login`) | **the owner** | done |
| `sbx exec v0-trial-1 claude -p --dangerously-skip-permissions "<task>"` | script | the session ran the suite (105 pass), wrote a file and committed it on a scratch branch, 18 s, no prompt, no workaround |
| `sbx cp v0-trial-1:/home/agent/.claude/projects <host folder>` | script | both transcript files copied out, with their usage records |
| `git fetch sandbox-v0-trial-1` on the host | script | the VM's commit is on the host, with no code-host token in the VM |

The last row matters for the design: the host can fetch what the VM
committed and push it itself, so a session that only builds needs no
push credential inside the VM at all. A token in the VM is needed only
if the session inside is to open the pull request, watch its checks and
answer its review.

### The code host's token, two at once, teardown

| Step | By | Result |
|---|---|---|
| A token for the one repository, stored for VM 1 only (`sbx secret set github --sandbox v0-trial-1`) | **the owner** | done |
| `git push origin <scratch branch>` from inside VM 1 | script | pushed in 1 s; the branch deleted again afterwards |
| Reading and pushing to another of the owner's repositories from VM 1 | script | both refused (403) |
| The token as the VM sees it | script | still the placeholder: the same hash as before the secret was stored |
| The code host from VM 2, which the secret is not scoped to | script | no credential |
| A session in VM 1 and one in VM 2 at the same time | script | VM 1 answered (20 s); VM 2, created before the model's sign-in, was not signed in |
| A third VM created after the sign-in | script | signed in with no new login: the sign-in is once per machine, for VMs created after it |
| `sbx rm --force` on the three VMs | script | 0.7 s; no containers, no volumes, the VM-scoped secret and rules gone, the VM's git remote gone from the host's clone. Left on the host: the base image (1.5 GB, a cache), the model's sign-in, the global policy |
| The same route through `vm.sh` alone (policy, create, allow, exec, run, out, destroy) | script | 18 s from the VM existing to its removal, a session run and its transcript copied out |

## 2026-11-20, further probes on the Mac (the owner: "fully answer all the remaining questions regarding the VM", the browser first)

### The browser

| Probe | Result |
|---|---|
| Branded Google Chrome in the VM | not available: no build for Linux on Arm64 (the installer refuses). What is there is Chrome for Testing 156, the same engine, as a full browser and as a headless shell |
| A script driving the full browser, headless (open the app, list the buttons, press Tab and read the focus, read computed colours, click, screenshot before and after, print to PDF) | all done, 0.8 s |
| The same with the headless shell | all done, 0.7 s; the same pixels as the full browser on this screen |
| The full browser headed, on a virtual display (`xvfb-run`, two packages from the image's own mirror) | works; the page does not see a headless browser |
| A session in the VM driving the browser itself, through browser tools over MCP (`@playwright/mcp`, pointed at the installed browser) | navigate, snapshot, screenshot, key press, snapshot, click, snapshot, screenshot: 38 s; its account of the page matches the screenshot it took |
| The tool's `claude.chrome` setting | left off: it lets the session reach the host's own browser tabs, which is outside the VM |

### The rest

| Question | Result |
|---|---|
| CPU and memory | set at creation (`--cpus 6 --memory 8g` gave 6 cores and 7 GB); the default is every core and half the host's memory |
| A plugin inside the VM | a folder mounted read-only and passed with `--plugin-dir` loads (the session listed its 38 skills) |
| Subagent transcripts | kept, in a `subagents/` folder beside the session's file, and copied out with the rest |
| The model's credentials | supplied outside the VM: a request to the model's API from the VM with no credential at all, or with a made-up one, is answered as signed in. So the VM needs no real token; the other side of it is that any process in the VM can use the owner's subscription on that one host |
| A secret for any other host (`sbx secret set-custom`, tried with a made-up value and an echo service) | the VM holds a placeholder; the proxy puts the real value into any header of a request to the named host; a placeholder in a JSON body or in the URL goes out unchanged. A provider must take its secret in a header |
| An idle VM | stops when no command is attached to it and starts again on the next one; its disk is kept, its processes are not. A server started in one command is gone in the next: the session and anything it needs running are one command |
| A prepared image | `sbx template save` of a stopped VM (30 s) keeps the toolchain and the browser; a VM from it is up in 4 s and captures the 9 screens with only the default hosts allowed |
| Two VMs under load | a full mutation pass in each at the same time: 661 s and 694 s against 573 s for one alone (15% and 21% slower), the same verdict on all 60 mutants in both (53 killed, the same 7 survivors) |
| A caller's own key for the model | replaced as well: a made-up key is answered as the owner. The tool adds credentials on the model's API host only; its other allowed hosts get none |

Read from the installed tool's help, not yet tried: `sbx create --clone
claude .` runs the agent on a clone inside the VM and the host fetches
its commits from a remote named `sandbox-<name>`; `sbx exec`, `sbx cp`
and `sbx rm --force` cover run, copy out and destroy; `--no-input`
makes every command fail instead of prompting, which a launcher needs.
The documentation lists Windows 11 (`winget install -h Docker.sbx`, no
admin; the Windows Hypervisor Platform feature must be on) and Ubuntu
24.04 (KVM, the user in the `kvm` group) as supported, so one backend
may cover the three systems; neither is tried yet.
