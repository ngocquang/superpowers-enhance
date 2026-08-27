#!/usr/bin/env python3
"""PostToolUse(Skill) hook: inject the enhance skill that supplements the base skill.

The enhance skills carry `disable-model-invocation`, so the model cannot invoke
them itself — this hook is their delivery path. It injects their full text as
additionalContext, prefixed by the skill's resolved directory so the injected
body can reference files on disk. Injecting on PostToolUse puts the supplement *after* the base
skill in context, so its scoping ("for step 3", "for the setup steps") resolves
against text the model has already read.

Also runs on PostCompact, where it releases the session's claims so a supplement
evicted by compaction is injected again on the next invocation.
"""

import errno
import json
import os
import re
import sys
import tempfile
import time

# base superpowers skill (name after the last ':') -> enhance skill directory
ENHANCE_FOR = {
    "brainstorming": "brainstorm-enhance",
    "executing-plans": "executing-plans-enhance",
    "subagent-driven-development": "executing-plans-enhance",
    "using-git-worktrees": "executing-plans-enhance",
}

STATE_DIR = os.path.join(tempfile.gettempdir(), "superpowers-enhance")
STATE_TTL = 7 * 24 * 60 * 60


def strip_frontmatter(text):
    """Drop the YAML block. It only tells Claude whether to invoke the skill —
    the hook has already made that call, so injecting it wastes context."""
    return re.sub(r"\A---\n.*?\n---\n+", "", text, count=1, flags=re.DOTALL)


def claim(payload, enhance):
    """True the first time this context sees this enhance skill, False after.

    Several base skills map to the same enhance skill, so without this a plan
    run injects executing-plans-enhance once per worktree/subagent skill.

    Keyed per *context*, not per session: subagents share the parent's
    session_id but have their own context window, so a parent claim must not
    silence them — that is exactly the plan-execution fan-out this skill exists
    for. Subagent payloads carry agent_id; the main thread's does not.
    """
    session_id = payload.get("session_id", "")
    if not session_id:
        return True
    context_id = f"{session_id}.{payload.get('agent_id') or 'main'}"
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        prune(STATE_DIR)
        fd = os.open(
            os.path.join(STATE_DIR, f"{context_id}.{enhance}"),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        os.close(fd)
        return True
    except OSError as e:
        if e.errno == errno.EEXIST:
            return False
        return True  # unwritable state dir: inject rather than stay silent


def release(payload):
    """Drop this session's claims so the next invocation injects again.

    Compaction can evict the injected supplement from the context window, but the
    claim file outlives it — so the hook would stay silent and the rest of the
    session would run on the base skill alone. PostCompact carries no agent_id
    (the payload is built without a tool-use context), so every context of the
    session is released together. A redundant re-injection costs a few thousand
    tokens; a missing one costs the supplement.
    """
    session_id = payload.get("session_id", "")
    if not session_id:
        return
    try:
        for entry in os.scandir(STATE_DIR):
            if entry.name.startswith(f"{session_id}."):
                os.unlink(entry.path)
    except OSError:
        pass


def prune(state_dir):
    cutoff = time.time() - STATE_TTL
    for entry in os.scandir(state_dir):
        try:
            if entry.stat().st_mtime < cutoff:
                os.unlink(entry.path)
        except OSError:
            pass


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    if payload.get("hook_event_name") == "PostCompact":
        release(payload)
        return

    invoked = payload.get("tool_input", {}).get("skill", "")
    enhance = ENHANCE_FOR.get(invoked.rsplit(":", 1)[-1])
    if not enhance:
        return

    if not claim(payload, enhance):
        return

    plugin_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    skill_dir = os.path.join(plugin_root, "skills", enhance)
    skill_path = os.path.join(skill_dir, "SKILL.md")
    try:
        with open(skill_path, encoding="utf-8") as f:
            body = strip_frontmatter(f.read())
    except OSError as e:
        print(f"superpowers-enhance: cannot read {skill_path}: {e}", file=sys.stderr)
        return

    context = (
        "<EXTREMELY_IMPORTANT>\n"
        f"You just invoked `{invoked}`. The `superpowers-enhance:{enhance}` skill "
        "below is a REQUIRED supplement to it: it adds detail and tightens "
        "specific steps, and does not replace the skill you just read. Follow "
        "that skill in full, and follow this one for the steps it names.\n\n"
        f"Skill directory: {skill_dir}\n"
        "Files the skill below references (`playbooks/`, `references/`) live in "
        "that directory. Build an absolute path from it to read one.\n\n"
        f"{body}\n"
        "</EXTREMELY_IMPORTANT>"
    )

    json.dump(
        {
            "systemMessage": f"superpowers-enhance: {enhance} applied over {invoked}",
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            },
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
