# portfolio — Operating Instructions

**What's being built:** Ross's public GitHub face. This repo is
`github.com/ossger/ossger`, so its `README.md` renders on the GitHub profile
page. `homelab/` holds the sanitized home lab showcase it links to.

Roadmap: `PLAN.md`.

## What this is (and isn't)

- **Not the home lab.** `~/Projects/homelab` is the source of truth, and it is
  **read-only** from here (same shape as `golden-bridges → homelab`). Never
  edit it from a session here, and never copy files across wholesale.
  Everything under `homelab/` is fresh prose or a re-typed excerpt.
- **Not the resume.** Job-search copy (`~/Projects/job-search`) is T1 and never
  lands here verbatim. The profile README restates only what is already
  public on LinkedIn.
- Audience: recruiters and hiring managers for help desk / desktop support,
  network administrator, and systems administrator roles. Keep it scannable
  and factual, with numbers from the sources and no invented outcomes.

## Scrub gate (every commit; the repo is public)

Before staging, run this and justify or fix every hit:

```sh
grep -rnE -i 'infrarg|terraformer|tailnet|ts\.net|password|passwd|secret|apikey|api_key|token|thumbprint|[0-9a-f]{20,}|([0-9]{1,3}\.){3}[0-9]{1,3}|svc-[a-z]+' --exclude-dir=.git .
```

Allowed residue: `photocull.infrarg.com` (already public), invented example
addresses and subnets, `svc-example`, and generic uses of words like "token".
No real hostnames, subnets, tailnet or node names, thumbprints, account names,
credentials, employer or client names, health or financial detail.

## Lab status page (`homelab/STATUS.md`; Ross, 2026-11-09)

The public, current view of the lab: what it consists of and where each piece
stands, so the showcase is never a snapshot. **Refreshed at the close-out of
every session that changes the lab** (a lab change made, a lab ticket
progressed or closed, a component added, started or retired), by whichever
session did the work: the orchestrator, a homelab session, or `workbench`.
Pure study or drill sittings that change nothing in the lab don't touch it.

A refresh, in this order:
1. Bump `Last updated:`.
2. Fix the affected rows in **At a glance** (status vocabulary is fixed:
   Running, In progress, Planned, Deferred, Retired).
3. Add one dated line at the top of **Recent changes** (keep 10; the oldest
   drops off), and adjust **Current focus** / **Next up** if they moved.
4. If a component was added or retired, fix its row in `homelab/README.md`
   so the two pages agree.
5. Run the scrub gate below, then commit `homelab/STATUS.md` (and
   `homelab/README.md` if touched) as its own portfolio commit, named paths
   only, message `Lab status: <what changed>`.

Content rules on top of the scrub gate: no ticket numbers, no job-search or
interview framing, no target employers; lab work is called lab work; every
line traces to a homelab commit or ticket. An open security finding (an
exposed key, a rule that lets traffic through) goes on the page only once it
is remediated. The push to GitHub follows the root
`CLAUDE.md` commit grant.

## System showcase (`claude-system/`)

A public tour of the `~/Projects` Claude Code setup: `README.md` (overview,
architecture diagram, delegation ladder, queue, surfaces, tiers, close-out)
and `templates/` (sanitized rewrites of an agent file, a command, the worker
guard hook, a standing-orders file). Source: the root scaffolding
(`~/Projects/CLAUDE.md`, `SECURITY.md`, `MACHINES.md`, `.claude/`), read-only,
rewritten, never copied wholesale.

**Refreshed when the root scaffolding materially changes:** a new or retired
agent, command, standing session or script the page describes, or a doctrine
change (the ladder, the model table, the commit grant, the tiers, the
close-out order). Routine project work doesn't touch it.

Same scrub gate and content rules as the rest of this repo, plus: no project
names that reveal private matters (generalize to the registry categories), no
absolute home paths (write `~/Projects`), no session names, IDs or URLs, no
account labels, no ticket numbers, no dates of Ross's decisions. After the
scrub gate, also grep `claude-system/` for emails, phone numbers, `session_`,
`/Users/`, and each private project name from `PROJECTS.md`; justify or fix
every hit. If the guard template changes, `python3 -I
claude-system/templates/scripts/worker-guard.py --selftest` must pass.

## Project Pulse — cross-project context

Contract: `~/Projects/vault/Pulse/README.md`. At the end of substantive work,
refresh `~/Projects/vault/Pulse/portfolio.md` and commit only that file in the
vault repo. Edit only this project's own note.

## Security & data handling

Binding rules: `~/Projects/SECURITY.md`.

- **Tiers this project produces:** T0 only.
- **Remote:** GitHub (public), `ossger/ossger`. Treat every commit as already published.
- **Never leaves the machine:** n/a. Nothing non-T0 enters this repo at all.
