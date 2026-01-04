# Load the current config
$config = Get-Content c:\Users\skaku\Projects\mew-assistant\ca-config.json | ConvertFrom-Json

# Update DATABASE_URL to PostgreSQL
$dbUrlIndex = $config.properties.template.containers[0].env | ForEach-Object -Begin { $i=0 } { if ($_.name -eq "DATABASE_URL") { $i } else { $i++ } }
$config.properties.template.containers[0].env[$dbUrlIndex].value = "postgresql://mewadmin:mew_password_2026_secure@mew-assistant-db.postgres.database.azure.com:5432/mew_assistant"

# Add probes to the container
$config.properties.template.containers[0] | Add-Member -NotePropertyName "probes" -NotePropertyValue @(
    @{
        type = "liveness"
        httpGet = @{
            path = "/health"
            port = 8000
            scheme = "HTTP"
        }
        initialDelaySeconds = 30
        periodSeconds = 10
        timeoutSeconds = 5
        failureThreshold = 3
        successThreshold = 1
    },
    @{
        type = "readiness"
        httpGet = @{
            path = "/health"
            port = 8000
            scheme = "HTTP"
        }
        initialDelaySeconds = 10
        periodSeconds = 5
        timeoutSeconds = 3
        failureThreshold = 2
        successThreshold = 1
    }
) -Force

# Save to file
$config | ConvertTo-Json -Depth 100 | Set-Content c:\Users\skaku\Projects\mew-assistant\ca-config-updated.json

Write-Host "✅ Configuration updated:"
Write-Host "  - DATABASE_URL changed to PostgreSQL"
Write-Host "  - Liveness probe added (30s delay, 10s period)"
Write-Host "  - Readiness probe added (10s delay, 5s period)"
Write-Host ""
Write-Host "Saved to: ca-config-updated.json"
