# Monitoring and logging

Three sources feed visibility: availability checks, metrics, and logs. Windows security events
take a separate path through Windows Event Forwarding.

## Availability and metrics

All of this runs as one Docker Compose project on DOCKER1, with `restart: unless-stopped`.

| Component | Job |
|---|---|
| Uptime Kuma | 12 monitors: ICMP to every VM and the firewall, TCP checks for DNS, LDAPS and SMB, HTTP/HTTPS checks for the web services |
| Prometheus | Scrapes every 15 seconds, 30-day retention |
| Node Exporter | Host CPU, memory, disk and network, read from read-only bind mounts of `/proc`, `/sys` and `/` |
| Grafana | Dashboards (the community Node Exporter dashboard) and Explore for both Prometheus and Loki |

The Uptime Kuma checks cross the firewall, so they also act as a regression test for the
segmentation rules: tightening a rule that breaks a monitor shows up as a red check.

## Logs with Loki

Promtail discovers containers through the Docker socket, tails their log files and labels each
stream with container, Compose project and service. Loki indexes labels only and stores
compressed chunks, which is far lighter than a full-text index on a 4 GB VM.

- Loki and Promtail are pinned to the same version, since mismatches cause protocol errors.
- Storage uses the current TSDB schema. Retention is 14 days (logs are bulkier than
  metrics), enforced by the compactor, which has to be explicitly enabled.
- Queries are LogQL, for example errors across one Compose project or a parsed-JSON level
  filter on one container.
- **pfSense syslog:** Promtail also runs a syslog receiver, and the firewall forwards its logs
  to it over UDP. Streams are labelled by job, host and app, so firewall filter events and
  DHCP events can be queried separately. Generating a deliberate cross-VLAN request produces
  a visible block entry, which proves the whole path from rule to dashboard.

## Windows Event Forwarding

DC1 is the Windows Event Collector. The DC and the three other domain-joined servers (file
server, issuing CA, sync server) are sources. The offline root CA is a workgroup machine and
is not a source.

| Subscription | Sources | Covers |
|---|---|---|
| Authentication | All | Logon, logoff, explicit-credential logon, special privileges, Kerberos and NTLM validation |
| Account management | DC only | Account create/enable/disable/delete, group membership changes, audit and domain policy changes |
| System | All | New services, service crashes, shutdowns, event-log start/stop |
| PowerShell | All | Pipeline output and script block logging |

- Subscriptions are collector-initiated over WinRM with Kerberos. The collector authenticates
  as its machine account, so that account has to be in each source's local Event Log Readers
  group.
- Sources batch events (at most 15 minutes, or 20 events) and send an hourly heartbeat.
- Audit policy is set per subcategory with `auditpol`, and PowerShell script block logging is
  enabled by policy registry key.
- Account-management events are collected from the DC only because that is where the change
  is processed in a single-DC domain.
- Triage is done by querying the `ForwardedEvents` log, for example filtering to event ID 4625
  for failed logons, or by machine name.

## Troubleshooting approach

When a subscription shows inactive: check per-source status with `wecutil gr`, confirm WinRM
with `Test-WSMan`, confirm the collector account's group membership, then confirm the
collector service is running. When nothing arrives, wait out the batch window, or toggle the
subscription to force delivery.

A Wazuh SIEM (agents on the Linux host and DC) was planned and deferred because the host RAM
could not support the indexer.

**Skills demonstrated:** Prometheus and Grafana, Uptime Kuma, Loki/LogQL, syslog ingestion,
Windows event IDs and audit policy, WEF/WEC configuration, retention planning, using
monitoring to validate firewall changes.
