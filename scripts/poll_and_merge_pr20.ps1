$merged = $false
for ($i = 1; $i -le 5; $i++) {
    Write-Output ("--- poll {0} / 5 - {1} ---" -f $i, (Get-Date))
    $out = gh pr checks 20 2>&1
    Write-Output $out
    if ($out -notmatch 'Some checks were not successful') {
        Write-Output 'All checks passed — attempting merge'
        gh pr merge 20 --squash --delete-branch
        $merged = $true
        break
    }
    if ($i -lt 5) { Start-Sleep -Seconds 120 }
}
if (-not $merged) { Write-Output 'Checks did not all pass within polling window' }
