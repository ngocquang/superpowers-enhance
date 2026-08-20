# superpowers-enhance

A supplement layer for Jesse Vincent's [superpowers](https://github.com/obra/superpowers) skills.

Superpowers skills are good defaults, but two of them leave room where a stricter
rule works better in practice. This plugin fills that room. It changes nothing in
the superpowers skills themselves and never asks you to skip a step of one — a
hook injects the supplement into context immediately after the base skill is read,
marked as required for the steps it names.

## What it adds

| Base skill invoked | Enhance skill injected |
|---|---|
| `superpowers:brainstorming` | `brainstorm-enhance` |
| `superpowers:executing-plans` | `executing-plans-enhance` |
| `superpowers:subagent-driven-development` | `executing-plans-enhance` |
| `superpowers:using-git-worktrees` | `executing-plans-enhance` |

### `brainstorm-enhance` — ask in rounds, not one at a time

`superpowers:brainstorming` requires one clarifying question per message. On a
design with a dozen open decisions that is a dozen round-trips.

This skill supplies **only** that step. It models the design as a tree and asks
every question on the *frontier* — the decisions whose prerequisites are already
settled — in a single round via `AskUserQuestion`, with a recommended answer as
the first option. Questions downstream of an open decision wait for the next
round. Facts the agent could look up itself are never asked; they are dispatched
to a sub-agent.

Everything else in `superpowers:brainstorming` is untouched, including the hard
gate that blocks any code before an approved design.

### `executing-plans-enhance` — worktree isolation, no fallback

`superpowers:using-git-worktrees` allows an agent to degrade to the current
checkout when worktree setup fails. In a sandbox that clause fires often, and
plan execution quietly lands in the root checkout.

This skill declines that allowance: no isolated workspace, no execution. Consent
still belongs to the user — a worktree they *decline* is a decision the skill
follows; a worktree that *fails* is not.

It also fills in what the base skill leaves open:

- **Setup** — a fixed `./worktrees/` root (git-ignored, inside the repo
  so the sandbox can write to it), a branch cut from the freshly-fetched
  integration branch, *entered* through the harness's own tool (`EnterWorktree`
  with `path:`) rather than a bare `cd`, a real dependency install in the
  worktree, and a baseline verification run before the first task.
- **Staying isolated** — a worktree has its own `HEAD`, not its own repository.
  Branches, tags, the object store and `refs/stash` all live in the shared
  `.git`, so `cd`-ing into a worktree is not enough. The skill names the four
  command classes that reach back out (escape hatches like `git -C` and absolute
  paths into root, shared-ref writes, history pruning, sibling-worktree removal)
  and requires every subagent dispatch to carry the absolute worktree path and
  verify `git rev-parse --show-toplevel` before its first write.
- **Never symlinking `node_modules`** to the root checkout's — installs write
  *through* the link and mutate the root's tree.
- **Getting back out** — from Claude Code 2.1.237 the harness enforces the
  isolation itself: an entered worktree has every git command aimed at the root
  checkout refused at the tool layer, reads included, and disabling the sandbox
  does not lift it. That also blocks the merge that
  `superpowers:finishing-a-development-branch` runs from root. The skill supplies
  the sanctioned route — `ExitWorktree` with `action: "keep"`, then a
  fast-forward-only merge and cleanup from root — plus the values that skill's
  Step 2 can no longer probe for itself, and a clean handoff for the case where
  the session cannot leave at all.

## Requirements

- Claude Code with the `superpowers` plugin installed
- `python3` on `PATH` — the hook is a Python script

## Install

```
/plugin marketplace add ngocquang/superpowers-enhance
/plugin install superpowers-enhance@ngocquang-superpowers
```

If you do not have superpowers yet, install it first — see
[obra/superpowers](https://github.com/obra/superpowers). It is also carried by
the official marketplace as `superpowers@claude-plugins-official`.

## Verifying it works

Invoke a base skill and watch for the system message:

```
superpowers-enhance: executing-plans-enhance applied over superpowers:executing-plans
```

That line is emitted by the hook at the moment of injection. No line means the
supplement did not fire.

## How it works

`hooks/hooks.json` registers `hooks/skill-enhance.py` on two events. On
`PostToolUse` for the `Skill` tool it looks up the invoked skill name in its
mapping table and, on a match, injects the enhance skill's full text as
`additionalContext`. On `PostCompact` it re-arms that injection.

Two details matter:

**PostToolUse, not PreToolUse.** A supplement should be read *after* the thing it
supplements: the enhance skills scope themselves by reference ("for step 3", "for
the setup steps"), and that scoping only resolves against base-skill text the
model has already read.

**The hook is the only delivery path.** Both enhance skills carry
`disable-model-invocation: true`, so the model never invokes them on its own —
the hook injects the skill body instead. You can still run `/brainstorm-enhance`
or `/executing-plans-enhance` by hand to re-read one. The YAML frontmatter is
stripped before injection: it only governs invocation, which the hook has already
settled.

The injection happens **once per context**, not once per invocation. Three of the
four base skills map to the same enhance skill, so without this a single plan run
would inject `executing-plans-enhance` several times. The claim is keyed by
`session_id` + `agent_id`, so a sub-agent still gets its own copy — sub-agents
share the parent's session but have their own context window, and the plan
fan-out is exactly the case this plugin exists for. State lives in a temp
directory and is pruned after 7 days.

**Compaction releases the claim.** The claim file outlives the context window it
guards, so once compaction evicts the injected text the hook would otherwise stay
silent and the rest of the session would run on the base skill alone. The
`PostCompact` hook deletes that session's claims, and the next invocation injects
again. `PostCompact` carries no `agent_id`, so every context of the session is
released together — a redundant re-injection costs a few thousand tokens, a
missing one costs the supplement.

## Troubleshooting

**The skill was injected the first time but not the second.** By design — see
above. It is already in the context window, and compaction re-arms it.

**No system message at all.** Check `python3 --version` resolves, and that the
invoked skill name matches the table. The hook matches on the segment after the
last `:`, so `superpowers:brainstorming` and a personal `brainstorming` skill
both trigger it.

**The hook cannot read a `SKILL.md`.** It writes the path and error to stderr and
stays silent rather than injecting a partial supplement.

## Layout

```
.claude-plugin/
  plugin.json           plugin manifest
  marketplace.json      lets this repo be added as a marketplace directly
hooks/
  hooks.json            PostToolUse(Skill) + PostCompact registration
  skill-enhance.py      mapping table, injection, compaction release
skills/
  brainstorm-enhance/SKILL.md
  executing-plans-enhance/SKILL.md
```

To add another enhance skill: drop a `SKILL.md` under `skills/` with
`disable-model-invocation: true`, then add the base skill name to `ENHANCE_FOR`
in `hooks/skill-enhance.py`.

## License

Apache-2.0. See [LICENSE](LICENSE).
