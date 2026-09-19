PASS

Judge agent (final run): the `AttorneyDirectory` double is a plain object implementing the interface, passed straight into `AssignCase`'s constructor, exactly matching how the design says the dependency is consumed — no module-level mocking, no mock targeting the wrong layer.
