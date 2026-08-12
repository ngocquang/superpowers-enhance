---
name: executing-plans-enhance
description: Use when about to execute a written implementation plan, or when superpowers:executing-plans, superpowers:subagent-driven-development, or superpowers:using-git-worktrees is invoked — including when a sandbox denial, permission error, or "this change is small" reasoning tempts working in the current checkout.
---

# Executing Plans — Enhance

## Overview

Plan execution happens on its own branch, in its own worktree. Always. This skill
overrides the escape hatches in superpowers:using-git-worktrees that let an agent
degrade to working in the current checkout.

**Core principle:** No isolated workspace, no execution. When isolation fails,
escalate to your human partner — never continue in place.

**Announce at start:** "I'm using executing-plans-enhance to enforce branch + worktree isolation."

## The Iron Rule

**Never execute plan tasks in the root checkout.** The root checkout stays on the
integration branch (`develop` / `main` / `master`) at all times.

**No exceptions:**
- Not for a one-file change
- Not because the plan is short
- Not because `git worktree add` returned an error
- Not because the sandbox refused a write

**The one real exception is your human partner.** superpowers:using-git-worktrees
Step 0 asks for consent before creating a worktree; that ask still happens, and
their answer outranks this skill. If they decline, say plainly that plan tasks
will then run in the root checkout and what that costs, and follow their call. A
declined worktree is a decision. A failed one is not.

If you already created files in the root checkout, stash them, create the
worktree, and re-apply there. Do not "just finish this one thing first".

## Worktree Setup Recipe

**Do you have a native worktree tool?** Something named like `EnterWorktree`,
`WorktreeCreate`, a `/worktree` command, or a `--worktree` flag. If so, use it and
continue at step 3 — `git worktree add` alongside a native tool creates phantom
state the harness cannot see or clean up. Steps 1–2 below are the fallback for
when there is none; steps 3–4 apply either way.

Otherwise, setup is these four steps, in this order.

### 1. Resolve a project-local worktree root

```bash
git rev-parse --git-dir; git rev-parse --git-common-dir   # differ → already in a worktree, skip to step 3
cd "$(git rev-parse --show-toplevel)"
```

**`./.worktrees/` is the recommended root** — use it unless the project already
committed to another one. The other candidates exist only so an established
layout is not duplicated. Resolve the choice into `$DIR`; the candidate list is a
lookup, not a path to retype later.

```bash
DIR=$(for d in .worktrees .claude/worktrees worktrees; do [ -d "$d" ] && echo "$d" && break; done)
DIR=${DIR:-.worktrees}
mkdir -p "$DIR"
```

Then confirm git ignores it. `git check-ignore` is the check — a rule already
covering the directory (a blanket `.claude/` entry, say) means there is nothing
to add.

```bash
git check-ignore -q "$DIR" || {
  printf '\n%s/\n' "$DIR" >> .gitignore
  git add .gitignore && git commit -m "chore: ignore worktrees"
}
```

The leading newline matters: `.gitignore` files often lack a trailing one, and a
bare `echo` would splice the entry onto the last existing rule.

**The directory MUST live inside the repository root.** Not `$TMPDIR`, not
`~/worktrees`. The repo root is what the sandbox grants write access to, and it is
what the optional `node_modules` link in step 3 has to reach.

### 2. Branch off the freshly-fetched integration branch

```bash
git fetch origin
git worktree add "$DIR/$BRANCH" -b "$BRANCH" origin/<integration-branch>
cd "$DIR/$BRANCH"
```

### 3. Wire dependencies — pnpm installs, the rest may symlink

Identify the package manager from the lockfile at the repository root — the
lockfile wins over a `packageManager` field in `package.json` if they disagree:

| Lockfile | Manager |
|----------|---------|
| `pnpm-lock.yaml` | pnpm |
| `package-lock.json` | npm |
| `yarn.lock` | yarn |
| `bun.lock` / `bun.lockb` | bun |

#### pnpm → always install, never symlink

```bash
[ -L node_modules ] && rm node_modules   # stale link from an earlier setup
pnpm install
```

Drop the stale link **before** installing. An earlier setup — or a worktree you
resumed into via step 1 — may have left a symlinked `node_modules` behind, and
installing over it writes straight into the root checkout's tree.

This holds whether or not the root checkout already has a `node_modules` — seeing
one there is not a reason to reach for the symlink. pnpm's `node_modules` is a tree
of symlinks into `node_modules/.pnpm`; layering another symlink over it points every
resolved dependency path back into the root checkout's store, and any later install
writes *through* the link and mutates the root's tree. The install is cheap:
packages hardlink from pnpm's global store, so nothing is re-downloaded.

#### npm / yarn / bun → the manifest diff decides

```bash
git diff --quiet origin/<integration-branch> -- package.json <lockfile>
```

| Manifests | Do this |
|-----------|---------|
| Identical (exit 0) | Symlink — instant, zero disk |
| Differ (exit 1) | Real install in the worktree |

```bash
ROOT=$(git worktree list --porcelain | head -1 | cut -d' ' -f2)
ln -s "$ROOT/node_modules" node_modules
```

If the root checkout has no `node_modules`, there is nothing to link — run the
project's install command in the worktree instead.

**Symlinking is sandbox-permitted** because both the link and its target sit under
the repository root, which is in the sandbox's writable roots. Verified: `ln -s`
plus read-through both succeed under the default sandbox.

**A symlinked `node_modules` is shared with the root checkout.** Anything installed
in the worktree writes *through* the link and mutates the root's tree. That is why
the manifest diff decides — when the branch touches dependencies, install for real.

### 4. Baseline

Run the project's verification gate before touching plan tasks. A dirty baseline
makes every later failure ambiguous.

## When a Command Actually Fails

A permission or sandbox error means the path is wrong or the sandbox config
changed. In order:

1. Re-check the worktree path is inside the repository root.
2. Retry the exact command with the sandbox disabled.
3. Still failing → **stop and report to your human partner.**

Working in the root checkout is never step 4.

## Finishing

Do not invent a teardown flow. Hand off to **superpowers:finishing-a-development-branch**
for merge and cleanup. Merges into root are fast-forward only; if it will not
fast-forward, rebase the branch in the worktree and retry. Never force.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "using-git-worktrees says to fall back to the current directory on a sandbox denial" | That clause is overridden by this skill. The repo root is writable, so worktree creation succeeds; a denial means a wrong path, not a reason to work in place. |
| "They declined the worktree, but the Iron Rule says no exceptions" | Step 0 consent is real, and their answer outranks this skill. Tell them what it costs, then do as they asked. This is the one exception; a sandbox denial is not. |
| "I'm already on a feature branch, that's enough isolation" | A branch is not a worktree. The root checkout must stay on the integration branch so parallel sessions do not collide. |
| "The plan is 2 tasks / one file — a worktree is overkill" | Setup is three commands plus a dependency step. Size never changes the rule. |
| "Root already has `node_modules`, I'll just link it" | Not in a pnpm repo. A visible `node_modules` is not a signal to symlink — the lockfile decides. |
| "`pnpm install` will re-download everything" | It hardlinks from the global store. Cost is near zero; a poisoned root checkout is not. |
| "I'll create the worktree after I confirm the approach works" | The confirmation edits land in the root checkout. Worktree first. |
| "No native worktree tool here, so I'll skip it" | `git worktree add` is the documented fallback. Missing tooling is not missing isolation. |

## Red Flags — STOP

- About to edit a file whose path starts at the repository root during plan execution
- Thinking "sandbox blocked it, so I'll work here instead"
- `git branch --show-current` in the root checkout returns something other than the integration branch
- About to symlink `node_modules` in a repo that has a `pnpm-lock.yaml`
- Running an install in a worktree whose `node_modules` is a symlink — whenever it was made
- Symlinking `node_modules` when the root checkout has none — the link dangles

**All of these mean: stop, set up the worktree, move the work there.**
