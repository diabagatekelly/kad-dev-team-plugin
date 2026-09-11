PASS

The output provides five concrete, testable Given/When/Then criteria that cover all three required areas (credentials not logged/leaked including on failure paths, failure messages not exposing provider internals/raw responses/headers, and transport encryption with rejection of non-encrypted endpoints), plus reasonable extras (no residual credential state after failed retry, fabricated test data) — none of it vague or checklist-style.
