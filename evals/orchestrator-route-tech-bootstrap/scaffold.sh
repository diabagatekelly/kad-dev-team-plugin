#!/usr/bin/env bash
set -euo pipefail
here="$(dirname "${BASH_SOURCE[0]}")"
mkdir -p docs/cancel-hold
cp -R "$here/../fixtures/library-app/route-plants/cancel-hold/." docs/cancel-hold/
# The shared plant's design was written for the library app, where HoldQueue,
# InMemoryHoldQueue and PlaceHold exist. This repo is empty apart from docs/,
# so a design that calls them "existing" contradicts the repo, and two runs in
# three stopped to ask which was true instead of routing. Make the design
# consistent with an empty repo: the port and adapter are new, and the
# constructor convention is the design's own.
sed -i -e 's/strategic, existing port): gains an operation that$/strategic, new port): one operation, which/' \
       -e 's/tactical, existing adapter):$/tactical, new adapter):/' \
       -e 's/^  implements the new operation\.$/  implements it in memory./' \
       -e 's/through its constructor, the way$/through its constructor, the convention/' \
       -e 's/^  PlaceHold does\.$/  every use case here will follow./' docs/cancel-hold/design-001.md
grep -q "existing" docs/cancel-hold/design-001.md && { echo "design-001.md still claims existing code" >&2; exit 1; }
exit 0
