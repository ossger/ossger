#!/usr/bin/env python3
"""PreToolUse guard for orchestrator workers (template, condensed from the working version).

Wire it as a `PreToolUse` hook with matcher "Bash" in an agent file:

    hooks:
      PreToolUse:
        - matcher: "Bash"
          hooks:
            - type: command
              command: "python3 -I ~/Projects/.claude/scripts/worker-guard.py subagent"

Claude Code sends the pending tool call as JSON on stdin. This script parses the Bash command
text and exits 2 (block; the reason on stderr goes back to the model) when it crosses a hard
line. It only parses; it never runs anything.

  worker-guard.py session    an adjacent session: may commit its OWN work, by named paths
  worker-guard.py subagent   an in-process subagent: never commits
  worker-guard.py --selftest run the built-in cases

Hard lines:
  * no push, pull, merge, rebase, reset, ref surgery or amend
  * no GitHub writes through `gh` (PRs, releases, repo edits); reads are fine
  * commits name their paths: `git add <paths>` then `git commit -m msg -- <paths>`;
    never `git add -A/./-u/-f`, never `git commit -a`
  * the working copy is shared with other sessions, so no stash, clean, checkout, switch,
    or `restore` outside `--staged`

A seat belt for a cooperative but fallible agent, not a sandbox: it cannot see inside a script
file that gets run, and interpreter one-liners are matched only by a coarse pattern.
"""
import json
import os
import re
import shlex
import sys

SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
WRAPPERS = {"command", "env", "sudo", "time", "nice", "nohup", "exec", "builtin", "xargs"}
INTERPRETERS = {"python", "python3", "perl", "ruby", "node"}
HISTORY = {"push", "pull", "merge", "rebase", "reset", "filter-branch", "filter-repo",
           "update-ref", "replace", "gc", "prune"}
SHARED_TREE = {"stash", "clean", "checkout", "switch"}
WHOLE_TREE = {".", "./", "*", ":/", ":(top)", "/"}
GH_READ_VERBS = {"view", "list", "status", "diff", "checks", "search", "browse"}
GIT_GLOBAL_WITH_ARG = {"-C", "-c", "--git-dir", "--work-tree"}
COMMIT_ARG_SHORT = "mFCct"                      # short flags that take a value
COMMIT_ARG_LONG = {"--message", "--file", "--author", "--date", "--fixup", "--squash"}


def block(msg):
    return msg + " (see ~/Projects/CLAUDE.md, 'Commit grant'; ask the orchestrator)"


def strip_heredocs(s):
    """Drop heredoc bodies: their text is data, not commands."""
    out, delim = [], None
    for line in s.split("\n"):
        if delim:
            if line.strip() == delim:
                delim = None
            continue
        out.append(line)
        m = re.search(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1", line)
        if m:
            delim = m.group(2)
    return "\n".join(out)


def segments(s):
    """Split on ; & | newline ( ) { } and backticks, outside quotes."""
    segs, cur, quote, i = [], [], None, 0
    while i < len(s):
        c = s[i]
        if quote:
            cur.append(c)
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
            cur.append(c)
        elif c == "\\" and i + 1 < len(s):
            cur += [c, s[i + 1]]
            i += 1
        elif c in ";&|\n(){}`":
            segs.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    segs.append("".join(cur))
    return [x.strip() for x in segs if x.strip()]


def subshells(s):
    """$(...) and backtick substitutions run even inside double quotes."""
    return re.findall(r"\$\(([^)]*)\)", s) + re.findall(r"`([^`]*)`", s)


def tokens(seg):
    try:
        toks = shlex.split(seg)
    except ValueError:
        toks = seg.split()
    while toks and re.match(r"^[A-Za-z_]\w*=", toks[0]):   # leading VAR=value
        toks.pop(0)
    return toks


def check_add(rest):
    after_dd = False
    for t in rest:
        if t == "--" and not after_dd:
            after_dd = True
        elif not after_dd and t.startswith("--") and t in ("--all", "--update", "--force"):
            return block("git add " + t + " stages more than named paths")
        elif not after_dd and t.startswith("-") and not t.startswith("--") and set(t[1:]) & set("Auf"):
            return block("git add " + t + " stages more than named paths (or force-adds ignored files)")
        elif t in WHOLE_TREE or t.endswith("/."):
            return block("git add " + t + " stages the whole tree; name the paths")
    return None


def check_commit(mode, rest):
    if mode == "subagent":
        return block("a subagent never commits; leave the tree dirty for the parent session")
    j = 0
    while j < len(rest):
        t = rest[j]
        if t == "--":
            paths = rest[j + 1:]
            if not paths:
                break
            if any(p in WHOLE_TREE for p in paths):
                return block("git commit -- " + " ".join(paths) + " is the whole tree")
            return None
        if t.startswith("--"):
            name = t.split("=", 1)[0]
            if name in ("--amend", "--all"):
                return block("git commit " + name + " rewrites history or commits unnamed paths")
            if name in COMMIT_ARG_LONG and "=" not in t:
                j += 1
        elif t.startswith("-") and len(t) > 1:
            for k, ch in enumerate(t[1:], 1):
                if ch == "a":
                    return block("git commit -a commits every tracked change, including other sessions' files")
                if ch in COMMIT_ARG_SHORT:
                    j += 1 if k == len(t) - 1 else 0   # value is the next token, or glued on
                    break
        j += 1
    return block("git commit must name its paths: git add <paths>, then git commit -m '<msg>' -- <paths>")


def check_git(mode, args):
    i = 0
    while i < len(args) and args[i].startswith("-"):        # skip global options
        i += 2 if args[i] in GIT_GLOBAL_WITH_ARG else 1
    if i >= len(args):
        return None
    sub, rest = args[i], args[i + 1:]
    if sub in HISTORY:
        return block("git " + sub + " is blocked (no push, pull, merge, rebase, reset or history rewrite)")
    if sub in SHARED_TREE:
        return block("git " + sub + " can destroy or hide other sessions' uncommitted work")
    if sub == "restore":
        if not ({"--staged", "-S"} & set(rest)) or ({"--worktree", "-W"} & set(rest)):
            return block("git restore outside --staged can discard other sessions' work")
        return None
    if sub == "commit":
        return check_commit(mode, rest)
    if sub == "add":
        return check_add(rest)
    if sub in ("cherry-pick", "revert", "am") and mode == "subagent":
        return block("a subagent never commits; git " + sub + " makes commits")
    if sub == "branch" and any(re.match(r"^-[a-zA-Z]*[dDmMfcC]|^--(delete|move|force|copy)", t) for t in rest):
        return block("git branch with that flag changes or removes refs")
    if sub == "tag" and {"-d", "--delete", "-f", "--force"} & set(rest):
        return block("git tag with that flag deletes or moves a tag")
    if sub == "remote" and rest and rest[0] in ("add", "remove", "rm", "rename", "set-url"):
        return block("git remote " + rest[0] + " edits remotes")
    if sub == "worktree" and rest and rest[0] != "list":
        return block("git worktree " + rest[0] + " is blocked")
    return None


def check_gh(args):
    words = [a for a in args if not a.startswith("-")]
    if not words:
        return None
    noun, verb = words[0], (words[1] if len(words) > 1 else "")
    if noun == "api":
        writes = {"-X", "--method", "-f", "-F", "--field", "--raw-field", "--input"}
        return block("gh api with a method or body is a GitHub change") if writes & set(args) else None
    if noun == "auth":
        return None if verb == "status" else block("gh auth " + verb + " changes credentials")
    if noun in ("help", "version") or verb in GH_READ_VERBS:
        return None
    return block("gh " + noun + " " + verb + " is a GitHub change (no PRs, merges, releases or edits)")


def check_segment(mode, seg):
    toks = tokens(seg)
    if not toks:
        return None
    head = os.path.basename(toks[0])
    if head in WRAPPERS:                                    # env git push, xargs git ..., sudo bash -c
        for j, t in enumerate(toks[1:], 1):
            if os.path.basename(t) in ({"git", "gh", "eval"} | SHELLS):
                return check_segment(mode, " ".join(shlex.quote(x) for x in toks[j:]))
        return None
    if head == "git":
        return check_git(mode, toks[1:])
    if head == "gh":
        return check_gh(toks[1:])
    if head == "eval":
        return decide(mode, " ".join(toks[1:]))
    if head in SHELLS:                                      # bash -c '...'
        for k, t in enumerate(toks[1:], 1):
            if re.match(r"^-[A-Za-z]*c[A-Za-z]*$", t) and k + 1 < len(toks):
                return decide(mode, toks[k + 1])
        return None
    if head in INTERPRETERS:
        joined = " ".join(toks)
        if re.search(r"git\W+(push|pull|merge|rebase|reset|commit|stash|clean|checkout|switch)\b", joined):
            return block("run git directly so it can be checked; an interpreter one-liner cannot")
        if re.search(r"\bgh\W+(pr|release|repo|workflow)\b", joined):
            return block("run gh directly so it can be checked")
    return None


def decide(mode, command):
    """Return a block reason, or None to allow."""
    cleaned = strip_heredocs(command)
    for seg in segments(cleaned):
        reason = check_segment(mode, seg)
        if reason:
            return reason
    for inner in subshells(cleaned):
        reason = decide(mode, inner)
        if reason:
            return reason
    return None


CASES = [  # (mode, command, should_block)
    ("session", "git status && git log -3", False),
    ("session", "git add README.md docs/a.md && git commit -m 'Fix links' -- README.md docs/a.md", False),
    ("session", "git commit -m 'msg'", True),                    # no named paths
    ("session", "git commit -am 'msg' -- a.md", True),           # -a
    ("session", "git commit --amend --no-edit -- a.md", True),
    ("session", "git add -A", True),
    ("session", "git add .", True),
    ("session", "git push origin main", True),
    ("session", "cd repo; git -C . reset --hard HEAD~1", True),
    ("session", "git stash", True),
    ("session", "git restore --staged a.md", False),
    ("session", "git restore a.md", True),
    ("session", "bash -c 'git push'", True),
    ("session", "env FOO=1 git push", True),
    ("session", "echo $(git rebase main)", True),
    ("session", "cat <<'EOF'\ngit push\nEOF", False),          # heredoc body is data
    ("session", "gh pr view 12", False),
    ("session", "gh pr create --fill", True),
    ("session", "gh api repos/o/r/pulls -f title=x", True),
    ("session", "python3 -c \"import os; os.system('git push')\"", True),
    ("subagent", "git add a.md && git commit -m x -- a.md", True),
    ("subagent", "git diff --stat", False),
]


def selftest():
    failed = 0
    for mode, cmd, want in CASES:
        got = decide(mode, cmd) is not None
        if got != want:
            failed += 1
            print("FAIL [%s] %r: blocked=%s, expected %s" % (mode, cmd, got, want))
    print("%d/%d cases pass" % (len(CASES) - failed, len(CASES)))
    return 1 if failed else 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "session"
    if mode == "--selftest":
        sys.exit(selftest())
    if mode not in ("session", "subagent"):
        print("worker-guard: unknown mode " + mode, file=sys.stderr)
        sys.exit(2)
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)        # not a hook payload: don't wedge unrelated tools
    if payload.get("tool_name") != "Bash":
        sys.exit(0)
    command = (payload.get("tool_input") or {}).get("command", "")
    try:
        reason = decide(mode, command)
    except Exception as exc:   # fail closed on our own bug
        reason = block("guard error (" + type(exc).__name__ + "); simplify the command")
    if reason:
        print("BLOCKED by the worker guard: " + reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
