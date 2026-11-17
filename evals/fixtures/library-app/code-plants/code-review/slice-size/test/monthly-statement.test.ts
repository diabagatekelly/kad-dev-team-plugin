import { test } from "node:test";
import assert from "node:assert/strict";
import { produceMonthlyStatements } from "../reporting/monthly-statement";
import { describeEntry } from "../reporting/statement-table";

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

test("describes each kind of entry in one printed line", () => {
  assert.equal(describeEntry({ kind: "fine", reason: "late", cents: 150, assessedOn: "2026-10-12" }), "Fine of $1.50 assessed on 2026-10-12: late.");
  assert.equal(describeEntry({ kind: "return", title: "Lichens", returnedOn: "2026-10-12", daysLate: 1 }), 'Returned "Lichens" on 2026-10-12, 1 day late.');
  assert.equal(describeEntry({ kind: "payment", cents: 150, paidOn: "2026-10-13", method: "cash" }), "Paid $1.50 in cash at the desk on 2026-10-13.");
});
