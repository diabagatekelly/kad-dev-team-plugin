// Which lines of a TypeScript file hold runtime code once Node strips the types?
//
// validation_gate.py asks this for the coverage check: Node's coverage table
// lists only files the tests loaded, so a module that is nothing but types
// (a port interface, erased at runtime) never appears, and under
// --experimental-transform-types the erased lines of a loaded module (a type
// alias above a class) are counted as uncovered. Neither is a coverage gap.
//
// Usage: node --no-warnings ts_runtime_lines.mjs <file> [<file> ...]
// Prints one JSON array: per file {"file", "mode": "strip" | "transform",
// "lines": [1-based line numbers with runtime code]}, or {"file", "error"}
// when Node cannot parse it (the gate then counts every line). JSX is one
// such case: Node's type stripping takes no `.tsx`, in either mode, so a
// `.tsx` file is counted as it was before this helper existed.
//
// Strip mode keeps every line in place, so a runtime line is one that holds
// something other than whitespace and comments. Comments are found by
// walking the text with a small state machine (string, template literal
// with its `${}` interpolations, regular expression, line comment, block
// comment), not by a regular expression: `//` or `/*` inside a string or a
// template literal is code, and a comment marker inside a regex literal is
// code too. Strip mode refuses a few constructs (parameter properties,
// enums, namespaces); transform mode takes those, and its source map says
// which original lines produced any output at all.
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

// Characters after which a `/` starts a regular expression rather than a
// division: the end of an expression is a word, a number, `)`, `]` or `}`.
const BEFORE_DIVISION = /[\w$)\]}]/;

function runtimeLinesFromText(text) {
  const hasCode = [];
  let line = 0;
  let state = 'code';            // code | line-comment | block-comment | single | double | template | regex
  let templateDepth = [];        // one entry per open template literal: its `${}` nesting depth
  let lastSignificant = '';      // last non-space character seen in code, for the regex/division call
  let regexInClass = false;
  const mark = () => { hasCode[line] = true; };
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const next = text[i + 1];
    if (ch === '\n') {
      line++;
      if (state === 'line-comment' || state === 'single' || state === 'double' || state === 'regex') {
        state = 'code';          // an unterminated string, regex or line comment ends with its line
      }
      continue;
    }
    switch (state) {
      case 'code':
        if (ch === '/' && next === '/') { state = 'line-comment'; i++; break; }
        if (ch === '/' && next === '*') { state = 'block-comment'; i++; break; }
        if (/\s/.test(ch)) break;
        mark();
        if (ch === "'") { state = 'single'; }
        else if (ch === '"') { state = 'double'; }
        else if (ch === '`') { state = 'template'; templateDepth.push(0); }
        else if (ch === '/' && !BEFORE_DIVISION.test(lastSignificant)) { state = 'regex'; regexInClass = false; }
        else if (ch === '}' && templateDepth.length && templateDepth[templateDepth.length - 1] > 0) {
          // closing a `${ ... }` interpolation: back into the template text
          templateDepth[templateDepth.length - 1]--;
          if (templateDepth[templateDepth.length - 1] === 0) state = 'template';
        }
        lastSignificant = ch;
        break;
      case 'line-comment':
        break;
      case 'block-comment':
        if (ch === '*' && next === '/') { state = 'code'; i++; }
        break;
      case 'single':
      case 'double':
        mark();
        if (ch === '\\') { i++; if (text[i] === '\n') line++; break; }
        if ((state === 'single' && ch === "'") || (state === 'double' && ch === '"')) state = 'code';
        break;
      case 'template':
        mark();
        if (ch === '\\') { i++; if (text[i] === '\n') line++; break; }
        if (ch === '`') { state = 'code'; templateDepth.pop(); lastSignificant = '`'; break; }
        if (ch === '$' && next === '{') { templateDepth[templateDepth.length - 1]++; state = 'code'; i++; lastSignificant = '{'; }
        break;
      case 'regex':
        mark();
        if (ch === '\\') { i++; break; }
        if (ch === '[') regexInClass = true;
        else if (ch === ']') regexInClass = false;
        else if (ch === '/' && !regexInClass) { state = 'code'; lastSignificant = '/'; }
        break;
      default:
        break;
    }
  }
  const lines = [];
  hasCode.forEach((v, idx) => { if (v) lines.push(idx + 1); });
  return lines.filter((n) => !/^\s*export\s*\{\s*\}\s*;?\s*$/.test(text.split('\n')[n - 1] || ''));
}

const VLQ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

function decodeVlq(segment) {
  const fields = [];
  let value = 0, shift = 0;
  for (const ch of segment) {
    const digit = VLQ.indexOf(ch);
    if (digit < 0) throw new Error(`bad VLQ character ${ch}`);
    value += (digit & 31) << shift;
    if (digit & 32) {
      shift += 5;
    } else {
      fields.push(value & 1 ? -(value >>> 1) : value >>> 1);
      value = 0;
      shift = 0;
    }
  }
  return fields;
}

function runtimeLinesFromMap(transformed) {
  const m = /\/\/# sourceMappingURL=data:application\/json;base64,([A-Za-z0-9+/=]+)/.exec(transformed);
  if (!m) throw new Error('transform output carries no inline source map');
  const map = JSON.parse(Buffer.from(m[1], 'base64').toString('utf8'));
  const lines = new Set();
  let origLine = 0;
  for (const generatedLine of map.mappings.split(';')) {
    for (const segment of generatedLine.split(',')) {
      if (!segment) continue;
      const fields = decodeVlq(segment);
      if (fields.length >= 4) {
        origLine += fields[2];
        lines.add(origLine + 1);
      }
    }
  }
  return [...lines].sort((a, b) => a - b);
}

// `--text FILE`: report the runtime lines of a file that is already plain
// JavaScript or stripped TypeScript, without stripping (for checking the
// comment walk on its own).
const args = process.argv.slice(2);
const results = [];
if (args[0] === '--text') {
  for (const file of args.slice(1)) {
    results.push({ file, mode: 'text', lines: runtimeLinesFromText(readFileSync(file, 'utf8')) });
  }
} else {
  for (const file of args) {
    let source;
    try {
      source = readFileSync(file, 'utf8');
    } catch (e) {
      results.push({ file, error: e.message });
      continue;
    }
    try {
      results.push({ file, mode: 'strip', lines: runtimeLinesFromText(stripTypeScriptTypes(source, { mode: 'strip' })) });
    } catch (stripError) {
      try {
        const transformed = stripTypeScriptTypes(source, { mode: 'transform', sourceMap: true, sourceUrl: file });
        results.push({ file, mode: 'transform', lines: runtimeLinesFromMap(transformed) });
      } catch (e) {
        results.push({ file, error: `${stripError.message}; ${e.message}` });
      }
    }
  }
}
process.stdout.write(JSON.stringify(results) + '\n');
