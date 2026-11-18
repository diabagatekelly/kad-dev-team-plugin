#!/usr/bin/env bash
# The launcher's test (bin/kad), run without a model and without the real
# tools: `claude`, `srt` and `gh` are stubs on PATH that print what they
# were handed, HOME and the config directory are a scratch tree, and the
# project is a scratch repository with a package.json. It covers what P1 of
# .synthesis/handoff-slice2.md made the launcher promise:
#
# - the first run on a project shows the permission set and asks one yes;
#   with no terminal and no --yes it stops and stores nothing;
# - --yes approves the set: the stored file lists the project with the
#   domains its manifests called for, the srt settings carry the launcher's
#   own folders and the bridge hosts, Chrome's native-messaging files are
#   written when missing, and the session gets KAD_CHROME, KAD_GH_DIR and
#   KAD_SRT_SETTINGS;
# - the second run asks nothing and starts;
# - --reset never deletes the file: declined (no terminal) it is byte for
#   byte what it was (0.13.1's --reset removed it before asking, and an
#   interrupted reset lost every answer: the 2026-11-08 first-run questions);
#   approved, it is rewritten whole with the other projects' entries kept;
# - a changed set (a manifest that now calls for another registry) is shown
#   again for one yes;
# - --no-chrome closes the bridge and starts claude with --no-chrome;
# - --relaunch and --prepare are refused with the one line to run instead;
# - nothing in the script removes the stored file.
#
# Usage: bash evals/tools/kad_test.sh
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
kad="$root/bin/kad"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
export HOME="$T/home" KAD_CONFIG_DIR="$T/conf" KAD_AUDIT_DIR="$T/audit"
unset CLAUDE_CONFIG_DIR CLAUDE_CODE_TMPDIR GH_TOKEN KAD_CHROME KAD_SRT_SETTINGS KAD_GH_DIR 2>/dev/null || true
mkdir -p "$HOME/Library/Application Support/Google/Chrome" "$HOME/.config/google-chrome" "$T/bin" "$T/proj"
cat > "$T/bin/claude" <<'EOF'
#!/bin/sh
echo "claude-stub: $*"
EOF
cat > "$T/bin/srt" <<'EOF'
#!/bin/sh
echo "srt-stub: $*"
env | grep -E '^(KAD_|GH_TOKEN=|GH_CONFIG_DIR=|CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=)' | sort
EOF
cat > "$T/bin/gh" <<'EOF'
#!/bin/sh
[ "$1 $2" = "auth token" ] && echo ghs_stub_token
exit 0
EOF
chmod +x "$T/bin/"*
export PATH="$T/bin:$PATH"
printf '{"name":"proj","scripts":{"test":"node --test"}}\n' > "$T/proj/package.json"
conf="$T/conf/launcher.json"
fails=0
pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; fails=$((fails + 1)); }
check() {  # check <name> <condition...>
  local name="$1"; shift
  if "$@"; then pass "$name"; else fail "$name"; fi
}
has() { grep -q -- "$2" <<< "$1"; }
run() {  # run <stdin> <args...> -> output in $out, status in $rc
  local stdin="$1"; shift
  rc=0; out="$(cd "$T/proj" && "$kad" "$@" 2>&1 < "$stdin")" || rc=$?
}

# 1. --check on a fresh machine: prints the set, writes nothing, starts nothing.
run /dev/null --check
check "check: exit 0" [ "$rc" = 0 ]
check "check: names the first run" has "$out" "first run on this machine"
check "check: shows the set with its values" bash -c '
  grep -q "  writes       the project; the audit directory $2/audit" <<< "$1" && grep -q "  never reads .*~/.ssh.*~/.config/gh" <<< "$1" \
  && grep -q "  network .*api.anthropic.com.*github.com.*bridge.claudeusercontent.com.*registry.npmjs.org" <<< "$1" \
  && grep -q "  credential .*GH_TOKEN" <<< "$1" && grep -q "  local ports  allowed" <<< "$1" \
  && grep -q "  chrome       on" <<< "$1" && grep -q "  audit        on.*$2/audit" <<< "$1"' _ "$out" "$T"
check "check: nothing written, not even the config directory" [ ! -e "$T/conf" ]
check "check: nothing started" bash -c '! grep -q srt-stub <<< "$1"' _ "$out"

# 2. First run with no terminal and no --yes: stops, stores nothing.
run /dev/null
check "first run, no terminal: exit 2" [ "$rc" = 2 ]
check "first run, no terminal: says how to approve" has "$out" "kad --yes to approve"
check "first run, no terminal: nothing stored" [ ! -f "$conf" ]
check "first run, no terminal: nothing started" bash -c '! grep -q srt-stub <<< "$1"' _ "$out"

# 3. --yes approves the set and starts.
run /dev/null --yes --domain extra.example
check "approve: exit 0" [ "$rc" = 0 ]
check "approve: says stored" has "$out" "approved and stored in $conf"
check "approve: starts srt with a per-run settings file and claude --chrome" bash -c 'grep -q "srt-stub: --settings $2/conf/srt/proj-[0-9a-f]*\.[0-9]*\.json claude --plugin-dir $3 --chrome" <<< "$1"' _ "$out" "$T" "$root"
check "approve: KAD_CHROME=1 in the session" has "$out" "KAD_CHROME=1"
check "approve: KAD_GH_DIR names the launcher's gh folder" has "$out" "KAD_GH_DIR=$T/conf/gh"
check "approve: GH_TOKEN from the gh login" has "$out" "GH_TOKEN=ghs_stub_token"
settings="$(sed -n 's/^srt-stub: --settings \([^ ]*\) .*/\1/p' <<< "$out")"
check "approve: KAD_SRT_SETTINGS is exactly the file srt was given, and it exists" bash -c 'grep -qx "KAD_SRT_SETTINGS=$2" <<< "$1" && [ -f "$2" ]' _ "$out" "$settings"
check "approve: KAD_AUDIT_DIR exported" has "$out" "KAD_AUDIT_DIR=$T/audit"
check "approve: audit on by default" has "$out" "KAD_AUDIT=1"
check "approve: stored file lists the project with its answers and the approved set" python3 -I -c '
import json, sys; d = json.load(open(sys.argv[1])); p = d["projects"][sys.argv[2]]
assert p["approved"].endswith("Z") and p["domains"] == ["extra.example"] and p["audit"] is True and p["audit_repo"] == "", p
assert p["set"] == {"audit": True, "audit_repo": "", "chrome": True, "domains": ["extra.example", "registry.npmjs.org", "results-receiver.actions.githubusercontent.com"], "github": True, "local": True}, p["set"]
assert d["audit"] is True and d["audit_repo"] == "" and d["domains"] == ["extra.example"], d   # the root: the defaults for the next project
' "$conf" "$T/proj"
check "approve: stored file owner-readable only" bash -c '[ "$(stat -f %Lp "$1" 2>/dev/null || stat -c %a "$1")" = 600 ]' _ "$conf"
check "approve: settings allow the launcher's folders and carry the domains" python3 -I -c '
import json, sys; s = json.load(open(sys.argv[1])); T = sys.argv[2]
w = s["filesystem"]["allowWrite"]; d = s["network"]["allowedDomains"]
assert T + "/conf/gh" in w and T + "/audit" in w and T + "/proj" in w, w
for x in ("registry.npmjs.org", "extra.example", "bridge.claudeusercontent.com", "mcp-proxy.anthropic.com", "github.com"):
    assert x in d, (x, d)
assert s["network"]["tlsTerminate"]["excludeDomains"] == ["bridge.claudeusercontent.com", "mcp-proxy.anthropic.com"]
assert s["network"]["allowLocalBinding"] is True
' "$settings" "$T"
case "$(uname -s)" in
  Darwin) manifest="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts/com.anthropic.claude_code_browser_extension.json" ;;
  *) manifest="$HOME/.config/google-chrome/NativeMessagingHosts/com.anthropic.claude_code_browser_extension.json" ;;
esac
check "approve: wrote Chrome's native-messaging manifest" [ -f "$manifest" ]
check "approve: the manifest names the host wrapper and the extension" python3 -I -c '
import json, sys; m = json.load(open(sys.argv[1]))
assert m["name"] == "com.anthropic.claude_code_browser_extension" and m["type"] == "stdio", m
assert m["path"] == sys.argv[2] and m["allowed_origins"] == ["chrome-extension://fcoeoabgfenejglbffodgkkbkcdhcgfn/"], m
' "$manifest" "$HOME/.claude/chrome/chrome-native-host"
check "approve: wrote the host wrapper, executable, exec'ing claude --chrome-native-host" bash -c '[ -x "$1" ] && grep -q "exec .*claude --chrome-native-host" "$1"' _ "$HOME/.claude/chrome/chrome-native-host"
check "approve: said what it wrote" has "$out" "chrome: wrote the native-messaging files"

# 4. The second run asks nothing, prints one line and starts.
run /dev/null
check "second run: exit 0" [ "$rc" = 0 ]
check "second run: one line naming the approval" has "$out" "set approved 20"
check "second run: no set shown" bash -c '! grep -q "  never reads " <<< "$1"' _ "$out"
check "second run: started" has "$out" "srt-stub:"
check "second run: no native-messaging files written again" bash -c '! grep -q "wrote the native-messaging" <<< "$1"' _ "$out"

# 5. --reset declined (no terminal): the file is byte for byte what it was.
cp "$conf" "$T/conf.before"
run /dev/null --reset
check "reset, no terminal: exit 2" [ "$rc" = 2 ]
check "reset, no terminal: shows the set" has "$out" "  never reads "
check "reset, no terminal: file untouched" cmp -s "$conf" "$T/conf.before"
check "reset, no terminal: nothing started" bash -c '! grep -q srt-stub <<< "$1"' _ "$out"

# 6. --reset approved: rewritten whole, the other projects' entries kept.
python3 -I - "$conf" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1])); d["projects"]["/elsewhere/other"] = {"approved": "2026-01-01T00:00:00Z", "domains": []}
json.dump(d, open(sys.argv[1], "w"), indent=2)
EOF
run /dev/null --reset --yes
check "reset --yes: exit 0" [ "$rc" = 0 ]
check "reset --yes: stored again" has "$out" "approved and stored"
check "reset --yes: other project kept, this one re-approved, answers kept" python3 -I -c '
import json, sys; d = json.load(open(sys.argv[1]))
assert "/elsewhere/other" in d["projects"], d
assert d["projects"][sys.argv[2]]["domains"] == ["extra.example"] and d["projects"][sys.argv[2]]["audit"] is True, d
' "$conf" "$T/proj"

# 7. A changed set is shown again for one yes.
printf '[project]\nname = "proj"\n' > "$T/proj/pyproject.toml"
cp "$conf" "$T/conf.before"
run /dev/null
check "changed set, no terminal: exit 2" [ "$rc" = 2 ]
check "changed set: names the widening" has "$out" "wider than the one approved"
check "changed set: names the new domains" has "$out" "domains files.pythonhosted.org, pypi.org"
check "changed set: file untouched" cmp -s "$conf" "$T/conf.before"
run /dev/null --yes
check "changed set --yes: exit 0" [ "$rc" = 0 ]
check "changed set --yes: pypi in the approved set" python3 -I -c '
import json, sys; d = json.load(open(sys.argv[1]))
assert "pypi.org" in d["projects"][sys.argv[2]]["set"]["domains"], d
' "$conf" "$T/proj"
settings="$(sed -n 's/^srt-stub: --settings \([^ ]*\) .*/\1/p' <<< "$out")"
check "changed set --yes: pypi in the settings" bash -c 'grep -q files.pythonhosted.org "$1"' _ "$settings"

# 7b. A per-run --domain widens the set (one yes); a narrower run asks nothing.
run /dev/null --domain more.example
check "per-run domain, no terminal: exit 2 (wider)" bash -c '[ "$1" = 2 ] && grep -q "domains more.example" <<< "$2"' _ "$rc" "$out"
run /dev/null --no-local
check "narrower run (--no-local): starts without a question" bash -c '[ "$1" = 0 ] && grep -q "srt-stub:" <<< "$2"' _ "$rc" "$out"

# 7c. Answers are per project: a second project with audit off and a local
#     audit repository leaves the first project's answers alone, and
#     --audit-repo none is local-only for one run.
git init -q --bare "$T/audit-remote.git"
mkdir -p "$T/proj2"
rc=0; out="$(cd "$T/proj2" && "$kad" --yes --audit-repo "$T/audit-remote.git" 2>&1 < /dev/null)" || rc=$?
check "second project: approved with its own repository" bash -c '[ "$1" = 0 ] && grep -q "KAD_AUDIT_REPO=$3/audit-remote.git" <<< "$2"' _ "$rc" "$out" "$T"
check "second project: the clone was made under the audit directory" [ -d "$T/audit/repo/.git" ]
run /dev/null
check "first project: still no repository, audit on" bash -c 'grep -q "KAD_AUDIT=1" <<< "$1" && ! grep -q "KAD_AUDIT_REPO=" <<< "$1"' _ "$out"
rc=0; out="$(cd "$T/proj2" && "$kad" --audit-repo none 2>&1 < /dev/null)" || rc=$?
check "second project, --audit-repo none: local only for this run" bash -c '[ "$1" = 0 ] && grep -q "KAD_AUDIT=1" <<< "$2" && ! grep -q "KAD_AUDIT_REPO=" <<< "$2"' _ "$rc" "$out"
check "second project: stored repository untouched" python3 -I -c '
import json, sys; d = json.load(open(sys.argv[1])); assert d["projects"][sys.argv[2]]["audit_repo"] == sys.argv[3], d
' "$conf" "$T/proj2" "$T/audit-remote.git"

# 7d. A manifest left invalid is repaired on the next launch, atomically.
printf 'garbage' > "$manifest"
run /dev/null
check "invalid manifest: repaired" python3 -I -c '
import json, sys; m = json.load(open(sys.argv[1])); assert m["path"] == sys.argv[2], m
' "$manifest" "$HOME/.claude/chrome/chrome-native-host"
check "invalid manifest: said so" has "$out" "chrome: wrote the native-messaging files"
check "invalid manifest: no temp file left" bash -c '! ls "$(dirname "$1")"/.com.anthropic.* 2>/dev/null | grep -q .' _ "$manifest"

# 8. --no-chrome: the bridge stays closed, claude starts with --no-chrome.
run /dev/null --no-chrome
check "no-chrome: exit 0" [ "$rc" = 0 ]
settings="$(sed -n 's/^srt-stub: --settings \([^ ]*\) .*/\1/p' <<< "$out")"
check "no-chrome: claude --no-chrome" has "$out" "claude --plugin-dir $root --no-chrome"
check "no-chrome: KAD_CHROME unset" bash -c '! grep -q "KAD_CHROME=" <<< "$1"' _ "$out"
check "no-chrome: no bridge host in the settings" bash -c '! grep -q bridge.claudeusercontent.com "$1"' _ "$settings"

# 8b. GitHub Actions' logs and artifacts: the storage hosts GitHub publishes
#     are allowed by name, never as *.blob.core.windows.net; the approved set
#     records the pattern, so a host GitHub adds later asks nothing.
cat > "$T/bin/gh" <<'EOF'
#!/bin/sh
[ "$1 $2" = "auth token" ] && echo ghs_stub_token
if [ "$1 $2" = "api meta" ]; then
  printf '%s\n' productionresultssa0.blob.core.windows.net productionresultssa17.blob.core.windows.net \
    '*.actions.githubusercontent.com' evil.blob.core.windows.net "${KAD_TEST_MORE:-productionresultssa17.blob.core.windows.net}"
fi
exit 0
EOF
run /dev/null
check "actions hosts, no terminal: exit 2 (wider), naming the pattern" bash -c '[ "$1" = 2 ] && grep -q "domains productionresultssa<N>.blob.core.windows.net" <<< "$2"' _ "$rc" "$out"
check "actions hosts: the set shown counts them and says where the list is" has "$out" "and the 2 storage hosts GitHub publishes, productionresultssa<N>.blob.core.windows.net, listed in $T/conf/actions-hosts"
run /dev/null --yes
settings="$(sed -n 's/^srt-stub: --settings \([^ ]*\) .*/\1/p' <<< "$out")"
check "actions hosts: each published storage host and the results receiver are in the settings" bash -c 'grep -q "\"productionresultssa0.blob.core.windows.net\"" "$1" && grep -q "\"productionresultssa17.blob.core.windows.net\"" "$1" && grep -q "\"results-receiver.actions.githubusercontent.com\"" "$1"' _ "$settings"
check "actions hosts: no wildcard over blob storage, and no name that is not a results host" bash -c '! grep -q "\*.blob.core.windows.net" "$1" && ! grep -q "evil.blob" "$1" && ! grep -q "\*.actions.githubusercontent.com" "$1"' _ "$settings"
rm -f "$T/conf/actions-hosts"
KAD_TEST_MORE=productionresultssa99.blob.core.windows.net run /dev/null
settings="$(sed -n 's/^srt-stub: --settings \([^ ]*\) .*/\1/p' <<< "$out")"
check "actions hosts: a host GitHub adds later is allowed without a question" bash -c '[ "$1" = 0 ] && grep -q "productionresultssa99.blob.core.windows.net" "$2"' _ "$rc" "$settings"

# 8c. A project with the capture package gets Playwright's download hosts
#     (one yes) and a browser folder of its own, out of git's sight.
mkdir -p "$T/proj/screens" "$T/proj/.git/info"
printf '{"name":"screens"}\n' > "$T/proj/screens/package.json"
cat >> "$T/bin/srt" <<'EOF'
env | grep -E '^PLAYWRIGHT_BROWSERS_PATH=' || true
EOF
run /dev/null
check "screens: the browser's download hosts widen the set" bash -c '[ "$1" = 2 ] && grep -q "cdn.playwright.dev" <<< "$2"' _ "$rc" "$out"
run /dev/null --yes
check "screens: the browser folder is inside the project" has "$out" "PLAYWRIGHT_BROWSERS_PATH=$T/proj/screens/.browsers"
check "screens: the folder is excluded from git, once" bash -c '[ "$(grep -cxF "screens/.browsers/" "$1/proj/.git/info/exclude")" = 1 ]' _ "$T"
run /dev/null
check "screens: the second run asks nothing and adds no second exclude line" bash -c '[ "$1" = 0 ] && [ "$(grep -cxF "screens/.browsers/" "$2/proj/.git/info/exclude")" = 1 ]' _ "$rc" "$T"

# 9. The old restart flags are refused with the one line to run instead.
run /dev/null --relaunch
check "relaunch: refused" bash -c '[ "$1" = 2 ] && grep -q "gone since 0.14.0" <<< "$2"' _ "$rc" "$out"
run /dev/null --prepare
check "prepare: refused" bash -c '[ "$1" = 2 ] && grep -q "gone since 0.14.0" <<< "$2"' _ "$rc" "$out"

# 10. Nothing in the launcher removes the stored file or opens a window.
check "source: no rm of the stored file" bash -c '! grep -nE "rm -r?f? *\"?\\\$conf\"?" "$1"' _ "$kad"
check "source: no osascript, no terminal window" bash -c '! grep -qE "osascript|x-terminal-emulator|gnome-terminal" "$1"' _ "$kad"
check "no lock left behind" [ ! -d "$conf.lock" ]

echo
if [ "$fails" = 0 ]; then echo "kad test: PASS"; else echo "kad test: FAIL ($fails)"; exit 1; fi
