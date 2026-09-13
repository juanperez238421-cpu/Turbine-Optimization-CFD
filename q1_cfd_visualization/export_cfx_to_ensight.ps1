param(
    [Parameter(Mandatory=$true)][string]$ResultsFile,
    [Parameter(Mandatory=$true)][string]$OutputBase,
    [string]$CfxBin = "C:\Program Files\ANSYS Inc\v241\CFX\bin",
    [int]$Timestep = -1
)

$ErrorActionPreference = "Stop"
$exe = Join-Path $CfxBin "cfx5export.exe"
if (-not (Test-Path $exe)) {
    throw "cfx5export.exe not found at $exe. Set -CfxBin to the installed ANSYS CFX bin directory."
}
if (-not (Test-Path $ResultsFile)) {
    throw "Results file not found: $ResultsFile"
}

$args = @("-ensight", "-geometry", "-verbose", "-name", $OutputBase)
if ($Timestep -ge 0) {
    $args += @("-timestep", "$Timestep")
}
$args += $ResultsFile

Write-Host "Running:" $exe ($args -join " ")
& $exe @args
if ($LASTEXITCODE -ne 0) {
    throw "cfx5export failed with exit code $LASTEXITCODE"
}

Write-Host "Export finished. Verify the generated EnSight case and variable files before rendering."
Write-Host "Recommended Carolina workflow:"
Write-Host "  1) export Parque I first;"
Write-Host "  2) export CFX-16 and CFX-28 as separate Logarithmic AI60 candidates;"
Write-Host "  3) do not rename either candidate as verified Log AI60 until mapping is resolved;"
Write-Host "  4) use identical final timestep and field selection across all compared cases."
