# Detailed Review Dimensions

Use the sections relevant to the diff. Repository policy and the actual task determine which checks are required; do not turn every heuristic into a gate for every edit.

## Review Process Overview

### Phase 1: Pre-Review Preparation

### Before starting review, gather context

1. **Understand the change**:

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
   - Is there a related issue/ticket? Review requirements
   - What domain is impacted?
   - What's the user-facing impact?

### Phase 2: Systematic Review

### Review across these dimensions

#### 1. Correctness

- **Does it solve the stated problem?**
- **Does business logic align with domain rules?**
- **Are edge cases handled appropriately?**
- **Do tests verify the expected behavior?**

### Check correctness by

- Reading tests first to understand intended behavior
- Tracing code paths through the change
- Verifying error scenarios are covered
- Cross-referencing with requirements

#### 2. Safety

- **Does it follow authorization/authentication patterns?**
- **Are there breaking changes to APIs or contracts?**
- **Could this expose sensitive data?**
- **Are data operations safe?**
- **Are there potential race conditions or data integrity issues?**

### Check safety by

- Verifying access control on operations
- Running compatibility checks for API changes
- Checking for proper input validation
- Reviewing transaction boundaries
- Validating input sanitization

#### 3. Maintainability

- **Does it follow existing codebase patterns?**
- **Is the code readable and understandable?**
- **Are complex areas documented?**
- **Does the changed code remain understandable without unrelated cleanup?**
- **Is naming clear and consistent?**

### Check maintainability by

- Comparing with similar code in codebase
- Verifying documentation on complex logic
- Checking for magic numbers and hard-coded values
- Ensuring consistent naming conventions
- Looking for commented-out code (anti-pattern)

#### 4. Testability

- **Are there tests for new functionality?**
- **Do tests cover edge cases and error scenarios?**
- **Are tests clear and maintainable?**
- **Is test data setup appropriate?**

### Check testability by

- Reviewing test coverage of changed code
- Verifying both happy and sad paths are tested
- Ensuring tests are deterministic and clear
- Checking for proper test isolation

#### 5. Performance

- **Are there obvious performance issues?**
- **Are database queries efficient?**
- **Are expensive operations properly optimized?**
- **Are resources properly managed?**

### Check performance by

- Identifying N+1 query patterns
- Checking for missing indexes on queries
- Reviewing resource allocation and cleanup
- Verifying appropriate data structures

#### 6. Standards Compliance

- **Does it follow language-specific best practices?**
- **Does it pass all verification checks?**
- **Are there linting or type errors?**
- **Does it follow agreed coding standards?**

### Check standards compliance by

- Running verification suite
- Checking for standard pattern violations
- Verifying no bypasses of quality gates

### Phase 3: Confidence Scoring

### Apply confidence scoring to all findings

Each identified issue must include a **confidence score (0-100)** indicating how certain you are that it's a genuine problem:

| Score | Confidence Level | When to Use |
|-------|------------------|-------------|
| 100   | Absolutely certain | Objective facts: linter errors, type errors, failing tests, security vulnerabilities |
| 90    | Very high confidence | Clear violations of documented standards, obvious correctness bugs |
| 80    | High confidence | Pattern violations, missing error handling, maintainability issues |
| 70    | Moderately confident | Potential issues that need context, possible edge cases |
| 60    | Somewhat confident | Questionable patterns, style concerns with codebase precedent |
| 50    | Uncertain | Potential improvements without clear precedent |
| <50   | Low confidence | Speculative concerns, personal preferences |

**CRITICAL FILTERING RULE**: Only report issues with **confidence >= 80%**. Lower-confidence findings create noise and should be omitted.

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

- Pre-existing issues not introduced by this change (check git blame)
- Issues already handled by linters/formatters
- Code with explicit lint-ignore comments (respect developer decisions)
- Style preferences without documented standards
- Theoretical bugs without evidence or reproduction
- "Could use" suggestions without clear benefit
- Pedantic nitpicks that don't affect quality

**VERIFY BEFORE REPORTING**:

- Run `git diff` to confirm issue is in changed lines
- Check if automated tools already catch this
- Verify against documented project standards (CLAUDE.md, CONTRIBUTING.md, etc.)
- Confirm the issue actually impacts correctness, safety, or maintainability

**Example of False Positive vs. Genuine Issue**:

False Positive: "This function could use TypeScript generics for better type safety" (confidence: 60%, style preference, no documented standard)

Genuine Issue: "Function `processPayment` at `services/payment.ts:42` performs database operation without transaction protection, risking data inconsistency if an error occurs mid-operation." (confidence: 90%, documented pattern violation, clear impact)

### Phase 4: Feedback & Decision

### Provide structured feedback

1. **Summary**: High-level assessment
2. **Strengths**: What's done well (positive reinforcement)
3. **Issues**: Organized by severity with **confidence scores**:
   - **Critical** (confidence >= 90): Blocks approval (security, correctness, breaking changes)
   - **Important** (confidence >= 80): Should be addressed (maintainability, best practices)
4. **Actionable next steps**: Specific changes with file:line references
5. **Decision**: Approve, Request Changes, or Needs Discussion

**Note**: Suggestions/nice-to-haves are intentionally omitted. Focus only on high-confidence, actionable feedback.

## Approval Criteria

### Approve When

- [ ] All verification checks pass (linting, tests, types, etc.)
- [ ] Business logic is correct and complete
- [ ] Security and authorization patterns followed
- [ ] No breaking changes (or properly coordinated)
- [ ] Code follows existing patterns
- [ ] Complex logic has clear documentation
- [ ] Tests cover happy paths, edge cases, and error scenarios
- [ ] Changes align with requirements
- [ ] Code is maintainable and clear
- [ ] Boy Scout Rule applied (code improved, not degraded)

### Request Changes When

- [ ] Critical issues: Security holes, correctness bugs, breaking changes
- [ ] Important issues: Pattern violations, missing tests, unclear code
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

### Reviewers often miss

1. **Authorization bypasses**: Operations without proper access control
2. **Breaking changes**: Not checking compatibility
3. **Error handling gaps**: Only reviewing happy paths
4. **Test quality**: Tests exist but don't actually test edge cases
5. **Domain logic errors**: Not understanding business rules
6. **Commented-out code**: Leaving dead code instead of removing
7. **Magic numbers**: Unexplained constants without names
8. **Over-clever code**: Complex when simple would work
9. **Scope regressions**: Introducing complexity or changing unrelated behavior

## Red Flags (Never Approve)

### These always require changes

- **Commented-out code** -> Remove it (git preserves history)
- **Secrets or credentials in code** -> Use secure configuration
- **Breaking changes** without compatibility verification
- **Tests commented out or skipped** -> Fix code, not tests
- **Verification failures ignored** -> Must all pass
- **Unverified behavioral changes** -> Request an appropriate safety net; a new test is useful when it exercises meaningful behavior
- **Incorrect business constants** -> Verify against the domain contract; configurability depends on actual requirements
- **Error handling missing** -> Must handle edge cases
- **Obvious security vulnerabilities** -> Must fix immediately

## Integration with Development Workflow

### Code review fits in Phase 2: Implementation

```text
Implementation -> Verification Suite -> Code Review -> Approval -> Merge
                 (automated checks)   (this skill)    (human)
```

### Review happens AFTER verification

1. Developer runs verification suite
2. Inspect relevant check results; distinguish known baseline failures from regressions
3. Code review skill applied for quality assessment
4. Issues identified and fixed
5. Re-verify after fixes
6. Human reviews and approves for merge

**Review is NOT a substitute for verification.** Both are required.
