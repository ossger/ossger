# Network segmentation with pfSense

FW1 is a pfSense VM with three virtual NICs: WAN (DHCP from the home router), a LAN interface
for the Windows VLAN, and an OPT1 interface for the Linux VLAN. It replaced an earlier setup
where the Hyper-V host acted as an implicit gateway.

| Interface | Segment | Role |
|---|---|---|
| WAN | External switch | Uplink and NAT source. No inbound NAT rules. |
| LAN | VLAN 10 (`198.51.100.0/24`) | Gateway for Windows servers |
| OPT1 | VLAN 20 (`203.0.113.0/24`) | Gateway for the Linux/Docker host |

## Policy

Cross-VLAN traffic is allowed only where a service needs it:

- **Windows to Linux:** admin ports on the Docker host (SSH, HTTP/HTTPS, reverse-proxy
  dashboard) and ICMP.
- **Linux to Windows:** DNS and LDAPS to the DC, SMB to the file server, the firewall web UI
  and ICMP, all of which exist so the monitoring stack can check those services.
- **Everything else between the VLANs** hits an explicit, logged `Block` rule. I used `Block`
  rather than `Reject` so a scanner gets no feedback, as at a real zone boundary.
- **Internet egress** is allowed with an invert-match destination (`!` the other VLAN). The
  allow rule itself excludes the internal zone, so it cannot reopen a cross-VLAN path even if
  the block rule above it were deleted.

Rules use aliases with a naming prefix (`NET_`, `H_`, `P_` for networks, hosts and ports), so
the rule list reads as plain English and a subnet or host changes in one place. Rules live
only on the interface where traffic originates; pfSense's state table handles return traffic.

## Four-phase rollout

| Phase | What happened |
|---|---|
| 1. Audit | Watched real traffic through the state table, firewall log and the monitoring stack, and listed every `source -> destination:port` flow |
| 2. Design | Turned that list into aliases and a written rule table, reviewed before touching the firewall |
| 3. Build | Added the specific rules above the existing allow-all, which still caught anything the audit missed |
| 4. Cutover | Replaced the allow-all with the invert-match egress rule |

Writing rules against observed traffic, not assumed traffic, is meant to catch dependencies
such as the monitoring checks before cutover rather than after it.

## Rollback

If a tightened ruleset breaks something: on each interface, edit the egress rule, clear
"Invert match" on the destination, save and apply. The allow-all behaviour returns
immediately, the specific rules still match first, and debugging can happen afterwards. My
decision log calls for exporting the firewall configuration as XML after every ruleset
change and keeping the copy off the host.

## Findings along the way

- **Host-to-Docker traffic bypasses the firewall.** The Hyper-V host has an adapter in both
  VLANs, so its route to the Linux host is directly connected and never reaches pfSense.
  Confirmed with `Find-NetRoute` (next hop `0.0.0.0`). Filtering that path needs Windows
  Firewall on the host, not a pfSense rule.
- **Rule hit counters reset on every Apply** and only count new states, so a counter of 1 on
  a long-lived connection is normal. Verification means resetting counters and generating
  known test traffic.
- Setup details that cost time: the host's own adapters had to move off the `.1` addresses
  pfSense took, DHCP on the LAN interface had to be disabled to avoid a rogue DHCP server, the
  VM had to be Generation 1 for the legacy bootloader, and NIC-to-switch mapping had to be
  matched by MAC address because Hyper-V presents NICs in arbitrary order.
- Firewall events are exported by syslog to Loki, so blocked cross-VLAN attempts are
  queryable. See [monitoring-and-logging](monitoring-and-logging.md).

**Skills demonstrated:** VLAN design, stateful firewall policy, alias-based rule hygiene,
least-privilege inter-zone rules, staged change rollout with a tested rollback, traffic
analysis, routing behaviour on multi-homed hosts.
