# Runs read-only checks, prints a pass/fail table, and exits non-zero if any check failed.
# Checks return objects, so the same results can drive the table, a log file, or a scheduled run.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-Check {
    param([string]$Resource, [scriptblock]$Test, [string]$Expect)
    try {
        $actual = & $Test
        $status = if ("$actual" -eq "$Expect") { 'Pass' } else { 'FAIL' }
    } catch {
        $actual = $_.Exception.Message
        $status = 'FAIL'
    }
    [pscustomobject]@{ Status = $status; Resource = $Resource; Expected = $Expect; Actual = $actual }
}

$checks = @(
    New-Check 'DNS.Resolves'   { [bool](Resolve-DnsName 'dc1.corp.example.com' -ErrorAction Stop) } 'True'
    New-Check 'LDAPS.Port'     { (Test-NetConnection 'dc1.corp.example.com' -Port 636 -WarningAction SilentlyContinue).TcpTestSucceeded } 'True'
    New-Check 'CertSvc.State'  { (Get-Service -Name CertSvc).Status } 'Running'
    New-Check 'Firewall.Domain' { (Get-NetFirewallProfile -Name Domain).Enabled } 'True'
)

$checks | Format-Table Status, Resource, Expected, Actual -AutoSize

$failed = @($checks | Where-Object Status -eq 'FAIL')
Write-Host ("{0} of {1} checks passed." -f ($checks.Count - $failed.Count), $checks.Count)
exit ($failed.Count -gt 0 ? 1 : 0)
