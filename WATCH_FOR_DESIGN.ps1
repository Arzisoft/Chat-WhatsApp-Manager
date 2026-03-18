# Watch for React/NextJS design completion
# Monitors the ui-redesign folder and notifies when it arrives

param(
    [int]$CheckIntervalSeconds = 30,
    [switch]$AutoStart = $false
)

function Write-Status {
    param([string]$Message, [string]$Type = "info")
    
    $colors = @{
        "info"    = "Cyan"
        "success" = "Green"
        "warning" = "Yellow"
        "error"   = "Red"
    }
    
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor $colors[$Type]
}

Write-Status "Watching for React/NextJS design completion..." "info"
Write-Status "Checking every $CheckIntervalSeconds seconds" "info"
Write-Status "Press Ctrl+C to stop" "warning"

$designPath = (Get-Location).Path + "\ui-redesign"
$lastStatus = "not_found"

while ($true) {
    $now = Get-Date
    
    if (Test-Path $designPath) {
        $files = @(Get-ChildItem -Path $designPath -Recurse -File -ErrorAction SilentlyContinue)
        $fileCount = $files.Count
        
        if ($fileCount -gt 0 -and $lastStatus -ne "found") {
            Write-Status "✨ DESIGN FOUND! UI redesign is ready!" "success"
            Write-Status "Files detected: $fileCount" "success"
            Write-Status "Ready to run: .\RUN_SYSTEM.ps1" "success"
            
            # Play system notification
            [System.Media.SystemSounds]::Exclamation.Play()
            
            if ($AutoStart) {
                Write-Status "Auto-starting system in 5 seconds..." "info"
                Start-Sleep -Seconds 5
                .\RUN_SYSTEM.ps1
                exit
            }
            
            $lastStatus = "found"
        }
        elseif ($fileCount -eq 0 -and $lastStatus -eq "not_found") {
            Write-Status "Design folder exists but still building..." "warning"
            $lastStatus = "building"
        }
        elseif ($fileCount -gt 0 -and $lastStatus -eq "found") {
            Write-Status "Design still ready. Files: $fileCount" "success"
        }
        else {
            Write-Status "Design building... Files: $fileCount" "warning"
        }
    }
    else {
        if ($lastStatus -ne "not_found") {
            Write-Status "Design folder not found yet. Still waiting..." "warning"
            $lastStatus = "not_found"
        }
    }
    
    Start-Sleep -Seconds $CheckIntervalSeconds
}
