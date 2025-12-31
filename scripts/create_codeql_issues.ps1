param(
    [string]$prNumber = '20',
    [string]$repo = 'skakumanu/mew-assistant',
    [string]$headRef = 'pr19/ready'
)

Write-Output "Fetching CodeQL alerts (severity=error) for $repo..."
$alerts = gh api repos/$repo/code-scanning/alerts?per_page=100 --jq '.[] | select(.rule.severity=="error")' 2>&1
if (-not $alerts) {
    Write-Output "No error-level alerts found or API call failed."
    exit 0
}

# Parse alerts by reading JSON array via ConvertFrom-Json
$alertsJson = gh api repos/$repo/code-scanning/alerts?per_page=100 | ConvertFrom-Json
$errorAlerts = $alertsJson | Where-Object { $_.rule.severity -eq 'error' }
if (-not $errorAlerts) { Write-Output "No error-level alerts."; exit 0 }

foreach ($alert in $errorAlerts) {
    $ruleId = $alert.rule.id
    $htmlUrl = $alert.html_url
    $tool = $alert.tool.name
    $state = $alert.state
    $instance = $alert.mostRecentInstance
    $filePath = $null
    $start = $null
    $end = $null
    $snippet = ''

    if ($instance -ne $null -and $instance.location -ne $null) {
        $filePath = $instance.location.path
        $start = $instance.location.start_line
        $end = $instance.location.end_line
    }

    if ($filePath) {
        Write-Output "Fetching file content for $filePath at ref $headRef"
        try {
            $contentResp = gh api repos/$repo/contents/$($filePath) -f ref=$headRef | ConvertFrom-Json
            if ($contentResp.content) {
                $decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String(($contentResp.content -replace "\n","")))
                $lines = $decoded -split "\r?\n"
                $s = [int]($start - 3); if ($s -lt 0) { $s = 0 }
                $e = [int]($end + 2); if ($e -ge $lines.Length) { $e = $lines.Length - 1 }
                $snippet = ($lines[$s..$e] -join "`n")
            }
        } catch {
            $err = $_.Exception.Message
            Write-Output ("Failed to fetch content for {0}: {1}" -f $filePath, $err)
        }
    }

    $issueTitle = "CodeQL: $ruleId in $($filePath -or 'unknown')"
    $issueBody = "CodeQL alert: $ruleId`nTool: $tool`nState: $state`nAlert: $htmlUrl`n`n"
    if ($filePath) {
        $issueBody += "File: $filePath (lines $start-$end)\n\n" + '```python' + "`n" + $snippet + "`n```\n\n"
    }
    $issueBody += "Suggested action: investigate the alert, fix the root cause (e.g. sanitize inputs, avoid logging untrusted data, add defensive checks), and push a fix to this PR branch or a follow-up branch. Once patched, re-run CodeQL checks."

    Write-Output "Creating issue for $ruleId in $filePath"
    $tmp = [System.IO.Path]::GetTempFileName()
    Set-Content -Path $tmp -Value $issueBody -Encoding UTF8
    gh issue create --repo $repo --title "$issueTitle" --body-file $tmp --label "security" --label "codeql"
    Remove-Item $tmp -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

Write-Output "Done creating issues for error-level CodeQL alerts."