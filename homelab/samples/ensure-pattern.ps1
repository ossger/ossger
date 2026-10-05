# Idempotent "Ensure" function: checks current state, changes only if needed, and reports what it did.
# Returns Created / Updated / Unchanged / Failed so a re-run on a healthy system changes nothing.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function New-Result {
    param([ValidateSet('Created','Updated','Unchanged','Failed')][string]$Status,
          [string]$Resource, [string]$Detail = '')
    [pscustomobject]@{ Status = $Status; Resource = $Resource; Detail = $Detail }
}

function Ensure-RegistryValue {
    [CmdletBinding(SupportsShouldProcess)]
    param(
        [Parameter(Mandatory)][string]$Path,        # e.g. 'HKLM:\SOFTWARE\Policies\Example'
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)]$Value,
        [ValidateSet('String','DWord','QWord')][string]$Type = 'DWord'
    )
    $resource = "Registry.$Path\$Name"
    try {
        if (-not (Test-Path $Path) -and $PSCmdlet.ShouldProcess($Path, 'Create key')) {
            New-Item -Path $Path -Force | Out-Null
        }

        $current = (Get-ItemProperty -Path $Path -Name $Name -ErrorAction SilentlyContinue).$Name
        if ($null -ne $current -and $current -eq $Value) {
            return New-Result Unchanged $resource "already $Value"
        }

        if (-not $PSCmdlet.ShouldProcess("$Path\$Name", "Set to $Value")) {
            return New-Result Unchanged $resource "-WhatIf: would set $current -> $Value"
        }
        Set-ItemProperty -Path $Path -Name $Name -Value $Value -Type $Type
        if ($null -eq $current) { return New-Result Created $resource "set to $Value" }
        return New-Result Updated $resource "$current -> $Value"
    }
    catch {
        return New-Result Failed $resource $_.Exception.Message
    }
}

# Run twice: the first pass reports Created/Updated, the second reports Unchanged.
# Ensure-RegistryValue -Path 'HKLM:\SOFTWARE\Policies\Example' -Name 'EnableFeature' -Value 1 -WhatIf
