# Detailed Review Dimensions

Use sections relevant to diff. Repository policy and actual task decide required checks. Do not turn every heuristic into gate for every edit.

## Review Process Overview

### Phase 1: Pre-Review Preparation

1. **Understand change**:

   ```bash
   # Review the diff
   git diff <base-branch>...HEAD

   # Check scope of changes
   git diff --stat <base-branch>...HEAD
   ```

2. **Identify relevant context**:

   ```bash
   # Find similar patterns in codebase
   grep -r "similar_pattern" .
   ```

3. **Verify business context**:
   - Related issue/ticket? Review requirements
   - What domain is impacted?
   - What's user-facing impact?

### Phase 2: Systematic Review

#### 1. Correctness

- **Solves stated problem?**
- **Business logic aligns with domain rules?**
- **Edge cases handled?**
- **Tests verify expected behavior?**

### Check correctness by

- Reading tests first for intended behavior
- Tracing code paths through change
- Verifying error scenarios covered
- Cross-referencing with requirements

#### 2. Safety

- **Follows authorization/authentication patterns?**
- **Breaks APIs or contracts?**
- **Could expose sensitive data?**
- **Data operations safe?**
- **Race conditions or data integrity risks?**

### Check safety by

- Verifying access control on operations
- Running compatibility checks for API changes
- Checking input validation
- Reviewing transaction boundaries
- Validating input sanitization

#### 3. Maintainability

- **Follows existing codebase patterns?**
- **Code readable?**
- **Complex areas documented?**
- **Changed code understandable without unrelated cleanup?**
- **Naming clear and consistent?**

### Check maintainability by

- Comparing with similar code in codebase
- Verifying documentation on complex logic
- Checking for magic numbers, hard-coded values
- Looking for commented-out code (anti-pattern)

#### 4. Testability

- **Tests for new functionality?**
- **Tests cover edge cases, error scenarios?**
- **Tests clear and maintainable?**
- **Test data setup appropriate?**

### Check testability by

- Reviewing test coverage of changed code
- Verifying both happy and sad paths tested
- Ensuring tests deterministic and clear
- Checking for proper test isolation

#### 5. Performance

- **Obvious performance problems?**
- **Database queries efficient?**
- **Expensive operations optimized?**
- **Resources managed properly?**

### Check performance by

- Identifying N+1 query patterns
- Checking for missing indexes on queries
- Reviewing resource allocation and cleanup
- Verifying appropriate data structures

#### 6. Standards Compliance

- **Follows language-specific best practices?**
- **Passes all verification checks?**
- **Linting or type errors?**
- **Follows agreed coding standards?**

### Check standards compliance by

- Running verification suite
- Checking standard pattern violations
- Verifying no bypasses of quality gates

### Phase 3: Confidence Scoring

Each issue must carry **confidence score (0-100)**: certainty it is genuine problem.

| Score | Confidence Level | When to Use |
|-------|------------------|-------------|
| 100   | Absolutely certain | Objective facts: linter errors, type errors, failing tests, security vulnerabilities |
| 90    | Very high confidence | Clear documented-standard violations, obvious correctness bugs |
| 80    | High confidence | Pattern violations, missing error handling, maintainability issues |
| 70    | Moderately confident | Potential issues needing context, possible edge cases |
| 60    | Somewhat confident | Questionable patterns, style concerns with codebase precedent |
| 50    | Uncertain | Potential improvements without clear precedent |
| <50   | Low confidence | Speculative concerns, personal preferences |

**CRITICAL FILTERING RULE**: Only report issues with **confidence >= 80%**.

### Confidence Scoring Guidelines

**High Confidence (90-100)** - Report these:

- Verification failures (linting, tests, types)
- Security vulnerabilities (SQL injection, XSS, auth bypass)
- Correctness bugs with clear reproduction
- Breaking API changes
- Violations of documented team standards

**Medium-High Confidence (80-89)** - Report these:

- Missing tests for new functionality
- Error handling gaps
- Performance issues (N+1 queries, missing indexes)
- Maintainability concerns with clear patterns
- Boy Scout Rule violations

**Medium Confidence (60-79)** - DO NOT REPORT:

- Style preferences without clear codebase precedent
- Speculative performance concerns
- Alternative approaches without clear benefit

**Low Confidence (<60)** - DO NOT REPORT:

- Personal opinions
- "Could be better" without specific impact
- Theoretical edge cases without evidence

### False Positive Filtering

**CRITICAL**: Apply these filters to avoid reporting non-issues:

**DO NOT REPORT**:

- Pre-existing issues not introduced by change (check git blame)
- Issues already handled by linters/formatters
- Code with explicit lint-ignore comments (respect developer decisions)
- Style preferences without documented standards
- Theoretical bugs without evidence or reproduction
- "Could use" suggestions without clear benefit
- Pedantic nitpicks that don't affect quality

**VERIFY BEFORE REPORTING**:

- Run `git diff` to confirm issue is in changed lines
- Check whether automated tools already catch it
- Verify against documented project standards (CLAUDE.md, CONTRIBUTING.md, etc.)
- Confirm issue actually impacts correctness, safety, or maintainability

**Example of False Positive vs. Genuine Issue**:

False Positive: "This function could use TypeScript generics for better type safety" (confidence: 60%, style preference, no documented standard)

Genuine Issue: "Function `processPayment` at `services/payment.ts:42` performs database operation without transaction protection, risking data inconsistency if an error occurs mid-operation." (confidence: 90%, documented pattern violation, clear impact)

### Phase 4: Feedback & Decision

1. **Summary**: High-level assessment
2. **Strengths**: What's done well (positive reinforcement)
3. **Issues**: Organized by severity with **confidence scores**:
   - **Critical** (confidence >= 90): Blocks approval (security, correctness, breaking changes)
   - **Major** (confidence >= 80): Address before merge (see severity scale in SKILL.md; Minor applies only to repository-required fixes)
4. **Actionable next steps**: Specific changes with file:line references
5. **Decision**: Approve, Request Changes, or Needs Discussion

**Note**: Suggestions/nice-to-haves intentionally omitted.

## Approval Criteria

### Approve When

- [ ] All verification checks pass (linting, tests, types, etc.)
- [ ] Business logic correct and complete
- [ ] Security and authorization patterns followed
- [ ] No breaking changes (or properly coordinated)
- [ ] Code follows existing patterns
- [ ] Complex logic clearly documented
- [ ] Tests cover happy paths, edge cases, error scenarios
- [ ] Changes align with requirements
- [ ] Code maintainable and clear
- [ ] Boy Scout Rule applied (code improved, not degraded)

### Request Changes When

- [ ] Critical issues: Security holes, correctness bugs, breaking changes
- [ ] Major issues: Pattern violations, missing tests, unclear code
- [ ] Verification failures not addressed
- [ ] Business logic doesn't match requirements
- [ ] Insufficient error handling

### Needs Discussion When

- [ ] Architectural concerns
- [ ] Unclear requirements
- [ ] Trade-off decisions needed
- [ ] Pattern deviation requires justification
- [ ] Performance implications uncertain

## Common Review Pitfalls

1. **Over-clever code**: Complex when simple would work
2. **Scope regressions**: Introducing complexity or changing unrelated behavior

## Red Flags (Never Approve)

- **Commented-out code**: Remove it (git preserves history)
- **Secrets or credentials in code**: Use secure configuration
- **Breaking changes** without compatibility verification
- **Tests commented out or skipped**: Fix code, not tests
- **Verification failures ignored**: All must pass
- **Unverified behavioral changes**: Request appropriate safety net. New test helps when it exercises meaningful behavior
- **Incorrect business constants**: Verify against domain contract. Configurability depends on actual requirements
- **Error handling missing**: Must handle edge cases
- **Obvious security vulnerabilities**: Must fix immediately

## Integration with Development Workflow

### Code review fits in Phase 2: Implementation

```text
Implementation -> Verification Suite -> Code Review -> Approval -> Merge
                 (automated checks)   (this skill)    (human)
```

### Review happens AFTER verification

1. Developer runs verification suite
2. Inspect relevant check results; distinguish known baseline failures from regressions
3. Apply code review skill for quality assessment
4. Issues identified and fixed
5. Re-verify after fixes
6. Human reviews and approves for merge

**Review is NOT a substitute for verification.** Both required.
