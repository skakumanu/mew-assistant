# Poll GitHub workflow run statuses for the given run IDs.
# Queries every 2 minutes, up to 30 attempts.
$runIds = @(20519973021,20519973013,20519993240,20519993249)
$max = 30
for ($i=1; $i -le $max; $i++) {
    $time = (Get-Date).ToString('o')
    Write-Output "=== Poll #$i ($time) ==="
    $allDone = $true
    foreach ($id in $runIds) {
        try {
            $rJson = gh run view $id --json status,conclusion,url 2>$null | ConvertFrom-Json
            if ($null -eq $rJson) {
                Write-Output "Run $id -> no data returned"
                $allDone = $false
                continue
            }
            $status = $rJson.status
            $conclusion = $rJson.conclusion
            $url = $rJson.url
            Write-Output "Run $id -> status=$status conclusion=$conclusion url=$url"
            if ($status -eq 'in_progress' -or $status -eq 'queued' -or $status -eq 'requested') { $allDone = $false }
        } catch {
            Write-Output "Run $id -> error querying: $_"
            $allDone = $false
        }
    }
    if ($allDone) { Write-Output 'All runs completed. Exiting poll.'; break }
    Start-Sleep -Seconds 120
}
Write-Output 'Poller finished.'
