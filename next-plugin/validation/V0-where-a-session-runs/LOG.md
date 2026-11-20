# V0 trial log

## 2026-11-20, the Mac (macOS 27.2.1, Apple silicon, 10 cores, 24 GB)

| Step | By | Result |
|---|---|---|
| `vm.sh check` | script | `sbx` missing, Homebrew present |
| `vm.sh install --yes` | script, on the owner's word in the session | Docker Sandboxes 0.54.0 installed by Homebrew in 39 s; no admin password asked; runs on macOS 27 (the documentation names 14 or later) |
| `sbx ls` | script | refused: "not signed in to Docker" |
| `sbx login` | **the owner** (opens a browser) | pending |

Read from the installed tool's help, not yet tried: `sbx create --clone
claude .` runs the agent on a clone inside the VM and the host fetches
its commits from a remote named `sandbox-<name>`; `sbx exec`, `sbx cp`
and `sbx rm --force` cover run, copy out and destroy; `--no-input`
makes every command fail instead of prompting, which a launcher needs.
The documentation lists Windows 11 (`winget install -h Docker.sbx`, no
admin; the Windows Hypervisor Platform feature must be on) and Ubuntu
24.04 (KVM, the user in the `kvm` group) as supported, so one backend
may cover the three systems; neither is tried yet.
