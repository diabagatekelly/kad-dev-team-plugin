#!/usr/bin/env bash
# Proves the fixture is what answer-key.md says it is:
#   1. the app type-checks (so no accidental errors distract a reviewer),
#   2. the planted runtime import cycle (lending/loan.ts <-> loan-policy.ts)
#      really crashes at module load,
#   3. the type-only cycle (lending/hold.ts <-> hold-queue.ts) really doesn't,
#   4. the clean catalog module loads,
#   5. the test suite under test/ passes.
# Run from anywhere: bash evals/fixtures/library-app/verify.sh
set -euo pipefail

app="$(cd "$(dirname "${BASH_SOURCE[0]}")/app" && pwd)"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

echo "== typecheck + compile"
npm install --prefix "$out/deps" --no-save --no-audit --no-fund --silent typescript@5 @types/node@24
(cd "$app" && "$out/deps/node_modules/.bin/tsc" -p tsconfig.json --outDir "$out" --typeRoots "$out/deps/node_modules/@types")
echo "ok: tsc clean"

# The vendor packages in types/vendor.d.ts are fictional; give the compiled
# output just enough runtime for the module-load checks below.
stub() { mkdir -p "$out/node_modules/$1"; printf '%s\n' "$2" > "$out/node_modules/$1/index.js"; }
stub date-fns-lite 'const ms=864e5;exports.addDays=(d,n)=>new Date(d.getTime()+n*ms);exports.differenceInCalendarDays=(a,b)=>Math.round((a-b)/ms);exports.isBefore=(a,b)=>a<b;exports.startOfDay=(d)=>new Date(d.getFullYear(),d.getMonth(),d.getDate());'
stub pg-orm 'class PgError extends Error{}class PgClient{constructor(o){this.o=o}async query(){return []}async end(){}}class OrmRow{async save(){}async remove(){}}class OrmRepository{constructor(c,t){this.t=t}async findOne(){return null}async findMany(){return []}async insert(v){return v}}module.exports={PgError,PgClient,OrmRow,OrmRepository};'
stub express-lite 'class Router{use(){}get(){}post(){}}exports.Router=Router;exports.rateLimit=()=>async(q,s,n)=>n();exports.createServer=()=>({listen(){}});'
stub monitor-sdk 'exports.MonitorClient=class{constructor(d){}captureException(){}};'
stub mail-sdk 'exports.MailClient=class{constructor(k){}async send(){return{id:"m"}}};'
stub sms-sdk 'exports.SmsError=class extends Error{};exports.SmsClient=class{constructor(a,b,o){}async send(){return{sid:"s"}}};'
stub stripe-sdk 'class StripeError extends Error{}exports.StripeError=StripeError;exports.StripeClient=class{constructor(k){this.charges={async create(){return{id:"c",amount:0,status:"succeeded"}},async list(){return []}};this.refunds={async create(){return{id:"r"}}}}};'

echo "== runtime cycle must crash (lending/loan.ts <-> loan-policy.ts)"
if node -e "require('$out/lending/loan.js')" 2>"$out/loan.err"; then
  echo "FAIL: lending/loan.js loaded without error; the planted runtime cycle is gone"
  exit 1
fi
grep -q "is not a constructor\|before initialization" "$out/loan.err" \
  || { echo "FAIL: loan.js failed for an unexpected reason:"; cat "$out/loan.err"; exit 1; }
echo "ok: crashes with: $(grep -m1 -o 'TypeError.*\|ReferenceError.*' "$out/loan.err")"

echo "== type-only cycle must load (lending/hold.ts <-> hold-queue.ts)"
node -e "const { Hold } = require('$out/lending/hold.js'); if (typeof Hold !== 'function') throw new Error('Hold missing')"
echo "ok: hold.js loads"

echo "== clean module loads (catalog)"
node -e "const { SearchCatalog } = require('$out/catalog/search-catalog.js'); if (typeof SearchCatalog !== 'function') throw new Error('SearchCatalog missing')"
echo "ok: catalog loads"

echo "== test suite passes (test/)"
(cd "$out" && node --test test/*.test.js >"$out/test.log" 2>&1) || { echo "FAIL: tests"; cat "$out/test.log"; exit 1; }
echo "ok: $(grep -m1 '^ℹ pass' "$out/test.log")"

echo "all checks passed"
