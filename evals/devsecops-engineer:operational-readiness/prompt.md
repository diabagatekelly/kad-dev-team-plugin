---
name: devsecops-engineer:operational-readiness
tags: [devsecops-engineer, operational-readiness]
runs: 3
---

Check whether this is ready to ship. It's a personal finance tracking app,
currently used only by its solo developer, hosted on a single small server
they redeploy manually by SSHing in and pulling the latest image.

The change about to ship:

- A database migration that renames the `transactions.category` text column
  to `transactions.category_id`, a foreign key into a new `categories`
  table.
- New application code that reads and writes `category_id` only — it no
  longer knows about the old `category` column at all.
- Both the migration and the new code are deployed together, in the same
  release.

Two more facts about the app as it exists today, not part of this change
but relevant to whether it's ready:

- If a required environment variable (the database connection string) is
  missing at startup, the app currently starts anyway and returns a 500 for
  every request, rather than failing to start.
- Nobody has ever run a rollback for any previous release of this app.

The developer asks: "Should I also set up an on-call rotation and a
post-mortem template before I ship this, just to be safe?"

## Scripted answers

- What happens if this is unavailable for an hour: "Nothing bad, I just
  fix it when I get to it. It's just me using it."
- Who would find out it's down, and how: "Me, next time I open it. Nobody
  else uses this."
- If asked whether to accept shipping the migration and the code together
  as a one-way change, or split it so the release can still be rolled
  back: "Let's split it — I'd rather not risk being stuck if something
  goes wrong, even though it's low stakes."
