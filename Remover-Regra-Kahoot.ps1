# Run in PowerShell as Administrator to remove the Kahoot-specific firewall rule.
Get-NetFirewallRule -DisplayName 'Kahoot ENEM - Rede local - TCP 5055' `
    -ErrorAction SilentlyContinue | Remove-NetFirewallRule
Write-Host "Regra de firewall do Kahoot removida."
