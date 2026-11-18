# Lab status

Last updated: 2026-11-18

The lab was fully built by mid-2026, then sat powered off for several months. It is coming back
one server at a time, in dependency order (firewall, domain controller, CAs, file server, sync
server, Linux host), and each restart is a ticket with a plan, verification and a rollback. In the
table, **Planned** means built before the outage with its restart queued, or new and approved.

## At a glance

| Component | Status | Since/last change | Note |
|---|---|---|---|
| Hyper-V host | Running | 2026-11-07 | Pre-flight done 2026-10-30; host sleep turned off so it can't suspend the VMs |
| AD DS forest on DC1 | Running | 2026-11-02 | Back after the outage; `dcdiag` clean, time-sync chain documented |
| Group Policy | Running | 2026-11-02 | Served by DC1 |
| FS1 (file server, DFS) | Planned | — | Next server in the restart order |
| Two-tier PKI | Running | 2026-11-18 | CA-ISSUING back and publishing revocation data over HTTP as well as LDAP; CA-ROOT stays offline by design |
| Hybrid identity (SYNC1) | Planned | — | Restart and sync check queued |
| FW1 (pfSense) | Running | 2026-11-18 | Ruleset verified against the design; web-admin certificate reissued from the issuing CA |
| Remote access (mesh VPN) | Running | 2026-10-22 | Tag-based access policy written down; full remote-path check queued |
| SSH certificate authority | In progress | 2026-11-07 | CA key and user certificate verified; server-side checks wait on DOCKER1 |
| DOCKER1 (Ubuntu, Docker) | Planned | — | Restart queued after its storage is reattached; brings back the SSSD domain join |
| Traefik | Planned | — | Returns with DOCKER1 |
| Prometheus, Grafana, Uptime Kuma | Planned | — | Return with DOCKER1; a sweep of all 12 monitors follows |
| Loki + Promtail | Planned | — | Return with DOCKER1 |
| Windows Event Forwarding | In progress | 2026-11-02 | Collector on DC1 starts automatically again; end-to-end check waits on the source servers |
| `Lab/` rebuild system | Running | 2026-11-07 | Code, not a VM; drift between its config and the live CA names was found and noted for the next full rebuild |
| Edge firewall (pfSense CE on a used appliance) | In progress | 2026-10-29 | Bench test passed; cutover is a separate planned change |
| Managed switch (Catalyst 3560-C) | In progress | 2026-10-27 | Baselined and hardened; joins the network at the edge cutover |
| Wireless (UniFi U6 Pro) | Running | 2026-10-28 | Carries the household Wi-Fi; moves behind the new edge at cutover |
| Windows 11 test client | Planned | 2026-11-09 | Approved; disposable domain-joined client for Group Policy and endpoint work |
| Wazuh SIEM | Deferred | — | Host lacks the RAM headroom for the indexer |

## Current focus

- **Finishing the restart sequence:** file server next, then the sync server, the event-forwarding
  check, the Linux host and its containers, then a full service sweep and fresh encrypted backups.
- **Linux administration on the Linux host** once it is back: services, storage, patching,
  containers, single sign-on with MFA in front of the existing apps, and tested backups.

## Recent changes

- **2026-11-18** Firewall web-admin certificate replaced after its private key was found in a
  web-published folder: the new key was generated on the firewall so only the signing request
  left it, the new certificate was verified end to end over HTTP, and the old one was revoked for
  key compromise and its leftover files deleted.
- **2026-11-18** Issuing CA now publishes its revocation lists and its own certificate over HTTP
  through a stable DNS alias on DC1's web server, so non-domain clients can check revocation. The
  CA writes into a share only it can write to; new certificates carry both the HTTP and the LDAP
  locations.
- **2026-11-07** Issuing CA back online: service and CRL healthy, chain validates. Found its CRL
  publishes to LDAP only; an HTTP distribution point is being added.
- **2026-11-07** Every VM showed a critical state at start. Worked it from the logs to an
  unplanned host sleep; it cleared on its own, no checkpoints touched, and host sleep is now off.
- **2026-11-02** DC1 back after the outage: time-sync chain documented, expired evaluation
  license extended, `dcdiag` clean, event collector set to start automatically.
- **2026-11-02** Host clean-up: an unused SSH server stopped, wake-on-pattern turned off, stale
  backups removed; the PowerShell profile now loads straight from the repo.
- **2026-11-01** FW1 verified after the outage: interfaces and ruleset checked against the design.
- **2026-10-30** Recovery resumed: host pre-flight finished (script execution policy, automatic
  checkpoints confirmed off on all seven VMs).
- **2026-10-29** Benched a used firewall appliance on pfSense CE against a pass/fail bar set in
  advance: full line rate at about 30% CPU. Two-router design chosen: the new edge does the house
  NAT, and FW1 stays the lab router behind it with static routes, so a lab outage never takes the
  house down.
- **2026-10-28** Household Wi-Fi moved to a UniFi U6 Pro on a gigabit PoE+ injector; the ISP
  gateway's Wi-Fi is off.

## Next up

- Build the Windows 11 test client: its own OU so only test policies reach it, and a checkpoint
  after the domain join as the reset button.
- Edge cutover: ISP gateway to bridge mode, the benched appliance as the house edge, the switch
  and access point behind it, and queue management for the latency under load the Wi-Fi tests
  measured. Rollback is turning bridge mode off.
- Take the Hyper-V host out of the domain it hosts, removing a circular dependency.

---

All hostnames, domains and addresses in this repository are placeholders (`example.com` and
RFC 5737 documentation ranges). No real names, keys or credentials appear here. This is a home
lab, not a production environment.

Back to the [lab overview](README.md) · [write-ups](README.md#write-ups)
