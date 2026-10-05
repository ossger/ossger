# Orders build phases so every phase runs after the phases it depends on (depth-first topological sort).
# Throws on a missing dependency or a cycle, and prints the path that formed the cycle.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PhaseOrder {
    param([Parameter(Mandatory)][object[]]$Phases)

    $byName  = @{}
    foreach ($p in $Phases) { $byName[$p.Name] = $p }

    $state   = @{}   # name -> 'visiting' | 'done'
    $ordered = [System.Collections.Generic.List[object]]::new()

    $visit = {
        param($Node, [string[]]$Stack)
        if ($state[$Node.Name] -eq 'done') { return }
        if ($state[$Node.Name] -eq 'visiting') {
            throw "Dependency cycle at '$($Node.Name)': $(($Stack + $Node.Name) -join ' -> ')"
        }
        $state[$Node.Name] = 'visiting'
        foreach ($dep in $Node.Dependencies) {
            if (-not $byName.ContainsKey($dep)) {
                throw "Phase '$($Node.Name)' depends on unknown phase '$dep'."
            }
            & $visit $byName[$dep] ($Stack + $Node.Name)
        }
        $state[$Node.Name] = 'done'
        $ordered.Add($Node)
    }

    foreach ($p in $Phases) { & $visit $p @() }
    return $ordered
}

# Example: phases are declared out of order on purpose.
$phases = @(
    [pscustomobject]@{ Name = '12-monitoring'; Dependencies = @('11-docker-host') }
    [pscustomobject]@{ Name = '03-ad-forest';  Dependencies = @('02-vms') }
    [pscustomobject]@{ Name = '11-docker-host'; Dependencies = @('02-vms') }
    [pscustomobject]@{ Name = '02-vms';        Dependencies = @('01-switches') }
    [pscustomobject]@{ Name = '01-switches';   Dependencies = @() }
)

(Get-PhaseOrder -Phases $phases).Name -join ' -> '
# 01-switches -> 02-vms -> 11-docker-host -> 12-monitoring -> 03-ad-forest
