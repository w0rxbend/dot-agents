# Agent Best Practices

- Separate measured graph facts from inference.
- Include confidence: high when graph nodes and relationships directly answer question, medium when evidence partial, low when fallback file inspection required.
- Never generate SDKs, refactors, or security claims from skill itself. Skill may plan workflows, but Ontoly stays source of truth.
