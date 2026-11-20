# V0: where a session runs

**Question:** can the plugin set up, with the owner's permission, a
disposable microVM on the owner's machine and run the working session
inside it, so that no sandbox workaround is needed and the controls
(network allowlist, scoped credentials, nothing left behind) hold?

The step's text, the flow and the paper comparison of the four
candidates are in `../../../TODO.md`, V0. First backend tried: Docker
Sandboxes (`sbx`), on the Mac; then the same contract on Windows.

## The bar (2026-11-20)

The one proposed in `TODO.md`, in force unless the owner changes it
before the session inside the VM runs:

1. The script reaches a running session with only the hand steps a
   script cannot do (virtualisation switched on, the tool's sign-in,
   the model's sign-in inside the VM, entering secrets).
2. No sandbox workaround is needed.
3. No step is slower than under `srt` (the suite, the browser walk,
   the push, the mutation pass of the fourth project).
4. Every control check passes: a host outside the allowlist is refused,
   the session's credentials reach nothing beyond their scope, nothing
   of the session is left after it ends.
5. Two sessions at once share nothing inside the VMs.
6. The same holds on the owner's Windows machine.

## What is here

- `vm.sh`: the launcher's verbs, added as the trial reaches them.
- `LOG.md`: what was run, in order, with times and every hand step.
