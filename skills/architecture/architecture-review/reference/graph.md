# Software Graph Evidence

Software Graph evidence is primary source of truth. Prefer deterministic identifiers over prose names.

Evidence fields to capture:

- graph hash
- capability invoked
- node id and node type
- edge type and direction
- source span when present
- diagnostic codes when relevant
- confidence and its reason

Do not infer relationships absent from graph. Clearly labeled inference is allowed only after stating supporting graph evidence.
