param(
    [switch]$Reset,
    [ValidateRange(1, 65535)]
    [int]$Port = 8010,
    [string]$LanAddress = ""
)

$ErrorActionPreference = "Stop"
if ($LanAddress) {
    $lanIp = [System.Net.IPAddress]::Parse($LanAddress)
    if ($lanIp.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork -or
        -not (Get-NetIPAddress -AddressFamily IPv4 | Where-Object IPAddress -eq $LanAddress)) {
        throw "LanAddress must be an IPv4 address assigned to this computer."
    }
}
$workspaceRoot = $PSScriptRoot
$portalRoot = Join-Path $workspaceRoot "EducAgent-Portal"
$nirvanaRoot = Join-Path $workspaceRoot "EducAgent-Nirvana"
$portalOutput = Join-Path $workspaceRoot "portal"
$nirvanaOutput = Join-Path $workspaceRoot "nirvana"
$mediaOutput = Join-Path $workspaceRoot "media"
$siteOutput = Join-Path $workspaceRoot ".demo-site"
$nirvanaPort = 8011

Push-Location $portalRoot
try {
    & npm run web:build
    if ($LASTEXITCODE -ne 0) {
        throw "Portal web build failed."
    }
}
finally {
    Pop-Location
}

New-Item -ItemType Directory -Force $portalOutput, $nirvanaOutput, $mediaOutput | Out-Null
Copy-Item -Path (Join-Path $portalRoot "web\dist\*") -Destination $portalOutput -Recurse -Force
Copy-Item -Path (Join-Path $nirvanaRoot "demo\*") -Destination $nirvanaOutput -Recurse -Force
Copy-Item -Path (Join-Path $portalRoot "web\dist\media\*") -Destination $mediaOutput -Recurse -Force

# Rebuild only the dedicated public output so withdrawn assets cannot linger.
$expectedSite = [System.IO.Path]::GetFullPath((Join-Path $workspaceRoot ".demo-site"))
if ([System.IO.Path]::GetFullPath($siteOutput) -ne $expectedSite -or
    (Split-Path -Parent $expectedSite) -ne [System.IO.Path]::GetFullPath($workspaceRoot)) {
    throw "Refusing to replace an output outside the dedicated .demo-site directory."
}
if (Test-Path -LiteralPath $siteOutput) {
    $siteItem = Get-Item -LiteralPath $siteOutput -Force
    if ($siteItem.FullName -ne $expectedSite -or
        ($siteItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        throw "Refusing to replace a public output containing a filesystem link."
    }
    if (Get-ChildItem -LiteralPath $siteOutput -Recurse -Force |
        Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReparsePoint }) {
        throw "Refusing to replace a public output containing a filesystem link."
    }
    Remove-Item -LiteralPath $expectedSite -Recurse -Force
}
New-Item -ItemType Directory -Force $siteOutput | Out-Null
Copy-Item -LiteralPath (Join-Path $workspaceRoot "index.html"), (Join-Path $workspaceRoot "styles.css") -Destination $siteOutput -Force
Copy-Item -LiteralPath (Join-Path $portalRoot "web\dist\sources.html") -Destination $siteOutput -Force
Copy-Item -LiteralPath (Join-Path $portalRoot "web\dist") -Destination (Join-Path $siteOutput "portal") -Recurse -Force
Copy-Item -LiteralPath (Join-Path $nirvanaRoot "demo") -Destination (Join-Path $siteOutput "nirvana") -Recurse -Force
Copy-Item -LiteralPath (Join-Path $portalRoot "web\dist\media") -Destination (Join-Path $siteOutput "media") -Recurse -Force

$env:PYTHONPATH = Join-Path $portalRoot "src"
$demoArguments = @(
    "run",
    "-n",
    "educagent-sdk",
    "python",
    (Join-Path $portalRoot "examples\playable_demo.py"),
    "--port",
    $Port,
    "--static-root",
    $siteOutput,
    "--unguarded-tutor"
)
if ($Reset) {
    $demoArguments += "--reset"
}
if ($LanAddress) { $demoArguments += "--lan" }

$pythonPath = (& conda run -n educagent-sdk python -c "import sys; print(sys.executable)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $pythonPath) {
    throw "Could not locate Python in the educagent-sdk Conda environment."
}
$nirvanaArguments = @(
    (Join-Path $nirvanaRoot "demo_server.py"),
    "--port",
    $nirvanaPort,
    "--origin-port",
    $Port,
    "--env-file",
    (Join-Path $portalRoot ".env")
)
if ($LanAddress) { $nirvanaArguments += @("--lan-address", $LanAddress) }
$nirvanaProcess = Start-Process -FilePath $pythonPath -ArgumentList $nirvanaArguments -WindowStyle Hidden -PassThru
if ($LanAddress) {
    Write-Host "LAN demo: http://${LanAddress}:$Port/ (Portal progress follows each browser session)"
}

Write-Host "Learning resources: http://127.0.0.1:$Port/"
Write-Host "Portal:             http://127.0.0.1:$Port/portal/ (guided free-text mode)"
Write-Host "Nirvana:            http://127.0.0.1:$Port/nirvana/ (LLM API on $nirvanaPort)"
try {
    & conda @demoArguments
    exit $LASTEXITCODE
}
finally {
    if (-not $nirvanaProcess.HasExited) {
        Stop-Process -Id $nirvanaProcess.Id
    }
}
