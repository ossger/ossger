# Lab status

Last updated: 2026-11-09

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
| Two-tier PKI | In progress | 2026-11-07 | CA-ISSUING back, CRL fresh, chain validates, LDAPS listening; CA-ROOT stays offline by design; HTTP CRL point being added |
| Hybrid identity (SYNC1) | Planned | — | Restart and sync check queued |
| FW1 (pfSense) | Running | 2026-11-01 | Interfaces and ruleset verified against the design; a web-admin access fix is queued |
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

- **PKI: an HTTP CRL distribution point for the issuing CA.** It publishes revocation data to AD
  (LDAP) only, so non-domain clients (Linux, phones, browsers off the domain) can't check it. The
  change adds an HTTP location on DC1's web server, plus HTTP for the CA's own certificate (AIA).
- **Reissuing the firewall's web-admin certificate** from the issuing CA, with the key generated on
  the firewall so only the signing request leaves it. Waits on the HTTP change so the new
  certificate carries it.
- **Finishing the restart sequence:** file server, sync server, event-forwarding check, the Linux
  host and its containers, then a full service sweep and fresh encrypted backups.

## Recent changes

- **2026-11-07** Issuing CA back online: service and CRL healthy, chain validates. Found its CRL
  publishes to LDAP only, and two health checks that report green on the wrong data (fixes queued).
- **2026-11-07** Every VM showed a critical state at start. Worked it from the logs to an
  unplanned host sleep; it cleared on its own, no checkpoints touched, and host sleep is now off.
- **2026-11-02** DC1 back after the outage: time-sync chain documented, expired evaluation
  license extended, `dcdiag` clean, event collector set to start automatically.
- **2026-11-02** Host clean-up: an unused SSH server stopped, wake-on-pattern turned off, stale
  backups removed; the PowerShell profile now loads straight from the repo.
- **2026-11-01** FW1 verified after the outage: interfaces and ruleset checked against the design;
  a web-GUI access fix is queued as its own change.
- **2026-10-30** Recovery resumed: host pre-flight finished (script execution policy, automatic
  checkpoints confirmed off on all seven VMs).
- **2026-10-29** Benched a used firewall appliance on pfSense CE against a pass/fail bar set in
  advance: full line rate at about 30% CPU. Two-router design chosen: the new edge does the house
  NAT, and FW1 stays the lab router behind it with static routes, so a lab outage never takes the
  house down.
- **2026-10-28** Household Wi-Fi moved to a UniFi U6 Pro on a gigabit PoE+ injector; the ISP
  gateway's Wi-Fi is off.
- **2026-10-27** Catalyst 3560-C baselined over the serial console: Smart Install off, web admin
  off, SSH v2 only, local logins; the saved startup-config checked, not just the running one.
- **2026-10-22** Mesh VPN: traced a blocked admin path to a device carrying the wrong access tag
  (two devices shared one tag, so no rule connected them). Retagged it, verified SSH and RDP, and
  wrote the tag-based access policy down.

## Next up

- Restrict FW1's web GUI to admin sources, with every other source blocked and logged.
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
