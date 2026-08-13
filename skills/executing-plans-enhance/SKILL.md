---
name: executing-plans-enhance
description: Supplement to superpowers:executing-plans, subagent-driven-development and using-git-worktrees — specifies the worktree setup those skills leave open, and keeps plan tasks from reaching the main checkout. Delivered by the superpowers-enhance hook; invoke manually only to re-read it.
disable-model-invocation: true
---

# Executing Plans — Enhance

## Overview

Plan execution happens on its own branch, in its own worktree. Always.

Every step of superpowers:executing-plans, superpowers:subagent-driven-development
and superpowers:using-git-worktrees still runs, unchanged. This skill adds to two
of them: it declines the latitude using-git-worktrees grants to degrade to the
current checkout when setup fails, and it fills in the setup that skill leaves
open (where the worktree lives, how dependencies are wired, what stays off-limits
once you are inside it).

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

### 3. Install dependencies in the worktree

A fresh worktree has no `node_modules`. Run a real install there. Identify the
manager from the lockfile at the repository root — the lockfile wins over a
`packageManager` field in `package.json` if they disagree:

| Lockfile | Manager |
|----------|---------|
| `pnpm-lock.yaml` | pnpm |
| `package-lock.json` | npm |
| `yarn.lock` | yarn |
| `bun.lock` / `bun.lockb` | bun |

```bash
[ -L node_modules ] && rm node_modules   # stale link from an earlier setup
<manager> install
```

**Never symlink `node_modules` to the root checkout's.** Installs write *through*
the link and mutate the root's tree — the exact isolation breach this skill exists
to prevent — and in a pnpm repo, whose `node_modules` is itself a tree of symlinks
into `node_modules/.pnpm`, every resolved dependency path points back at the root's
store. Drop a stale link **before** installing: a worktree you resumed into via
step 1 may carry one from an older setup.

Installing for real is cheap — pnpm and bun hardlink from a global store, npm and
yarn hit their local cache. A poisoned root checkout is not.

### 4. Baseline

Run the project's verification gate before touching plan tasks. A dirty baseline
makes every later failure ambiguous.

## Staying Isolated: One `.git`, Many Worktrees

A worktree gives you your own working directory and your own `HEAD`. It does not
give you your own repository:

```
git rev-parse --git-dir         → <root>/.git/worktrees/<name>   # yours
git rev-parse --git-common-dir  → <root>/.git                    # everyone's
```

Branches, tags, remotes, the object store, the reflog and `refs/stash` all live in
the common dir. A stash taken in the root checkout appears as `stash@{0}` inside
your worktree — one `git stash pop` there and the other session's work is gone.

**Never run these during plan execution, in any session, from any directory:**

| Class | Commands | What it reaches |
|-------|----------|-----------------|
| Escape hatches — any command, not just git | `git -C <path>`, `--git-dir` / `--work-tree`, `GIT_DIR` / `GIT_WORK_TREE`, and in plain Bash: `cd` out of the worktree, `../` traversal, absolute paths into the root checkout | Nothing alone — they make your cwd irrelevant, which is how every row below lands on root. Reading through them is fine; never let one carry a write. |
| Shared refs | `git branch -D` / `-f`, `git push --force`, `git push --delete`; `git stash pop` / `drop` / `clear` on an entry you did not create | Sibling sessions' branches and stashed work |
| Shared history | `git gc --prune=now`, `git reflog expire --all` | The only recovery path from the row above |
| Sibling worktrees | `git worktree remove --force`, `git worktree prune` | Another session's checkout, mid-task |

Your own worktree is yours: commit, rebase your branch, `reset --hard` your own
HEAD, `clean` your own tree, stash work *you* created. The line is whether the
effect can reach outside your working directory.

Before any write-side git command, confirm where you are:

```bash
git rev-parse --show-toplevel   # must be the worktree path, not the repo root
```

### Subagents

Isolation is not inherited. A subagent may start in the root checkout even when
you dispatched it from the worktree.

- Every dispatch prompt states the **absolute worktree path** and says to work only there.
- Before its first write, the subagent runs `git rev-parse --show-toplevel` and
  compares. Mismatch → stop and report; never `cd` into root and continue.
- The command table above binds subagents exactly as it binds you.

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

That merge — and removing your own worktree — is the one sanctioned touch of the
root checkout. It comes after the last task, never during one.

## Rationalizations

| Excuse | Reality |
|--------|---------|
| "using-git-worktrees says to fall back to the current directory on a sandbox denial" | That clause is an allowance, and this skill declines it. The repo root is writable, so worktree creation succeeds; a denial means a wrong path, not a reason to work in place. |
| "They declined the worktree, but the Iron Rule says no exceptions" | Step 0 consent is real, and their answer outranks this skill. Tell them what it costs, then do as they asked. This is the one exception; a sandbox denial is not. |
| "I'm already on a feature branch, that's enough isolation" | A branch is not a worktree. The root checkout must stay on the integration branch so parallel sessions do not collide. |
| "The plan is 2 tasks / one file — a worktree is overkill" | Setup is three commands plus a dependency step. Size never changes the rule. |
| "Root already has `node_modules`, I'll just link it" | The link is a write channel into the root checkout. Install in the worktree. |
| "The install will re-download everything" | pnpm and bun hardlink from a global store; npm and yarn hit their cache. Cost is near zero; a poisoned root checkout is not. |
| "I'm inside the worktree, so any git command is safe" | cwd scopes files, not refs. Branches, stash and the object store are shared — the command table lists what reaches out. |
| "I just need to read root's branch, `git -C` is harmless" | Reading is fine. The habit is not: the same handle is one flag away from a write, and that is how every root-mutation incident starts. |
| "Root drifted off the integration branch, I'll switch it back for them" | That is a write into another session's checkout. Report it; do not reach in. |
| "The stash is right there, it must be mine" | `refs/stash` is one stack shared by every worktree. If `git stash list` shows entries you did not create, do not touch it. |
| "The subagent runs in my worktree, it inherits the cwd" | Do not assume. Put the absolute path in the prompt and have it verify before writing. |
| "I'll create the worktree after I confirm the approach works" | The confirmation edits land in the root checkout. Worktree first. |
| "No native worktree tool here, so I'll skip it" | `git worktree add` is the documented fallback. Missing tooling is not missing isolation. |

## Red Flags — STOP

- About to edit a file whose path starts at the repository root during plan execution
- Thinking "sandbox blocked it, so I'll work here instead"
- `git branch --show-current` in the root checkout returns something other than the integration branch
- About to symlink `node_modules`, or running an install in a worktree whose `node_modules` is a symlink
- Typing `git -C`, `--git-dir`, `--work-tree`, or a path starting at the repository root into a git command
- A Bash call that `cd`s out of the worktree, traverses `../`, or names an absolute path into the root checkout
- `git stash list` shows entries you did not create — and `pop` or `drop` is the next word
- About to run `git worktree remove` / `prune`, `git gc`, or `git push --force` during plan execution
- Dispatching a subagent whose prompt does not carry the absolute worktree path

**All of these mean: stop, set up the worktree, move the work there.**
