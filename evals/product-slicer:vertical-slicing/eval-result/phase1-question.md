Skills consulted: /Users/kellydiabagate/Documents/kad-developer-suite/skills/vertical-slicing/SKILL.md, /Users/kellydiabagate/Documents/kad-developer-suite/skills/acceptance-criteria/SKILL.md

## Scenario A

The requirements doc already confirmed WHAT — single user, live bank connection over CSV, one checking account, why. I'm not re-asking any of that. One thing it doesn't resolve: the requirements doc itself notes the user has more than one checking account, and "one checking account, connected live" doesn't say whether that means whichever account gets connected first, or a specific one the user picks — that changes the connection flow's shape, so I need to ask it directly: **does "their checking account" mean the first account they connect, or do they need to choose which specific one?**

## Scenario B

No requirements-refinement doc exists yet for any step of this problem. Deciding what capability or approach to build first isn't mine to make — that's `product-manager`'s call, made by asking the user directly, not something I infer from a scope map's step names. I can't cut a slice here yet, even with the request to skip straight to it: a `product-manager:requirements-refinement` pass needs to happen first, for whichever step is next in line. Handing this back rather than guessing at WHAT.
