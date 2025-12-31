for ($i=1; $i -le 5; $i++) {
    Write-Output ("--- poll {0} / 5 - {1} ---" -f $i, (Get-Date))
    gh pr checks 20
    if ($i -lt 5) { Start-Sleep -Seconds 120 }
}
