---
name: agent-crew
description: Guided, interview-style setup for multi-agent collaboration in GitHub Copilot CLI. Asks the user how they want to work and how to divide labor (orchestrator + workers like architect/coder/reviewer), then generates the wired-up .github/agents/*.agent.md files with correct `tools` so agents really delegate to each other (producing "Calling Agent" boxes). Use when the user wants to set up a team of custom agents, multi-agent workflow, agent orchestration, architect/coder/reviewer split, or asks to "build agents that call each other". Triggers - "multi-agent", "agent team", "agent crew", "agents that delegate", "architect coder reviewer", "orchestrate agents", "build custom agents".
allowed-tools: ask_user, view, create, edit, powershell, glob, grep, Read, Write, Edit, Bash
---

# agent-crew

Stand up a team ("crew") of GitHub Copilot CLI **custom agents** that genuinely delegate work
to each other. Runs a short guided interview, then writes one `*.agent.md` per role into
`.github/agents/`, correctly wired so an orchestrator agent calls workers via the `agent` tool
(the call that renders the **"Calling Agent: …"** execution box).

This skill is for **Copilot CLI / Desktop custom agents** (`.github/agents/*.agent.md`).
It is **not** for Copilot Studio (`agent.mcs.yml`) — if the user is in a Copilot Studio project,
stop and hand off to the Copilot Studio sub-agents instead.

---

## The one thing that makes delegation work (read first)

A custom agent can only call another custom agent if it has the **`agent`** tool
(official aliases: `Task`, `custom-agent`). That tool is what produces the
"Calling Agent: <name>" box, with the payload sent and the value returned.

Authoritative `tools` aliases (case-insensitive) for `.agent.md` frontmatter:

| Alias     | Grants                                              |
| --------- | --------------------------------------------------- |
| `agent`   | Invoke another custom agent (delegation). Aliases: `Task`, `custom-agent` |
| `read`    | Read files (`view`)                                 |
| `edit`    | Create/modify files (`Write`/`Edit`)                |
| `search`  | `grep`/`glob`                                       |
| `execute` | Run shell commands (`bash`/`powershell`). Aliases: `shell` |
| `web`     | `WebSearch`/`WebFetch`                              |
| `todo`    | Structured task lists                               |

Rules of thumb the skill MUST enforce when generating files:
- The **orchestrator** needs `agent` (to delegate) + usually `read`, `search`, `todo`.
  Withhold `edit` from a pure orchestrator so it is forced to delegate implementation.
- **Implementer** roles (coder) get `read`, `edit`, `search`, `execute`; usually **not** `agent`.
- **Reviewer / auditor** roles get `read`, `search`, `execute` and **not** `edit`
  (separation of duties: review-only).
- If `tools` is omitted entirely, the agent defaults to ALL tools — works, but explicit is safer
  and demonstrates the division of labor. Always set `tools` explicitly.
- Unrecognized tool names are ignored, so it is safe to list product-specific tools.

`.agent.md` frontmatter supported keys: `name`, `description` (required), `tools`, `model`,
`target`, `disable-model-invocation`, `user-invocable`. Body (the system prompt) max 30,000 chars.

---

## Workflow

### Step 0 — Disambiguate (only if unclear)
If a `agent.mcs.yml` exists anywhere in the workspace, this is Copilot Studio — do not use this
skill; hand off. Otherwise proceed.

### Step 1 — Guided interview
Ask the questions below **one at a time** using the `ask_user` tool (prefer multiple-choice).
Do not ask everything in one message. Adapt/skip questions already answered in the prompt.
In autopilot or when the user is unavailable, pick the recommended default and state the assumption.

1. **Goal / domain** — "這支 agent 團隊主要要協助什麼工作？" (free-form: e.g. web app dev,
   data pipeline, docs). Drives wording in each agent's prompt.
2. **Crew preset** — "要用哪種分工？"
   - `architect + coder + reviewer`（推薦，經典三角：規劃→實作→審核）
   - `planner + implementer`（兩人精簡）
   - `自訂角色`（讓使用者列出角色名稱）
3. **Per role — responsibilities** — for each role, "「<role>」負責什麼？有什麼必須遵守的規則？"
   (free-form; keep short). Skip if preset roles are obvious and user accepts defaults.
4. **Per role — capabilities** — "「<role>」需要哪些能力？" multi-select mapped to tool aliases:
   讀檔(read) / 改檔(edit) / 搜尋(search) / 執行指令(execute) / 委派其他 agent(agent) /
   上網(web) / 待辦清單(todo). Offer a sensible default per role (see presets) and let them adjust.
5. **Per role — model (optional)** — "「<role>」要指定模型嗎？" Offer common options the
   environment supports (e.g. a strong model for reviewer/architect) or "用預設".
   IMPORTANT: only write a `model:` value the environment actually supports. If the user names an
   unsupported id (e.g. `gpt-4o`, `anthropic.claude-3-opus-...`), warn and map to a valid one or omit.
6. **Delegation topology** — "誰可以呼叫誰？" Default: orchestrator → each worker, and the
   review loop returns through the orchestrator. Confirm or let them draw a different graph.
   Ensure every role that needs to call another has the `agent` tool.
7. **Workflow loop** — "完成後的流程是什麼？" Default for the classic preset:
   orchestrator plans → calls coder → calls reviewer → if issues, back to coder → re-review → done.
8. **Location** — "要建立在哪裡？" `.github/agents/`（專案層級，隨 repo 共享，推薦） or the user
   agents dir（個人跨專案）。Default `.github/agents/`.

After gathering answers, **echo a one-screen summary** of the crew (roles, tools, models, who calls
whom, the loop) so the user can sanity-check before files are written. In autopilot, skip waiting and
proceed.

### Step 2 — Generate the files
Create the target directory if needed, then write one `<role>.agent.md` per role using the
template in `templates/agent.template.md` as a guide. For each file:
- Frontmatter: `name`, `description`, `tools: [<resolved aliases>]`, and `model:` only if specified/valid.
- Body: a clear system prompt that states the role, its rules, and — for any role with the `agent`
  tool — **explicit instructions to use the `agent` tool to call the named downstream agents**, plus
  what to put in each delegation payload (task goal, relevant files, constraints, acceptance criteria).
- Enforce separation of duties: orchestrator has no `edit`; reviewer has no `edit`.
- Use the user's language for the prompt body (e.g. Traditional Chinese if they wrote in zh-TW).

Use the `create` tool (never overwrite blindly — if a file exists, show it and ask before replacing).

### Step 3 — Verify & hand off
- Re-read each generated file and confirm: required `description`, valid `tools`, valid/blank `model`,
  orchestrator has `agent`.
- Tell the user how to run it: type `@<orchestrator> <your request>`; the orchestrator will then use
  the `agent` tool to call workers, each producing a "Calling Agent: …" box you can expand to see the
  payload and return value.
- Optionally offer to commit the new files.

---

## Defaults for the classic preset (architect + coder + reviewer [+ tester])

| Role      | tools                              | edit? | agent? | typical model note |
| --------- | ---------------------------------- | ----- | ------ | ------------------ |
| architect | `agent, read, search, todo`        | ❌    | ✅     | default/strong     |
| coder     | `read, edit, search, execute`      | ✅    | ❌     | strong coding model|
| reviewer  | `read, search, execute`            | ❌    | ❌     | careful/critical model |
| tester    | `read, search, execute`            | ❌    | ❌     | strong reasoning model |

The orchestrator (architect) plans, then calls coder, then reviewer (static code review). For
runnable products (web apps/games), also add a **tester** that drives a **real browser via
Playwright** to actually run/play the product and report playability, difficulty and smoothness —
catching "code looks fine but it doesn't actually run / isn't fun" issues that static review and
node-only logic tests miss. The architect consolidates reviewer + tester feedback and loops
coder↔reviewer↔tester through itself until both pass, then summarizes back to the user.

> Lesson baked in: a reviewer reading code (or node smoke tests) can pass a build that is broken or
> unplayable in a real browser (e.g. `file://` + ES modules blocked by CORS, bad difficulty curve).
> Whenever the deliverable is something a user runs, include a tester that exercises it for real.

## Gotchas
- No "Calling Agent" box appears unless a real `agent`/`Task` tool call is made. Role-playing in text
  is not delegation — the orchestrator must actually invoke the worker agent.
- Workers return their result to whoever called them; nested workers need their own `agent` tool only
  if they themselves delegate.
- Keep each agent body focused; the orchestrator should pass full context in the delegation payload
  (workers are stateless across calls).
