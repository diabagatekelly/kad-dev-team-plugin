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
check "check: shows the set (writes, never reads, network, chrome, audit)" bash -c '[ "$(printf "%s" "$1" | grep -c "  writes \|  never reads \|  network \|  chrome \|  audit ")" = 5 ]' _ "$out"
check "check: nothing written" [ ! -f "$conf" ]
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
check "approve: starts srt with the settings file and claude --chrome" bash -c 'grep -q "srt-stub: --settings $2/conf/srt/proj-[0-9a-f]*.json claude --plugin-dir $3 --chrome" <<< "$1"' _ "$out" "$T" "$root"
check "approve: KAD_CHROME=1 in the session" has "$out" "KAD_CHROME=1"
check "approve: KAD_GH_DIR names the launcher's gh folder" has "$out" "KAD_GH_DIR=$T/conf/gh"
check "approve: GH_TOKEN from the gh login" has "$out" "GH_TOKEN=ghs_stub_token"
check "approve: KAD_SRT_SETTINGS exported" has "$out" "KAD_SRT_SETTINGS=$T/conf/srt/"
check "approve: audit on by default" has "$out" "KAD_AUDIT=1"
check "approve: stored file lists the project" python3 -I -c '
import json, sys; d = json.load(open(sys.argv[1])); p = d["projects"][sys.argv[2]]
assert p["approved"].endswith("Z") and p["domains"] == ["registry.npmjs.org"], p
assert d["audit"] is True and d["audit_repo"] == "" and d["domains"] == ["extra.example"], d
' "$conf" "$T/proj"
check "approve: stored file owner-readable only" bash -c '[ "$(stat -f %Lp "$1" 2>/dev/null || stat -c %a "$1")" = 600 ]' _ "$conf"
settings="$(ls "$T"/conf/srt/proj-*.json)"
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
assert d["projects"][sys.argv[2]]["domains"] == ["registry.npmjs.org"]
assert d["domains"] == ["extra.example"] and d["audit"] is True, d
' "$conf" "$T/proj"

# 7. A changed set is shown again for one yes.
printf '[project]\nname = "proj"\n' > "$T/proj/pyproject.toml"
cp "$conf" "$T/conf.before"
run /dev/null
check "changed set, no terminal: exit 2" [ "$rc" = 2 ]
check "changed set: names the change" has "$out" "now call for other domains"
check "changed set: file untouched" cmp -s "$conf" "$T/conf.before"
run /dev/null --yes
check "changed set --yes: exit 0" [ "$rc" = 0 ]
check "changed set --yes: pypi stored with the approval" python3 -I -c '
import json, sys; d = json.load(open(sys.argv[1]))
assert d["projects"][sys.argv[2]]["domains"] == ["registry.npmjs.org", "pypi.org", "files.pythonhosted.org"], d
' "$conf" "$T/proj"
check "changed set --yes: pypi in the settings" bash -c 'grep -q files.pythonhosted.org "$1"' _ "$settings"

# 8. --no-chrome: the bridge stays closed, claude starts with --no-chrome.
run /dev/null --no-chrome
check "no-chrome: exit 0" [ "$rc" = 0 ]
check "no-chrome: claude --no-chrome" has "$out" "claude --plugin-dir $root --no-chrome"
check "no-chrome: KAD_CHROME unset" bash -c '! grep -q "KAD_CHROME=" <<< "$1"' _ "$out"
check "no-chrome: no bridge host in the settings" bash -c '! grep -q bridge.claudeusercontent.com "$1"' _ "$settings"

# 9. The old restart flags are refused with the one line to run instead.
run /dev/null --relaunch
check "relaunch: refused" bash -c '[ "$1" = 2 ] && grep -q "gone since 0.14.0" <<< "$2"' _ "$rc" "$out"
run /dev/null --prepare
check "prepare: refused" bash -c '[ "$1" = 2 ] && grep -q "gone since 0.14.0" <<< "$2"' _ "$rc" "$out"

# 10. Nothing in the launcher removes the stored file or opens a window.
check "source: no rm of the stored file" bash -c '! grep -nE "rm -r?f? *\"?\\\$conf\"?" "$1"' _ "$kad"
check "source: no osascript, no terminal window" bash -c '! grep -qE "osascript|x-terminal-emulator|gnome-terminal" "$1"' _ "$kad"

echo
if [ "$fails" = 0 ]; then echo "kad test: PASS"; else echo "kad test: FAIL ($fails)"; exit 1; fi
