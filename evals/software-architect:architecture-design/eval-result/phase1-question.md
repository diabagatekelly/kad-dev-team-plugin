Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/architecture-design/SKILL.md

Before I lay out this slice's structure, here's the first real decision:
should CSV export run synchronously within the request, or asynchronously
via a background job with a download-ready notification?

**My recommendation:** synchronous. **Why:** nothing in this slice's
acceptance criteria suggests large exports or concurrent load, and a
background job adds a job-status concept plus a notification mechanism
this slice doesn't need yet. **Alternative considered:** an asynchronous
job queue — the right call if export volume or size turns out to be large
enough that generating it in-request would be slow or unreliable, but
there's no evidence of that here.

This isn't a detail — it changes the actual structure (a job-status/
notification component vs. a single request-handling component), so I
want your call before I go further: which one do you want?
