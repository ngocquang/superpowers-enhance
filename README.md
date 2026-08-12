# superpowers-enhance

An override layer for Jesse Vincent's [superpowers](https://github.com/obra/superpowers) skills.

Superpowers skills are good defaults, but two of them leave room where a stricter
rule works better in practice. This plugin closes that room. It does not ask the
model to consider an improvement — a hook injects the override into context
immediately after the base skill is read, marked as mandatory.

## What it overrides

| Base skill invoked | Enhance skill injected |
|---|---|
| `superpowers:brainstorming` | `brainstorm-enhance` |
| `superpowers:executing-plans` | `executing-plans-enhance` |
| `superpowers:subagent-driven-development` | `executing-plans-enhance` |
| `superpowers:using-git-worktrees` | `executing-plans-enhance` |

### `brainstorm-enhance` — ask in rounds, not one at a time

`superpowers:brainstorming` requires one clarifying question per message. On a
design with a dozen open decisions that is a dozen round-trips.

This skill replaces **only** that phase. It models the design as a tree and asks
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

This skill removes the escape hatch: no isolated workspace, no execution. It also
specifies the setup that the base skill leaves open — a project-local
`./.worktrees/` root, a branch cut from the freshly-fetched integration branch,
and a dependency step where the lockfile decides between a real install and a
symlink (pnpm always installs; a symlinked `node_modules` writes *through* the
link into the root checkout).

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
override did not fire.

## How it works

`hooks/hooks.json` registers `hooks/skill-enhance.py` on two events. On
`PostToolUse` for the `Skill` tool it looks up the invoked skill name in its
mapping table and, on a match, injects the enhance skill's full text as
`additionalContext`. On `PostCompact` it re-arms that injection.

Two details matter:

**PostToolUse, not PreToolUse.** Injecting *after* the base skill puts the
override later in the context window, which is what makes "where this conflicts,
this one wins" hold.

**Full text, not a suggestion.** These are overrides, so the hook injects the
skill body rather than asking the model to invoke it. The YAML frontmatter is
stripped — it only tells the model whether to invoke the skill, and the hook has
already made that call.

The injection happens **once per context**, not once per invocation. Three of the
four base skills map to the same enhance skill, so without this a single plan run
would inject `executing-plans-enhance` several times. The claim is keyed by
`session_id` + `agent_id`, so a sub-agent still gets its own copy — sub-agents
share the parent's session but have their own context window, and the plan
fan-out is exactly the case this plugin exists for. State lives in a temp
directory and is pruned after 7 days.

**Compaction releases the claim.** The claim file outlives the context window it
guards, so once compaction evicts the injected text the hook would otherwise stay
silent and the base skill would quietly win the rest of the session. The
`PostCompact` hook deletes that session's claims, and the next invocation injects
again. `PostCompact` carries no `agent_id`, so every context of the session is
released together — a redundant re-injection costs a few thousand tokens, a
missing one costs the override.

## Troubleshooting

**The skill was injected the first time but not the second.** By design — see
above. It is already in the context window, and compaction re-arms it.

**No system message at all.** Check `python3 --version` resolves, and that the
invoked skill name matches the table. The hook matches on the segment after the
last `:`, so `superpowers:brainstorming` and a personal `brainstorming` skill
both trigger it.

**The hook cannot read a `SKILL.md`.** It writes the path and error to stderr and
stays silent rather than injecting a partial override.

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

To add another override: drop a `SKILL.md` under `skills/`, then add the base
skill name to `ENHANCE_FOR` in `hooks/skill-enhance.py`.

## License

Apache-2.0. See [LICENSE](LICENSE).
