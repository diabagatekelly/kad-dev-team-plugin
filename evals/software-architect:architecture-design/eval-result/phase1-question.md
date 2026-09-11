Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/architecture-design/SKILL.md

Before working out structure, one real decision needs your call: **should export run synchronously in the request, or be handed off to a background job with a status/notification flow?**

**Recommendation: synchronous.** The acceptance criteria describe a single user downloading their own transaction history — there's no actor or scale mentioned that would make a request-time export slow enough to need offloading.

**Alternative considered and rejected: an asynchronous background job.** This would add a job queue, a status-tracking mechanism, and a way to notify the user when the file is ready — real infrastructure this slice doesn't need yet, for a volume of data (one person's own transactions) that a synchronous response handles without issue. This isn't ADR-worthy either way — it's cheap to swap for a background job later if volume changes, not a precedent the rest of the system would follow.

Which do you want — synchronous, or should I design for the background-job version instead?
