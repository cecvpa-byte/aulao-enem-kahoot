# Run in PowerShell as Administrator. Allows only classroom-subnet traffic to TCP 5055.
$ruleName = 'Kahoot ENEM - Rede local - TCP 5055'
$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if (-not $existing) {
    New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow `
        -Protocol TCP -LocalPort 5055 -RemoteAddress LocalSubnet -Profile Any `
        -EdgeTraversalPolicy Block | Out-Null
}
Write-Host "Regra local criada/confirmada: TCP 5055, origem limitada à sub-rede local."
