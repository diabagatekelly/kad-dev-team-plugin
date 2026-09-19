PASS

Judge agent (final run): `'applies zero discount when lookup fails'` is flagged for the exact defect — `mockDiscountFor` never wired via `vi.spyOn`, real `StubDiscountLookup` default is what actually runs.
