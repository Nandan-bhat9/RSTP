@echo off
setlocal
echo ==========================================================
echo KAVACH RTSP Simulator — Windows Firewall Rule
echo ==========================================================
echo.
echo This script will add an inbound Windows Firewall rule for:
echo   Port: 8554
echo   Protocol: TCP
echo   Rule Name: KAVACH_RTSP_CCTV_8554
echo.
echo NOTE: Must be run as Administrator (Right click -> Run as administrator).
echo.
netsh advfirewall firewall show rule name="KAVACH_RTSP_CCTV_8554" >nul 2>&1
if %errorlevel% equ 0 (
    echo Firewall rule 'KAVACH_RTSP_CCTV_8554' already exists.
    pause
    exit /b 0
)

echo Adding inbound rule for TCP port 8554...
netsh advfirewall firewall add rule name="KAVACH_RTSP_CCTV_8554" dir=in action=allow protocol=TCP localport=8554 profile=any description="Allow RTSP traffic for KAVACH multi-camera presentation simulation"

if %errorlevel% equ 0 (
    echo.
    echo SUCCESS: Port 8554 TCP is now allowed through Windows Firewall.
) else (
    echo.
    echo ERROR: Failed to add firewall rule. Please ensure you ran this script as Administrator.
)
echo.
pause
