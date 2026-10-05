# Identity: AD DS, two-tier PKI, hybrid identity

The Windows track is built the way a small enterprise would build it: one forest, an OU
structure designed for delegation and policy targeting, an internal certificate authority
hierarchy, and a sync link to Entra ID.

## Active Directory and Group Policy

- Forest and DNS on DC1 (`corp.example.com`), with an OU tree split by object type so Group
  Policy and delegation can target users, computers and workstations separately.
- Test users and security groups with realistic attributes (department, title), used to
  exercise policy and sync scope.
- **Windows LAPS.** The AD schema is extended, computer accounts get self-write permission on
  the managed OUs, and a GPO sets the policy. Each domain-joined machine gets a unique local
  administrator credential stored in AD, which limits lateral movement from one compromised
  box.
- **GPO baseline.** A domain-level password and lockout policy; a workstation security
  baseline linked at the workstation OU (SMBv1 off, SMB signing required on client and
  server, firewall profiles enforced); a relaxed variant for an owner-managed OU; and
  user drive mappings delivered through Group Policy Preferences.
- **File services.** FS1 hosts SMB shares fronted by a DFS namespace, so a share can move
  without users changing paths. Share permissions are open and all control is in NTFS, to
  avoid reasoning about two interacting ACL layers.
- **Linux in the domain.** The Ubuntu host is joined with realmd/SSSD, and domain admins get
  sudo. This surfaced several SSSD behaviours covered in
  [troubleshooting-highlights](troubleshooting-highlights.md).

## Two-tier PKI

| Tier | Host | Role |
|---|---|---|
| Root | CA-ROOT | Standalone, workgroup, powered off after signing the issuing CA |
| Issuing | CA-ISSUING | Enterprise subordinate CA, online, publishes templates to AD |

The root stays offline so that a compromise of an always-on server does not compromise the
trust anchor. Operational points:

- CRL and AIA locations are **HTTP**, served by IIS on DC1 under `/pki`. HTTPS would make
  certificate validation depend on a certificate that is itself being validated.
- Autoenrollment via GPO puts the root and issuing CA into the trust store of every
  domain-joined machine; LDAPS on the DC uses a template-issued certificate.
- A custom certificate template and an HTTPS binding on the DC were added after the base
  build, and a wildcard certificate for the Linux reverse proxy is issued from the built-in
  web server template.
- The root CRL has a finite life. If it expires, the issuing CA's service stops because it
  cannot validate its chain. Recovery is to bring the root online briefly, publish a new CRL,
  copy it to the IIS directory and restart the CA service. The renewal date is tracked as an
  operational task.
- Non-domain devices (phones, laptops) never receive the GPO, so the root certificate has to
  be installed on them by hand. See the Apple-device note in the troubleshooting log.

## Hybrid identity

- A domain-joined sync server (SYNC1) runs classic Entra Connect with password hash
  synchronization. PHS was chosen because cloud sign-in keeps working if the DC is down.
- The UPN suffix is the public domain (`example.com`) rather than the internal
  `corp.example.com`, so users sign in with a clean, routable name.
- Entra is on the free tier, so conditional access and password writeback were studied
  conceptually but not built.
- Sync health comes from the Synchronization Service Manager and `Get-ADSyncScheduler`,
  because the portal telemetry is licence-gated. Delta sync runs every 30 minutes; the
  ADSync module works only in Windows PowerShell 5.1, not PowerShell 7.
- Sign-in logs (basic info, device, authentication details, conditional access) were read to
  trace a sign-in end to end. Free-tier retention is 7 days.

**Skills demonstrated:** Active Directory design and administration, Group Policy, Windows
LAPS, DFS and NTFS permissions, ADCS and offline-root PKI, certificate templates and
autoenrollment, CRL/AIA publication, Entra Connect, Linux-to-AD integration.
