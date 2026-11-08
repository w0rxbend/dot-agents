---
name: bdd-principles
user-invocable: false
description: Run Behavior-Driven Development end to end, from discovery (Three Amigos, Example Mapping, outside-in) to Gherkin scenarios, edge cases, tags and step definitions. Use when acceptance criteria must be readable by business stakeholders or when a project already keeps `.feature` files; use test-driven-development for developer-level unit tests.
---

# Behavior-Driven Development

```
Discovery (conversation) -> Formulation (Gherkin) -> Automation (step definitions) -> Delivery
```

## When to Use

- Business rules stakeholders must read and approve.
- Project already uses Cucumber, SpecFlow/Reqnroll, behave, pytest-bdd, Godog or similar runner.
- Vague requirements need concrete examples before anyone builds.

**Do not use** for pure technical internals (parsers, caches, algorithms). Unit-test those with `test-driven-development`. Do not add Gherkin toolchain to project without one unless user asks.

## Phase 1: Discovery

### Three Amigos

Before writing scenarios, get three perspectives:

| Perspective | Questions |
|---|---|
| Business (PO/BA) | Which problem does it solve? Which rules? What value? |
| Development | Which constraints? Which edge cases come from implementation? |
| Testing | What could go wrong? What is missing? How do we know it works? |

Example, "password reset": tokens expire after 1 hour; new request invalidates older tokens; unknown emails get same success message (no account enumeration); requests rate-limited. Each answer becomes a scenario.

Agent working alone: play all three roles explicitly. Send open questions to user; do not invent business answers.

### Example Mapping

Short session producing four card types for one story:

| Card | Meaning |
|---|---|
| Story (yellow) | Feature being explored |
| Rule (blue) | Acceptance criterion |
| Example (green) | Concrete case illustrating a rule |
| Question (red) | Unresolved uncertainty |

Signals: many red cards: story not ready. Many blue cards: story too big, split it. Rule without examples: not yet understood.

### Ubiquitous language

Use domain words in scenarios ("Member places an order", not "user submits form; row inserted"). Keep short glossary for confusable terms (Member vs Guest, Cart vs Order). Reuse same terms in code.

## Phase 2: Formulation (Gherkin)

### Scenario quality

Good scenario: **specific** (one behavior), **declarative** (what, not how), **domain language**, **independent** (no reliance on other scenarios' state). Aim for 3-7 steps.

```gherkin
# Good: declarative, one behavior
Scenario: Gold member receives loyalty discount
  Given a customer with Gold membership
  And a cart total of $100
  When the customer checks out
  Then a 10% loyalty discount is applied
  And the final total is $90

# Bad: UI script coupled to implementation
Scenario: Apply discount
  Given I click the membership dropdown
  And I select "Gold" from the list
  When I click the checkout button
  Then the JavaScript calculates 10% off
```

### Feature structure: Background, Rule, Outline

```gherkin
@cart
Feature: Shopping cart
  As a customer
  I want to manage items in my cart
  So that I can buy what I chose

  Background:
    Given I am signed in as a customer

  Rule: Refunds are available within 30 days
    Scenario: Refund inside the return window
      Given an order placed 15 days ago
      When the customer requests a refund
      Then a full refund is processed

    Scenario: Refund after the return window
      Given an order placed 45 days ago
      When the customer requests a refund
      Then the refund is denied with "Return window expired"

  Scenario Outline: Password validation
    When I register with password "<password>"
    Then I see "<message>"

    Examples:
      | password   | message                 |
      | abc        | Password too short      |
      | abcdefgh   | Password needs a number |
      | abcdefgh1  | Password accepted       |
```

- `Background` only for setup shared by every scenario in file. Keep short.
- Group criteria with `Rule:` (Gherkin 6+). Check runner version first.
- `Scenario Outline`: same behavior, different data. Do not hide different behaviors in one table.

### Edge cases checklist

Start with happy path, then add scenarios for each that applies:

- Duplicate or conflicting data (existing email, double submit)
- Invalid format, empty required input
- Boundaries (limits, exactly-at-threshold, expiry times)
- Permissions and ownership (another user's resource)
- Repeated or concurrent actions (second reset request, retry)
- Security-neutral responses (same message for unknown accounts)

### Tags

```gherkin
@authentication @critical
Feature: Login
  @smoke
  Scenario: Basic login
  @wip
  Scenario: Two-factor authentication
```

Tags serve CI selection (smoke vs full suite), ownership, quarantining work in progress. Cucumber-style expression: `--tags "@smoke and not @wip"`. Check runner's own syntax.

## Phase 3: Automation (step definitions)

Bind steps in repository's existing framework. Cucumber (Ruby) example:

```ruby
Given('a registered user with email {string}') do |email|
  @user = User.create!(email: email, password: 'password123')
end

When('the user signs in with correct credentials') do
  visit login_path
  fill_in 'Email', with: @user.email
  fill_in 'Password', with: 'password123'
  click_button 'Log In'
end

Then('the user sees the dashboard') do
  expect(page).to have_current_path(dashboard_path)
end
```

Rules for steps:

- Step text stays business-level. UI or API mechanics go in step code, page objects or helpers.
- Reuse step definitions via parameters. Do not copy near-identical steps.
- Prefer driving system through API or service layer. Use UI only for UI scenarios.
- Each scenario creates and cleans up own state.

## Outside-In Development

1. Write failing acceptance scenario.
2. Drop to outermost layer: write failing unit test, make it pass (`test-driven-development`).
3. Move inward layer by layer, refactoring as you go.
4. Stop when scenario passes.

Not every scenario needs automation: automate high-value behaviors, cover details with unit tests.

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Scenarios written after code, by one person | Discovery first; review scenarios with stakeholders |
| Feature files left stale | Treat as code; update with behavior change |
| "BDD = Cucumber" | Conversation and examples matter; tool optional |

## Done When

- Every rule has at least one example. Open questions resolved or listed for user.
- Scenarios declarative, independent, covering happy path plus relevant edge cases.
- Step definitions reuse existing steps and run in repository's runner. New scenarios fail before change, pass after.
