# Troubleshooting highlights

The lab keeps a numbered log of mistakes (89 entries so far) so the same one is not paid for
twice. Six that show different kinds of diagnosis, each as symptom, cause, fix, lesson.

## 1. Firewall rules that did nothing

- **Symptom:** After a segmentation ruleset was in place, traffic between the Hyper-V host
  and the Linux VM was not covered by any of it.
- **Cause:** The host has an adapter in both VLANs. Windows prefers a directly connected route
  to a gateway route, so host-to-Linux packets stay on the switch and never reach pfSense.
  `Find-NetRoute` showed a next hop of `0.0.0.0`.
- **Fix:** Accept that pfSense cannot filter that path and use Windows Firewall on the host for
  it. When the host serves files to the Linux VM, use the host's address on the Linux VLAN.
- **Lesson:** Check the actual path a packet takes before concluding a rule is wrong.

## 2. A certificate template that would not issue

- **Symptom:** A hand-built ADCS certificate template was published but the CA refused
  requests with an unsupported-template error.
- **Cause:** Cloning a template by setting AD attributes in PowerShell missed interdependent
  attributes, including the template OID. The Certificate Templates console and its COM API set
  dozens of related values atomically.
- **Fix:** Create templates in the console, or duplicate them with a PKI-aware PowerShell
  module; after publishing, force the CA to re-read templates from AD.
- **Lesson:** Do not reimplement a GUI's side effects by writing directory attributes. Use the
  supported interface for anything with hidden coupling.

## 3. Containers resolving the wrong host

- **Symptom:** Inside the Docker network, a bare container name (`loki`) resolved to the wrong
  place instead of the container.
- **Cause:** The Linux host's search domain was inherited by containers. The bare name `loki`
  became `loki.<domain>`, which matched an A record on the domain controller, and that answer
  won over Docker's internal DNS.
- **Fix:** Set `dns_search: ["."]` (the DNS root) on every service. An empty list is silently
  ignored by Compose v2, and in a base-plus-override setup it has to be repeated on each
  service in the override.
- **Lesson:** Split-horizon surprises come from search-domain inheritance. When a name
  resolves to the wrong place, ask which resolver answered, not whether DNS is up.

## 4. Loki in a restart loop

- **Symptom:** After enabling retention, the Loki container restarted repeatedly.
- **Cause:** Loki 3.x rejects a config with retention enabled unless a delete request store is
  set. Separately, a retention period on its own does nothing; the compactor enforces it.
- **Fix:** Enable compactor retention, set the delete request store to the filesystem, and read
  `docker logs` for the `invalid compactor config` message instead of guessing.
- **Lesson:** Policy settings need an enforcement mechanism. Read the container's own error
  output first. Related: a bind-mounted config file that does not exist yet makes Docker create
  a directory with that name, so create files before first start.

## 5. sudo ignoring a valid rule after domain join

- **Symptom:** A domain user authenticated over SSH with a certificate, but a sudoers entry
  for that user never matched.
- **Cause:** The sudoers entry used the fully qualified name. sudo treats `@` as a netgroup
  reference, so the line silently never matched. A related trap: a `grep -q` guard meant to
  append an SSH principals directive matched the commented-out default line, so the real
  directive was never written.
- **Fix:** Turn off fully qualified names in SSSD, restart it, confirm `id <user>` resolves,
  then write the short-name sudoers entry. Replace the directive with `sed` so it works whether
  the line is commented or not.
- **Lesson:** Change one layer at a time and verify each, in dependency order. Idempotent
  edits should replace a line, not test for a substring.

## 6. A port that timed out while ping worked

- **Symptom:** SSH from one workstation to another over the mesh VPN timed out. Ping over the
  VPN succeeded.
- **Cause:** Two rounds of local firewall diagnosis found nothing, because the block was the
  mesh network's ACL policy, which gates specific ports between peers and is edited in the
  admin console, not on either machine.
- **Fix:** Correct the ACL policy.
- **Lesson:** An ACL block looks identical to a firewall drop from the client side. Bisect the
  layers (reachability, ACL, host firewall, service) in order before going deep on one.

**Skills demonstrated:** Layered diagnosis, reading logs before changing config, routing and
DNS resolution behaviour, ADCS, Docker Compose, SSSD and sudo, SSH configuration, writing down
root causes.
