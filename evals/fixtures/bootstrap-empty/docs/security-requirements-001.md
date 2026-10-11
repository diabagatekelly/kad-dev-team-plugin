# Security criteria for slice 1 (abridged)
- No bank username or password is ever received or stored — the vendor's
  flow means they never enter the system.
- The vendor access token never appears in logs, error responses, or any
  stack trace, and is not written to any persistent store in this slice.
