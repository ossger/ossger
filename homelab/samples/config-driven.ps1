# Applies declared state from a data structure (in the lab this lives in a .psd1 file) instead of hardcoding it.
# Each declared setting goes through one Ensure-style function; adding a setting means adding a data row.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Declared = @{
    Policies = @(
        @{ Name = 'Security Baseline'
           Links = @('Corp/Computers')
           Settings = @(
               @{ Key = 'HKLM\Software\Policies\Example\LanmanServer'; ValueName = 'SMB1'; Type = 'DWord'; Value = 0 }
               @{ Key = 'HKLM\System\CurrentControlSet\Services\LanmanServer\Parameters'
                  ValueName = 'RequireSecuritySignature'; Type = 'DWord'; Value = 1 }
           ) }
        @{ Name = 'User Experience'
           Links = @('Corp/Users')
           Settings = @(
               @{ Key = 'HKCU\Software\Policies\Example\Explorer'; ValueName = 'ShowRunAs'; Type = 'DWord'; Value = 1 }
           ) }
    )
}

function Invoke-DeclaredState {
    param([Parameter(Mandatory)][hashtable]$State,
          [Parameter(Mandatory)][scriptblock]$EnsureSetting)   # injected so the loop is testable

    foreach ($policy in $State.Policies) {
        foreach ($s in $policy.Settings) {
            & $EnsureSetting -PolicyName $policy.Name -Setting $s
        }
    }
}

# Dry run: print what would be ensured, change nothing.
Invoke-DeclaredState -State $Declared -EnsureSetting {
    param($PolicyName, $Setting)
    '{0,-18} {1}\{2} = {3}' -f $PolicyName, $Setting.Key.Split('\')[-1], $Setting.ValueName, $Setting.Value
}
