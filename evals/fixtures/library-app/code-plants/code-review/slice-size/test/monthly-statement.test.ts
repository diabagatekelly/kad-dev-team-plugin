import { test } from "node:test";
import assert from "node:assert/strict";
import { produceMonthlyStatements } from "../reporting/monthly-statement.ts";
import { renderTable } from "../reporting/statement-table.ts";

test("writes one statement per member with activity and tells the desk", async () => {
  const written: string[] = [];
  const sent: string[] = [];
  const run = await produceMonthlyStatements(
    "2026-10",
    {
      loansInMonth: async () => [
        { memberCard: "LC-1", memberName: "Ada Byrne", memberEmail: "a@x", isbn: "1", title: "Lichens", dueOn: "2026-10-10", returnedOn: "2026-10-12" },
      ],
      finesInMonth: async () => [{ memberCard: "LC-1", cents: 150, assessedOn: "2026-10-12", reason: "late" }],
    },
    { write: async (name) => { written.push(name); } },
    { send: async (_to, subject) => { sent.push(subject); } },
  );
  assert.equal(run.members, 1);
  assert.deepEqual(written, ["2026-10-LC-1-ada-byrne.csv"]);
  assert.deepEqual(sent, ["Monthly statements 2026-10"]);
});

test("renders a table that fits the width", () => {
  const text = renderTable([{ cells: ["Lichens", "1.50"] }], { headers: ["title", "owed"], align: ["left", "right"], maxWidth: 20 });
  assert.ok(text.split("\n").every((l) => l.length <= 20));
});
