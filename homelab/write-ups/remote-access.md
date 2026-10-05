# Remote access: mesh VPN, SSH certificates, reverse proxy

## Mesh VPN as a subnet router

The Hyper-V host runs a WireGuard-based mesh VPN client and advertises both lab VLANs. Any
enrolled device (phone, laptop) reaches the domain controller, file server, CAs and the Linux
host without a VPN client on any VM, and without port forwarding or dynamic DNS. The firewall
has no inbound NAT rules.

Things that had to be done beyond installing it:

- Advertised routes also have to be **approved** in the admin console, or nothing works.
- Key expiry is disabled on the subnet-router host so remote access does not silently lapse.
- The VPN adapter can be classified as a Public network profile by Windows Firewall, which
  blocks WinRM, SMB and RDP. Setting the profile to Private fixed it.
- MagicDNS can interfere with internal name resolution. Split DNS forwards the internal zone to
  the domain controller.
- Windows Admin Center runs in desktop mode on the host (not on a DC, where its web server
  conflicts with DC roles) and is reached over the VPN. Servers are added by FQDN.
- **ACL policy** gates specific ports between peers. A blocked port looks identical to a local
  firewall drop (silent timeout, ping still works). This is written up in
  [troubleshooting-highlights](troubleshooting-highlights.md).

## SSH certificate authority

SSH access to the Linux host uses short-lived certificates in place of per-host
`authorized_keys` files.

| Piece | Detail |
|---|---|
| CA keypair | Ordinary ed25519 key from `ssh-keygen`, private half kept on the issuing-CA host. SSH certificates are not X.509, so this is unrelated to ADCS |
| User certificate | Signed for 52 weeks with a named principal; renewal is a wrapper function |
| Host certificate | The Linux host's key is signed too, and clients trust the CA for the lab domain in `known_hosts`, so there are no first-connection prompts |
| Server config | `TrustedUserCAKeys` trusts the CA; `AuthorizedPrincipalsFile` (one file per local user) is the per-user ACL |
| Revocation | Key revocation list on the server, or let the certificate expire |

Trust in the CA alone is too broad, since any certificate it signed could log in as any user.
The principals file is the second check, and both must pass. At one host this is more
machinery than needed, but adding a server is one trust line and adding a user is one signing
operation, which is why enterprises use it. A separate certificate gives automation its own
identity.

## Traefik reverse proxy

Traefik v3.6 sits in front of every web container on DOCKER1 and gives them friendly
`*.lab.example.com` names over HTTPS.

- **Routing is label-driven.** Each container declares its hostname and port as Compose labels
  and Traefik discovers them through the Docker socket. `exposedByDefault` is false, so a
  container such as Node Exporter is never published by accident.
- **Two config layers.** Static config (entrypoints, providers, logging) needs a restart;
  dynamic config (certificates, middleware) hot-reloads.
- **TLS.** A wildcard certificate is issued by the internal issuing CA from the web server
  template and trusted by domain machines through autoenrollment, so there are no browser
  warnings on joined devices. HTTP redirects to HTTPS at the entrypoint.
- **One way in.** Backends no longer publish ports; everything enters on 80/443.
- **DNS.** Each hostname is an A record on the domain controller pointing at the proxy host.
- **Debugging.** With no published ports, `curl localhost` from the host fails by design, so
  checks run inside the container with `docker exec`. A plain-text 404 without backend
  headers is Traefik's own; a 404 with backend headers is the application's.
- Traefik v3.5 and earlier fail against Docker Engine 29 because of an API-version minimum,
  fixed by moving to 3.6.

**Skills demonstrated:** VPN and subnet routing, split DNS, SSH PKI and certificate-based
authentication, certificate issuance and renewal, reverse proxying, TLS termination,
principle of least privilege, container networking.
