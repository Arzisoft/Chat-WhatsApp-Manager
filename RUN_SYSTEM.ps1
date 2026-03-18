# ChatChaos WhatsApp Manager - Complete System Startup Script
# Starts bridge, API, and app servers in the correct order

param(
    [string]$Mode = "all",  # all | bridge | streamlit | react
    [switch]$Verbose
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

function Start-Bridge {
    Write-Status "Starting WhatsApp Bridge..." "info"
    
    $bridgePath = (Get-Location).Path + "\bridge"
    
    if (-not (Test-Path $bridgePath)) {
        Write-Status "Bridge folder not found at $bridgePath" "error"
        return $false
    }
    
    if (-not (Test-Path "$bridgePath\package.json")) {
        Write-Status "Installing bridge dependencies..." "info"
        Push-Location $bridgePath
        npm install
        Pop-Location
    }
    
    Write-Status "Launching bridge on port 3001..." "info"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd $bridgePath && npm start" -NoNewWindow
    
    Write-Status "Bridge starting (waiting for initialization)..." "warning"
    Start-Sleep -Seconds 3
    
    # Check if bridge is responsive
    $attempts = 0
    while ($attempts -lt 10) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:3001/status" -TimeoutSec 2 -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Status "Bridge is online!" "success"
                return $true
            }
        } catch {
            $attempts++
            if ($attempts -lt 10) {
                Write-Status "Waiting for bridge... (attempt $attempts/10)" "warning"
                Start-Sleep -Seconds 2
            }
        }
    }
    
    Write-Status "Bridge failed to start after 10 attempts" "error"
    return $false
}

function Start-Streamlit {
    Write-Status "Starting Streamlit Dashboard..." "info"
    
    $appPath = (Get-Location).Path
    
    Write-Status "Launching Streamlit on port 8501..." "info"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd $appPath && streamlit run app.py --logger.level=error" -NoNewWindow
    
    Write-Status "Streamlit starting..." "warning"
    Start-Sleep -Seconds 3
    
    Write-Status "Streamlit running at http://localhost:8501" "success"
    return $true
}

function Start-React {
    Write-Status "Starting React/NextJS UI..." "info"
    
    $reactPath = (Get-Location).Path + "\ui-redesign"
    
    if (-not (Test-Path $reactPath)) {
        Write-Status "React/NextJS folder not found at $reactPath" "error"
        Write-Status "Wait for design team to complete the build" "warning"
        return $false
    }
    
    if (-not (Test-Path "$reactPath\package.json")) {
        Write-Status "Installing React dependencies..." "info"
        Push-Location $reactPath
        npm install
        Pop-Location
    }
    
    Write-Status "Launching React dev server..." "info"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k cd $reactPath && npm start" -NoNewWindow
    
    Write-Status "React dev server starting..." "warning"
    Start-Sleep -Seconds 5
    
    Write-Status "React running at http://localhost:3000" "success"
    return $true
}

function Show-Menu {
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "╔════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   ChatChaos WhatsApp Manager - System Menu     ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host "`n"
    
    Write-Host "1. Start Bridge Only" -ForegroundColor Yellow
    Write-Host "2. Start Streamlit Only" -ForegroundColor Yellow
    Write-Host "3. Start React/NextJS Only" -ForegroundColor Yellow
    Write-Host "4. Start Bridge + Streamlit" -ForegroundColor Yellow
    Write-Host "5. Start Everything (when React ready)" -ForegroundColor Yellow
    Write-Host "6. System Health Check" -ForegroundColor Yellow
    Write-Host "7. Open Dashboard" -ForegroundColor Yellow
    Write-Host "8. Exit" -ForegroundColor Yellow
    Write-Host "`n"
}

function Check-SystemHealth {
    Write-Status "Checking system health..." "info"
    
    $health = @{}
    
    # Bridge
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3001/health" -TimeoutSec 2 -ErrorAction Stop
        $data = $response.Content | ConvertFrom-Json
        Write-Status "Bridge: Online (status: $($data.status))" "success"
        $health["bridge"] = $true
    } catch {
        Write-Status "Bridge: Offline" "error"
        $health["bridge"] = $false
    }
    
    # Streamlit
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 2 -ErrorAction Stop
        Write-Status "Streamlit: Online" "success"
        $health["streamlit"] = $true
    } catch {
        Write-Status "Streamlit: Offline" "warning"
        $health["streamlit"] = $false
    }
    
    # React
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 2 -ErrorAction Stop
        Write-Status "React: Online" "success"
        $health["react"] = $true
    } catch {
        Write-Status "React: Offline" "warning"
        $health["react"] = $false
    }
    
    return $health
}

function Open-Dashboard {
    $health = Check-SystemHealth
    
    if ($health["react"]) {
        Write-Status "Opening React UI..." "info"
        Start-Process "http://localhost:3000"
    } elseif ($health["streamlit"]) {
        Write-Status "Opening Streamlit Dashboard..." "info"
        Start-Process "http://localhost:8501"
    } else {
        Write-Status "No dashboard available. Start a service first." "error"
    }
}

# Main startup logic
if ($Mode -eq "all") {
    Write-Status "Starting complete ChatChaos system..." "info"
    Write-Status "Available modes: all | bridge | streamlit | react" "info"
    
    if (Start-Bridge) {
        if (Start-Streamlit) {
            Write-Status "Core system online!" "success"
            
            if (Test-Path ((Get-Location).Path + "\ui-redesign")) {
                Write-Status "React folder detected, starting..." "info"
                Start-React
            } else {
                Write-Status "React/NextJS not ready yet. Waiting for design completion..." "warning"
            }
        }
    }
    
    Write-Status "System startup complete!" "success"
    Write-Status "Dashboard: http://localhost:8501 (Streamlit) or http://localhost:3000 (React)" "info"
}
elseif ($Mode -eq "bridge") {
    Start-Bridge
}
elseif ($Mode -eq "streamlit") {
    Start-Streamlit
}
elseif ($Mode -eq "react") {
    Start-React
}

# Interactive menu (if no mode specified)
if (-not $PSBoundParameters.ContainsKey('Mode')) {
    while ($true) {
        Show-Menu
        $choice = Read-Host "Select option (1-8)"
        
        switch ($choice) {
            "1" { Start-Bridge }
            "2" { Start-Streamlit }
            "3" { Start-React }
            "4" { Start-Bridge; Start-Sleep -Seconds 2; Start-Streamlit }
            "5" { 
                Start-Bridge
                Start-Sleep -Seconds 2
                Start-Streamlit
                Start-Sleep -Seconds 2
                Start-React
            }
            "6" { Check-SystemHealth }
            "7" { Open-Dashboard }
            "8" { Write-Status "Exiting..."; exit }
            default { Write-Status "Invalid option" "error" }
        }
        
        Write-Host "`nPress Enter to continue..."
        Read-Host
    }
}
