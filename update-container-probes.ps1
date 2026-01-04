# Load the current config
$config = Get-Content c:\Users\skaku\Projects\mew-assistant\ca-config.json | ConvertFrom-Json

# IMPORTANT: Do NOT modify DATABASE_URL - it's already configured correctly in Azure
# The script only adds health probes

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
Write-Host "  - Liveness probe added (30s delay, 10s period)"
Write-Host "  - Readiness probe added (10s delay, 5s period)"
Write-Host "  - DATABASE_URL preserved from existing configuration"
Write-Host ""
Write-Host "Saved to: ca-config-updated.json"
