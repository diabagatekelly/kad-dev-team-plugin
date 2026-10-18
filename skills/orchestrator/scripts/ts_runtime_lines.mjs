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
// when Node cannot parse it (the gate then counts every line).
//
// Strip mode keeps every line in place, so a runtime line is one that is
// not blank once types and comments are gone. Strip mode refuses a few
// constructs (parameter properties, enums, namespaces); transform mode
// takes those, and its source map says which original lines produced any
// output at all.
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';

function withoutComments(text) {
  // Block comments become the same number of newlines so lines keep their numbers.
  return text
    .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))
    .replace(/(^|[^:])\/\/.*$/gm, '$1');
}

function runtimeLinesFromText(stripped) {
  const lines = [];
  withoutComments(stripped).split('\n').forEach((line, i) => {
    const code = line.trim();
    if (code && !/^export\s*\{\s*\}\s*;?$/.test(code)) lines.push(i + 1);
  });
  return lines;
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

const results = [];
for (const file of process.argv.slice(2)) {
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
process.stdout.write(JSON.stringify(results) + '\n');
