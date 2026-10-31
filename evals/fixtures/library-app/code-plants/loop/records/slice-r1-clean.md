# @NAME@ review: slice 001, fix round 1

Range `@HEAD@..@FIX@` (the fix's diff only); file lending/cancel-hold-notice.ts, test/cancel-hold-notice.test.ts.

## Findings

No findings. The heading and body are escaped before interpolation, and `a reason with markup in it is shown as text, not rendered` pins it.

Counts: C0 H0 M0 L0.
