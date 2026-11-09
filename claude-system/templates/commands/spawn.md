---
description: Launch an adjacent session on one project, already working on a task
argument-hint: "<project> [slug] --task \"…\" [--model m] [--effort e] [--terminal]"
---

<!--
Template. Lives at ~/Projects/.claude/commands/spawn.md. The heavy lifting is a launcher
script; the command file tells the orchestrator how to choose the options, read the exit
codes, and close the session afterwards.
-->

Spawn a project-named **adjacent session**, a peer of this orchestrator, already working on a
task. By default it is a **background session** (no window, supervisor-run); `--terminal` opens
a Remote Control window Ross can drive from his phone instead. Doctrine: root `CLAUDE.md`,
"Command center".

**Usage:** `/spawn <project> [slug] --task "<text>" [--model <m>] [--effort <e>] [--terminal]`

1. **Project name.** If Ross typed `/spawn` with no project, ask which. When the orchestrator
   decides to spawn (the normal case), it knows the project already: **no confirmation.**
2. **Validate** that the name is a real folder under `~/Projects`. If it isn't, say so rather
   than launching something wrong.
3. **Model and effort** come from the task-shape table in `CLAUDE.md`. Always pass `--model`;
   if it is omitted the script falls back to `sonnet`, never to the orchestrator's own model.
4. **Backend.** Background by default when a task is given. Its role (commit your own work with
   named paths; never push, open a PR or rewrite history; run the close-out; ask questions by
   `SendMessage`) comes from the `project-worker` agent file, so don't repeat it in the task.
5. **Run it**, passing this session's name and stable ref as `--from` so the spawn knows whom
   to report to:
   ```bash
   ~/Projects/.claude/scripts/Spawn-Session.sh <project> [slug] \
     --from "<name> [<ref>]" --model <m> [--effort <e>] [--terminal] \
     --task "<what to do, scoped to this project, and what done looks like>"
   ```
6. **Read the exit code.**
   - `0` spawned: the script prints the name, the ID and the close command.
   - `3` the project folder was never trusted. That prompt is Ross's to accept: tell him to
     open a session in that folder once, accept, exit, then spawn again.
   - `5` launched but never started. List the fleet, read the daemon line, remove the row.
   - `1` any other error; the script said why.
7. **Report in one line:** session name, path, model/effort, and whether it is reachable from
   the phone.
8. **Messaging it.** The printed name is the `SendMessage` address. A background session that
   sat idle gets stopped by the supervisor, so run `fleet.sh ensure <name>` before any message.
   Don't subscribe to idle notifications for a spawn that carries `--from`: its final
   `SendMessage` is the one completion signal. Never poll.
9. **Close it when done.** When its final report arrives and nothing waits on Ross, check its
   commits (`git log -1 --stat`) or the paths it left dirty, then `fleet.sh stop <name>` and
   `fleet.sh rm <name>`.

Session names are `<project>` or `<project>-<slug>`; the slug keeps parallel sessions on one
project apart. A spawn is local only: no remotes, no cloud routine. It loads the same root and
project `CLAUDE.md` as any session, and its agent file blocks push, PR and history rewrites in
code (`worker-guard.py`).
