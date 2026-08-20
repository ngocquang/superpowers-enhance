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

On Claude Code 2.1.237 and later the harness enforces part of this itself: a
session that entered its worktree through `EnterWorktree` has every git operation
aimed outside that worktree refused at the tool layer. The price is that leaving
must also go through the harness — which is what the Finishing section is for.

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

**Setup is always both halves:** create the worktree with `git worktree add` from
the root checkout, then *enter* it with the harness's own tool — `EnterWorktree`
with `path:`, or the equivalent.

Neither half substitutes for the other. `git worktree add` is what puts the
worktree at the fixed location below; a native **create** call (`EnterWorktree`
with `name:`) puts it under `.claude/worktrees/` instead, where
superpowers:finishing-a-development-branch Step 6 stops recognizing it as ours and
skips cleanup entirely. Entering through the harness is what makes the session
*isolated*: it moves the session's cwd, so the sandbox's `./` write scope follows
you in, and it is the only thing that gives you a sanctioned way back out. A plain
`cd` into the worktree leaves the session un-isolated — root stays writable and
the guard stays off, which is the exact breach this skill exists to prevent.

**Resuming a plan in a later session means entering through the tool again.** The
worktree survives on disk; the isolation does not.

Setup is these five steps, in this order.

### 1. Create the worktree root

```bash
git rev-parse --git-dir; git rev-parse --git-common-dir   # differ → already in a worktree, skip to step 4
cd "$(git rev-parse --show-toplevel)"
mkdir -p worktrees
```

**Always `./worktrees/` at the repository root.** Not `$TMPDIR`, not
`~/worktrees`, not `.worktrees` or another per-project variant — one fixed
location means every session and every subagent knows where the worktrees are
without probing for a layout. The repository root is also what the sandbox grants
write access to.

Then confirm git ignores it:

```bash
git check-ignore -q worktrees || {
  printf '\nworktrees/\n' >> .gitignore
  git add .gitignore && git commit -m "chore: ignore worktrees"
}
```

The leading newline matters: `.gitignore` files often lack a trailing one, and a
bare `echo` would splice the entry onto the last existing rule.

`worktrees/` is not hidden, so an un-ignored one lands in `git status` and in
every `ls`. Do not skip the check.

### 2. Branch off the freshly-fetched integration branch

Still in the root checkout — this is the last thing you do there until Finishing.

```bash
git fetch origin
git worktree add "worktrees/$BRANCH" -b "$BRANCH" origin/<integration-branch>
```

`git fetch` over SSH needs the sandbox disabled on a default setup; the sandbox
allows no network hosts. That is expected — see "When a Command Actually Fails".

Do not `cd` into it. That is step 3's job, and a `cd` is not the same thing.

### 3. Enter the worktree through the harness

```
EnterWorktree  path: "worktrees/$BRANCH"
```

`path:` accepts a worktree you just made with `git worktree add`, as long as it
appears in `git worktree list`. This is the step that isolates the session: cwd
moves, the sandbox's write scope moves with it, and `ExitWorktree` becomes
available as the sanctioned way out at Finishing.

Confirm before continuing:

```bash
git rev-parse --show-toplevel   # must be the worktree path
```

**No worktree tool in this harness at all?** Then `cd "worktrees/$BRANCH"` is all
you have. Say so out loud, because what you lose is the enforcement: the session
is not isolated, nothing refuses a command aimed at root, and every rule under
"Staying Isolated" falls back to your own discipline. Finishing then uses Step 5's
`cd "$MAIN_ROOT"` unchanged — there is no worktree session to exit.

### 4. Install dependencies in the worktree

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

### 5. Baseline

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

### The harness enforces part of this now

On Claude Code 2.1.237 and later, a session that entered its worktree through the
harness has every git operation aimed outside it **refused at the tool layer** —
`git -C <root>`, `--git-dir`, a `cd` out. Refused for *reads* too, not only
writes, and `dangerouslyDisableSandbox` does not lift it. The sandbox separately
refuses plain writes into root with `Operation not permitted`, because its `./`
write scope is the session's cwd. Two independent layers; neither negotiable.

Two consequences worth knowing before you trip over them:

- **Run plain, single commands inside the worktree.** A compound command carrying
  a pipe or a redirect is refused as "too complex to verify that it stays inside
  the worktree" — even when every part of it was legal. Read the output yourself
  instead of piping it into `head` or `grep`.
- **A refusal is not a bug to route around.** It is this skill, implemented. Seeing
  one means you were about to reach into root; the sanctioned route is in Finishing.

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

These need the sandbox disabled on a default setup. Expected, not an escalation:

| Command | Why |
|---|---|
| `git fetch` / `git pull` over SSH | The sandbox allows no network hosts |
| `git worktree remove` | Deleting the worktree directory is refused — and it can fail *partway*; see Finishing step 5 |
| `git branch -d` / `-D` | Its `.git/config` write is refused. The branch is still deleted anyway — confirm with `git branch --list <branch>` rather than trusting that the warning was harmless |

**A tool-layer refusal is different.** "This session is isolated in the worktree
… refusing to run it" is not a sandbox error, and disabling the sandbox does not
help. Nothing to retry: you aimed a command out of the worktree.

## Finishing

Do not invent a teardown flow. Hand off to **superpowers:finishing-a-development-branch**,
starting at its Step 1, from inside the worktree. Leaving early breaks it: Step 1
would run the test suite against the integration branch instead of your work, and
Step 2 would conclude there is no worktree to clean up.

**Supply Step 2's values yourself.** Its own probe `cd`s into the shared `.git`,
which an isolated session refuses — and the values then come back *empty*, so its
table reads "normal repo, no worktree to clean up" and Step 6 silently skips
cleanup. These run fine inside the worktree. Plain, one per call:

```bash
git worktree list --porcelain   # first record → MAIN_ROOT + root's current branch
git rev-parse --show-toplevel   # WORKTREE_PATH
git rev-parse --git-dir
git rev-parse --git-common-dir  # differs from --git-dir → you are in a worktree
```

The first record of `--porcelain` output is always the main checkout: its
`worktree` line is `MAIN_ROOT`, its `branch` line is what root has checked out.
Use `--porcelain` — the plain form's columns are not parseable.

**If your partner picks Option 2 (push + PR) or Option 3 (keep as-is), you are
done.** Both deliberately keep the worktree; nothing below applies.

### Amendments to Step 5 Option 1 — merge locally

That merge, and removing your own worktree, is the one sanctioned touch of the
root checkout. It comes after the last task, never during one. Option 1 changes in
five ways, in this order.

**1. Hard gate: root must be on the integration branch.** Read it off the
`git worktree list --porcelain` record above — no `git -C` needed, and none
possible. Anything else means a sibling session owns that checkout: report it and
stop. A `--ff-only` merge into the wrong branch is the hazard worth blocking.

A *dirty* root is not a blocker. You cannot see it from in here anyway, and
`git merge --ff-only` refuses on its own if local changes would be overwritten —
report it after the exit and let the merge be the backstop.

**2. Rebase while still inside the worktree, then re-verify.**

```bash
git fetch origin
git rebase origin/<integration-branch>
```

Re-run the project's verification gate afterwards: the rebase moved your commits
onto code Step 1 never tested. This is also what makes the fast-forward below a
guarantee instead of a retry loop.

**Skip the rebase if the branch is already pushed and shared** — rewriting
published history is worse than a merge commit. Say so and let your partner choose.

**3. Leave through the harness.** `ExitWorktree` with `action: "keep"`.

Never `"remove"`: it deletes the branch you are about to merge, and refuses
outright while that branch carries unmerged commits — so it either destroys the
work or blocks. Step 5's own `cd "$MAIN_ROOT"` is not a substitute either: in an
isolated session the sandbox's write scope follows the cwd, so root stays
unwritable until the harness moves you back.

If the exit reports no active worktree session, this session never entered through
the tool — see the handoff at the end of this section.

**4. Merge fast-forward only.** You are in root now:

```bash
git merge --ff-only <branch>
```

This overrides Step 5 Option 1's plain `git merge` — into root it is ff-only.
**Skip Step 5's `git checkout <base>` and `git pull` as well:** root is already on
the integration branch by the Iron Rule, and step 2 already rebased onto a fresh
fetch. If the merge refuses, the integration branch moved in between — re-enter
the worktree, rebase again, retry. Never force.

**5. Cleanup: Step 6, with one addition.** `git worktree remove "$WORKTREE_PATH"`
can fail *partway* under the sandbox — it deletes some tracked files, hits
`Operation not permitted`, and leaves behind a worktree that now looks dirty and
refuses to be removed without `--force`. The command table forbids `--force` and
Step 6 says never on your own initiative, so discriminate before you choose:

```bash
git -C "$WORKTREE_PATH" status --porcelain -uall
```

| Output | What it is | What to do |
|---|---|---|
| Only ` D ` lines, all on tracked files | The partial-delete artifact | Retry `git worktree remove --force` with the sandbox disabled |
| Any `??` or ` M ` | Real uncommitted work that exists nowhere else | Step 6's ask-your-partner path, unchanged |

This `git -C` is fine: you are in root, and the target is the worktree you own —
not the other way round.

**If you cannot leave the worktree** — the session never entered through the
harness, or the exit is unavailable — the merge is not yours to complete. Leave
the branch and the worktree in place and hand over the exact commands:

```
Branch <branch> is committed, green, and rebased onto origin/<integration-branch>.
This session can't reach the root checkout, so the merge is yours:

    cd <root>
    git merge --ff-only <branch>
    git worktree remove <worktree-path>
    git branch -d <branch>
```

Stopping there with a clean handoff is a success. Hunting for a way to write into
root from inside the worktree is not — there isn't one, by design.

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
| "No worktree tool in this harness, so I'll skip the worktree" | `git worktree add` plus a `cd` still gives you the isolated working directory. Missing tooling costs you the enforcement, not the isolation. |
| "The red flags say never `cd` out of the worktree, so I can't merge" | That list is scoped to plan execution. Step 5 Option 1 of Finishing is exactly where leaving the worktree belongs — through `ExitWorktree`, not a `cd`. |
| "I'll exit the worktree first, then start the finishing skill" | Its Step 1 would test the integration branch and its Step 2 would see no worktree to clean up. Hand off from inside; leave only at Option 1, step 3. |
| "I'll merge into root from inside the worktree with `git -C`" | The harness refuses it outright, reads included. There is no route from in there — leave through `ExitWorktree` first. |
| "The refusal is a sandbox error, so I'll retry with the sandbox disabled" | Disabling the sandbox does not lift a tool-layer refusal; it stays refused. The two failures look alike and are not. |
| "`EnterWorktree` can create the worktree itself — one call instead of two" | Its `name:` form creates under `.claude/worktrees/`, which finishing-a-development-branch Step 6 does not recognize as ours, so the worktree is never cleaned up. Create with `git worktree add`, enter with `path:`. |
| "The worktree from last session is still on disk, I'll just `cd` into it" | A `cd` leaves the session un-isolated: root writable, guard off, no sanctioned exit. Re-enter through the tool. |
| "`git worktree remove` failed and `--force` is forbidden, so I'll leave it" | Check `status --porcelain -uall` first: only ` D ` lines means the sandbox half-deleted it and `--force` is the fix. `??` or ` M ` means ask. |
| "I'm blocked from root, so I'll just call it done and stop" | Stopping is right; silence is not. Report the branch as committed, green and rebased, and hand over the exact merge commands. |
| "This project already has a `.worktrees/`, I'll reuse it" | The root is `./worktrees/`, always. A second layout is one more place a sibling session has to guess at. |

## Red Flags — STOP

- About to edit a file whose path starts at the repository root during plan execution
- Thinking "sandbox blocked it, so I'll work here instead"
- `git branch --show-current` in the root checkout returns something other than the integration branch
- About to symlink `node_modules`, or running an install in a worktree whose `node_modules` is a symlink
- Typing `git -C`, `--git-dir`, `--work-tree`, or a path starting at the repository root into a git command **during plan execution**
- A Bash call that `cd`s out of the worktree, traverses `../`, or names an absolute path into the root checkout **during plan execution**
- `git stash list` shows entries you did not create — and `pop` or `drop` is the next word
- About to run `git worktree remove` / `prune`, `git gc`, or `git push --force` during plan execution
- `cd`-ing into an existing worktree instead of entering it through the harness
- Retrying a tool-layer worktree refusal with the sandbox disabled
- Creating the worktree with a native `name:` call, landing it outside `./worktrees/`
- Dispatching a subagent whose prompt does not carry the absolute worktree path

**All of these mean: stop, set up the worktree, move the work there.**

**Not a red flag:** Step 5 Option 1 of the Finishing handoff. Leaving through
`ExitWorktree`, then merging and cleaning up from root, belongs there — after the
last task, once the branch is committed, green and rebased. See Finishing.
