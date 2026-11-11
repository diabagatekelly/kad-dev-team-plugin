// A fixed-width table of statement rows for the desk's printed copy.

export interface TableRow {
  cells: string[];
}

export interface TableOptions {
  headers: string[];
  maxWidth?: number;
  align?: ("left" | "right")[];
  gutter?: number;
}

export function renderTable(rows: TableRow[], options: TableOptions): string {
  const headers = options.headers;
  const columns = headers.length;
  const gutter = " ".repeat(options.gutter ?? 2);
  const align = options.align ?? headers.map(() => "left" as const);
  const maxWidth = options.maxWidth ?? 120;

  // Measure every column by its widest cell, header included.
  const widths: number[] = headers.map((h) => h.length);
  for (const row of rows) {
    for (let i = 0; i < columns; i += 1) {
      const cell = row.cells[i] ?? "";
      if (cell.length > widths[i]) {
        widths[i] = cell.length;
      }
    }
  }

  // Shrink the widest columns first until the line fits the page.
  let lineWidth = widths.reduce((a, b) => a + b, 0) + gutter.length * (columns - 1);
  while (lineWidth > maxWidth) {
    let widest = 0;
    for (let i = 1; i < columns; i += 1) {
      if (widths[i] > widths[widest]) {
        widest = i;
      }
    }
    if (widths[widest] <= 4) {
      break;
    }
    widths[widest] -= 1;
    lineWidth -= 1;
  }

  // Lay out one line, padding or truncating each cell to its column.
  const layout = (cells: string[]): string => {
    const parts: string[] = [];
    for (let i = 0; i < columns; i += 1) {
      let cell = cells[i] ?? "";
      if (cell.length > widths[i]) {
        cell = widths[i] > 1 ? `${cell.slice(0, widths[i] - 1)}…` : cell.slice(0, widths[i]);
      }
      if (align[i] === "right") {
        parts.push(cell.padStart(widths[i]));
      } else {
        parts.push(cell.padEnd(widths[i]));
      }
    }
    return parts.join(gutter).trimEnd();
  };

  const out: string[] = [];
  out.push(layout(headers));
  const rule: string[] = [];
  for (let i = 0; i < columns; i += 1) {
    rule.push("-".repeat(widths[i]));
  }
  out.push(rule.join(gutter));
  for (const row of rows) {
    out.push(layout(row.cells));
  }

  // A footer with the row count, right-aligned to the table's width.
  const count = `${rows.length} row${rows.length === 1 ? "" : "s"}`;
  const tableWidth = out[1].length;
  if (count.length < tableWidth) {
    out.push(count.padStart(tableWidth));
  } else {
    out.push(count);
  }
  return out.join("\n");
}
