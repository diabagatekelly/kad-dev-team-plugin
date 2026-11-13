- R3: Given the hold queue fails after removing a hold and before
  answering, when the same cancel is asked for again within 30 seconds,
  then the result says cancelled, once, the hold stays removed, and the
  removal is recorded exactly 1 time (issue #14).
