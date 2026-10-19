---
name: bdd-principles
user-invocable: false
description: Run Behavior-Driven Development end to end, from discovery (Three Amigos, Example Mapping, outside-in) to Gherkin scenarios, edge cases, tags and step definitions. Use when acceptance criteria must be readable by business stakeholders or when a project already keeps `.feature` files; use test-driven-development for developer-level unit tests.
---

# Behavior-Driven Development

BDD is a collaboration practice first and a test format second. Concrete examples, agreed by business, development and testing, become executable scenarios that double as living documentation.

```
Discovery (conversation) -> Formulation (Gherkin) -> Automation (step definitions) -> Delivery
```

## When to Use

- A feature has business rules that stakeholders need to read and approve.
- The repository already uses Cucumber, SpecFlow/Reqnroll, behave, pytest-bdd, Godog or a similar runner.
- Requirements are vague and need concrete examples before anyone builds anything.

**Do not use** for pure technical internals (parsers, caches, algorithms). Write unit tests for those with `test-driven-development`. Do not add a Gherkin toolchain to a project that does not have one unless the user asks for it.

## Phase 1: Discovery

### Three Amigos

Before writing scenarios, get three perspectives on the story:

| Perspective | Questions |
|---|---|
| Business (PO/BA) | What problem does this solve? What are the rules? What value does it deliver? |
| Development | What are the constraints? Which edge cases come from the implementation? |
| Testing | What could go wrong? What is missing? How will we know it works? |

Example outcome for "password reset": tokens expire after 1 hour; a new request invalidates older tokens; unknown emails get the same success message (no account enumeration); requests are rate-limited. Each of these answers becomes a scenario.

When working with an agent alone, play the three roles explicitly and send the open questions to the user instead of inventing the business answers.

### Example Mapping

A short session that produces four kinds of cards for one story:

| Card | Meaning |
|---|---|
| Story (yellow) | The feature being explored |
| Rule (blue) | An acceptance criterion |
| Example (green) | A concrete case that illustrates a rule |
| Question (red) | An unresolved uncertainty |

Signals: many red cards mean the story is not ready. Many blue cards mean the story is too big and should be split. A rule with no examples is not understood yet.

### Ubiquitous language

Use the domain's words in scenarios ("Member places an order", not "user submits form; row inserted"). Keep a short glossary when terms could be confused (Member vs Guest, Cart vs Order) and reuse the same terms in code.

## Phase 2: Formulation (Gherkin)

### Scenario quality

A good scenario is **specific** (one behavior), **declarative** (what, not how), in **domain language**, and **independent** (no reliance on other scenarios' state). Aim for 3-7 steps.

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

- Use `Background` only for setup shared by every scenario in the file, and keep it short.
- Group criteria with `Rule:` (Gherkin 6+). Check the runner version before using it.
- Use `Scenario Outline` for the same behavior with different data. Do not use it to hide different behaviors in one table.

### Edge cases checklist

Start with the happy path, then add scenarios for each of these that applies:

- Duplicate or conflicting data (existing email, double submit)
- Invalid format and empty required input
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

Use tags for selection in CI (smoke vs full suite), ownership, and quarantining work in progress. With Cucumber-style tag expressions: `--tags "@smoke and not @wip"`. Check the runner's own syntax.

## Phase 3: Automation (step definitions)

Bind steps in the framework the repository already uses. Cucumber (Ruby) example:

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

- Keep step text business-level and put UI or API mechanics inside the step code (or in page objects or helpers).
- Reuse step definitions through parameters. Do not copy near-identical steps.
- Prefer driving the system through its API or service layer. Use the UI only for scenarios that are about the UI.
- Each scenario creates and cleans up its own state.

## Outside-In Development

1. Write a failing scenario (acceptance level).
2. Drop to the outermost layer, write a failing unit test, and make it pass (`test-driven-development`).
3. Move inward layer by layer, refactoring as you go.
4. Stop when the scenario passes.

BDD answers "what should we build?" from the outside in. TDD answers "how do we build it?" from the inside out. They complement each other. Not every scenario needs automation: automate high-value behaviors and cover the details with unit tests.

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| Scenarios written after the code, by one person | Run discovery first, and review scenarios with stakeholders |
| UI-scripted steps ("click", "select") | Describe intent, and move mechanics into step code |
| Several behaviors in one scenario | Split per behavior/rule |
| Huge outlines mixing behaviors | One outline per behavior |
| Scenarios depending on each other | Independent setup per scenario |
| Feature files left stale | Treat them as code: update them with the behavior change |
| "BDD = Cucumber" | Conversation and examples are the point; the tool is optional |

## Done When

- Every rule has at least one example, and open questions are resolved or listed for the user.
- Scenarios are declarative, independent, and cover the happy path plus the relevant edge cases.
- Step definitions reuse existing steps and run in the repository's runner, and the new scenarios fail before the change and pass after it.
