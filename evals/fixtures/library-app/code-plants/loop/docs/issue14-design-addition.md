- R3 (`reliability-slice-001.md`, issue #14): CancelHold records the
  removal before the hold queue answers, so a queue that fails after
  removing a hold and before answering leaves a record; the same cancel
  asked for again within 30 seconds reads that record and says cancelled,
  once. The record lives with HoldQueue's removal operation. Approved
  2026-11-12 (decision 3).
