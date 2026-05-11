# Human decision prompt

Before asking for final approval, present required decisions one by one.

## Visibility rule (Chat / CUI / AskQuestion)

Some clients (terminal-heavy layouts, older UI, or certain integrations) **do not render** multiple-choice widgets or may show only the instruction line **「上の選択肢から回答してください」** with **no visible options**. That fails human gates.

**Mandatory:**

1. **Every decision must be self-contained in plain assistant message text**: start with a **short title line** so the human knows *what* is being decided (e.g. `Decision 1 — Output format:`), then the question.
2. **Every discrete choice must appear as a numbered or lettered list in the same message** (e.g. `1. …` `2. …` or `A. …` `B. …`), including **tradeoffs or consequences** per option when relevant.
3. **Forbidden:** phrases like “answer from the options above”, “as listed earlier”, or “choose one of the choices shown” **unless** the **full list of choices is repeated immediately above that sentence in the same message**.
4. If you use a multiple-choice UI tool (e.g. AskQuestion), **duplicate the exact same options as text in the assistant message body** in the **same turn**. Never rely on the widget alone.

---

## Decision 1: [title]

Use a **visible title** (what is being decided), then fill:

- Question:
- Recommended answer:
- Options / consequences (each option on its own numbered line in chat, not only here):
- Blocks next stage: yes / no
- Artifact to update:

**Example chat shape (copy this pattern into the real reply):**

```text
Decision 1 — [short title of what we are deciding]

Question: [one sentence]

Options:
1. [Option A — consequence]
2. [Option B — consequence]
3. [Option C — consequence] (if needed)

Recommendation: [which option and why — or “none”]

Reply with the option number (or your own short answer).
```

Human response:

> 

---

After all required decisions are answered or explicitly accepted as open/non-blocking:

Final approval question:

> May dev-process proceed to the next stage?

**Include** what “next stage” means in one line (e.g. proceed to **plan** / **merge** / **complete task**). A short `OK` is valid here.
