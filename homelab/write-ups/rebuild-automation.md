# Rebuild automation

`Lab/` is a declarative, idempotent PowerShell system meant to stand the whole lab up on a
fresh Hyper-V host. It runs alongside a day-to-day scripts folder: I do work by hand first,
then codify it.

## Layers

```
config/     authoritative values: domain, networks, VM specs, OUs, users, GPOs, CA settings
   |
modules/    Ensure-* functions, one module per area (Hyper-V, AD, PKI, file server, Docker)
   |
phases/     one file per phase: declares its dependencies and calls the modules
   |
orchestrator   discovers phases, sorts them, runs build then verify, writes a log
```

Nothing is hardcoded in a script. Names, addresses and sizes come from `.psd1` data files, so
changing the domain or a VM spec is an edit to config, not to code.

## The Ensure contract

Every resource function checks current state first and returns a result object with one of:

| Status | Meaning |
|---|---|
| Created | Resource did not exist and was created |
| Updated | Resource existed but differed from the spec and was corrected |
| Unchanged | Already correct, no action taken |
| ManualStepRequired / Skipped | A gate that cannot be automated, with a pointer to the guide |
| Failed | The check or change threw; the detail says why |

Re-running a phase on a healthy lab should print mostly `Unchanged`. That makes a re-run a
safe drift check as well as a repair.

## Phase ordering

Each phase file declares a name, a description and a list of dependency phase names. The
orchestrator loads them all and runs a depth-first topological sort. It throws on a missing
dependency and on a cycle, and the error includes the path that formed the cycle. A sample is
in [samples/phase-ordering.ps1](../samples/phase-ordering.ps1).

The 15 phases run from virtual switches and VMs, through forest, OUs, GPOs, file server, PKI
and hybrid identity, to the Docker host, monitoring, Traefik and logging. Three are
deliberately stubs with a manual gate (remote access, firewall VM, firewall ruleset), and the
offline root CA is never touched over the network.

## Verify tables

Every phase has a separate verify function that makes no changes. The orchestrator runs build
then verify for each phase, stops on the first failed check, and writes a JSON log with phase
names, durations and per-resource outcomes. A standalone verify script runs only the verify
side across every phase and exits non-zero on any failure, so it can be scheduled. See [samples/verify-table.ps1](../samples/verify-table.ps1).

## Command-line behaviour

| Invocation | Effect |
|---|---|
| `Invoke-LabBuild.ps1 -WhatIf` | Prints the resolved phase order and each description, changes nothing |
| `Invoke-LabBuild.ps1` | Runs all phases in dependency order |
| `Invoke-LabBuild.ps1 -Phase <name>` | Runs one phase |
| `Invoke-LabBuild.ps1 -From <name>` | Skips every phase before the named one |

## Script conventions

- PowerShell 7, `#Requires -RunAsAdministrator`, `Set-StrictMode -Version Latest`, and
  `$ErrorActionPreference = 'Stop'`.
- Remote execution passes values with `Invoke-Command -ArgumentList` rather than `$using:`.
- Steps that could fail silently are caught in `try/catch` and reported with a warning, never swallowed.
- A version-history block at the top of each file, and a verification summary at the end.
- Commands I invoke directly carry a consistent naming prefix after the verb, so tab
  completion lists everything I wrote.

## Lessons that shaped the design

- Some ADCS operations fail over PowerShell remoting because of double-hop authentication, so
  the CA promotion step is a manual gate rather than a hack.
- Compose `up -d` is already idempotent, so the Docker phases push files and let Compose
  decide what changed.
- Things that cannot be scripted safely (an offline root, a firewall appliance GUI) are
  documented as gates, not forced into code.

**Skills demonstrated:** PowerShell 7 module design, idempotent configuration, desired-state
thinking, dependency graphs, dry-run support with `-WhatIf`, structured logging, data-driven
config, separating build from verification.
