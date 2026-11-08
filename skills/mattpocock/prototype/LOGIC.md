# Logic Prototype

One self-contained HTML file (a **shareable demo**) where anyone drives a state model by clicking buttons. Use for questions about **business logic, state transitions, or data shape**: things that look reasonable on paper but feel wrong once pushed through real cases.

Nothing to install, so a non-developer (designer, PM, domain expert) can feel the model themselves.

## When this is the right shape

- "I'm not sure if this state machine handles the edge case where X then Y."
- "Does this data model actually let me represent the case where..."
- "I want to feel out what the API should look like before writing it."
- Anything where someone wants to **press buttons and watch state change**.

Question is "what should this look like"? Wrong branch; use [UI.md](UI.md).

## Process

### 1. State the question

Before coding, write state model and question in one paragraph at top of demo (visible intro, not just a comment).

### 2. Isolate the logic in a portable module

Put logic answering the question in one `<script>` block: small pure module, liftable into real codebase later. Page around it is throwaway; module isn't.

Pick shape by question:

- **A pure reducer**: `(state, action) => state`. For discrete-event actions and single-value state.
- **A state machine**: explicit states and transitions. For when "which actions are even legal right now" is part of question.
- **A small set of pure functions** over plain data type. For when there's no implicit current state, only transformations.
- **A class or module with a clear method surface** when logic genuinely owns ongoing internal state.

Fit shape to question, *not* to ease of wiring to a page. Keep it pure: no DOM, no `document`, no button handlers reaching inside. Page calls into module; nothing flows back.

### 3. Build the shareable HTML file

One file, plain HTML/CSS/JS, everything inline: no framework, no bundler, no server. Opens by double-click, survives being emailed around.

Write for non-developer. Every label in **domain language**: buttons and state read like the business, not the reducer. Explain in plain words what's happening.

Layout, top to bottom:

1. **Title and one-line explanation** of what demo explores (question from step 1).
2. **Current state**: full relevant state as readable panel (labelled fields, not raw JSON dump), re-rendered after every click. Where it helps non-developer follow, highlight what just changed.
3. **Free-play buttons**: one per action, always available, usable in any order. Each click dispatches its action and re-renders state.
4. **Guided walkthroughs**: set of **scenarios**, one per tab. Tab holds short plain-language description (situation set up, what to watch for), then ordered **buttons to press**. Each step is a real button: click performs action, advances to next step. Starting a walkthrough resets to known initial state, so scenario runs same way every time.

Pick scenarios showing awkward cases, hard to reason about on paper: happy path, tricky edge case, attempt at something that should be illegal.

Beautiful but restrained: clean typography, generous spacing, one accent colour. No animations, no gimmicks: nothing competing with state and buttons.

### 4. Hand it over

Send file or open it for them. They click through walkthroughs and free-play when they get to it. Watch for "wait, that shouldn't be possible" or "huh, I assumed X would be different": those are bugs in the _idea_. Add new actions or scenarios on request.

### 5. Capture the answer and the prototype

Once question is answered, capture answer, then capture prototype per [SKILL](SKILL.md). Logic mapping: validated reducer / machine / function set lifts into real module (decision absorbed). HTML shell goes to throwaway branch as primary source.

## Anti-patterns

- **Don't generalise.** No "what if we wanted to support X later." One question only.
