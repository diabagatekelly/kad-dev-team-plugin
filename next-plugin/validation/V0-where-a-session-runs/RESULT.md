# V0 result on the Mac (2026-11-20): the bar holds here; Windows not yet tried

Docker Sandboxes 0.54.0 as the first backend, driven by `vm.sh`. Every
row of `LOG.md` is a command that was run.

| Line of the bar | On the Mac |
|---|---|
| 1. A running session with only the hand steps | met. Three hand steps, each once per machine: `sbx login`, signing the model in inside one VM, and (only for a push from inside) storing a token. No admin password, no reboot |
| 2. No sandbox workaround | met. No git shim, no proxy approval; the headless browser ran as installed |
| 3. No step slower than before | met against the figures on record, with a caveat below: suite 3.4 s (3.5 to 4.2), mutation pass 573 s (900), 9 screens captured in 8 s, push 1 s |
| 4. The controls | met for every check made (below), with one left open |
| 5. Two at once share nothing | met for rules, files, credentials and reachability, and under load (two mutation passes at once, the same verdicts, 15% and 21% slower); the model's sign-in and its usage limit are shared by design |
| 6. The same on Windows | not tried |

## Controls checked

A host outside the allowlist is refused and logged; so is a redirect to
one; a removed rule bites; there is no route round the proxy; a rule or
a secret scoped to one VM is not in force in another; one VM cannot
reach another; the code host's token inside the VM is a placeholder,
pushes to its one repository and is refused on another; after removal
nothing of the VM is left but a cached base image.

## What the trial changes in the design

- **The host can fetch what the VM committed** (`git fetch
  sandbox-<name>`), so a session that only builds needs no push
  credential inside the VM; the launcher pushes from the host. A token
  inside is needed only if the session there is to open the pull
  request and watch it. Which of the two is the owner's, at V9.
- **One backend may cover the three systems:** the tool's install page
  lists Windows 11 and Ubuntu 24.04 as supported.
- **The image has no Node and no browser:** each project's toolchain is
  installed at create time (about 20 s here), with its download hosts
  allowed for that VM. A prepared image per project would remove that.
- **Allowing a host is the unit of approval:** a refused host answers
  "Approval required", and the tool has an approval queue, which fits
  "any other host only with the owner's approval".

## Caveats and what is open

- **The speed line** is against figures recorded on 2026-11-19, when
  two arms shared the machine, not against a fresh run under `srt`.
- **The model's credentials** are added outside the VM: a request from
  inside with no credential, or a made-up one, is answered as the
  owner. So the token cannot be taken out of the VM, and any process in
  the VM can use the owner's subscription while the VM lives. What the
  credentials file inside actually holds was not read (refused by this
  session's permission rules, not worked around), and a real key of
  another account was not tried.
- **The browser:** driven by a script (full Chrome for Testing
  headless, the headless shell, and headed on a virtual display) and by
  a session through browser tools; screenshots from each. Branded
  Chrome has no build for Linux on Arm64, which is what the VM is on
  this Mac.
- **Two at once under load:** two full mutation passes together ran 15%
  and 21% slower than one alone, with the same verdicts.
- **An idle VM stops** and keeps its disk but not its processes: a
  session and whatever it needs running are one command.
- **A prepared image** (toolchain and browser installed, saved in 30 s)
  brings a VM up in 4 s with only the default hosts allowed.
- **A secret for another host** is swapped in by the proxy in headers
  only, not in a body or a URL.
- **The kit's own eight allowed hosts** cannot be edited.
- **The tool is at 0.54** with weekly releases; removing a rule needed
  `--force`, and a VM created before the sign-in stays signed out.
- **Left for the owner to tidy:** the fine-grained token made for the
  trial can be revoked on the code host.
