PASS

The finding explicitly names whole-object logging as its own distinct problem ("This is a distinct problem from 'a sensitive field got logged'... leaks every field either one has, including fields added later by someone who never considered this log line"), and the suggested fix points to identifier-based logging (invoiceId, userId) rather than the objects themselves.
