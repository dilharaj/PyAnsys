echo off
set LOCALHOST=%COMPUTERNAME%
set KILL_CMD="C:\PROGRA~1\ANSYSI~1\v252\fluent/ntbin/win64/winkill.exe"

start "tell.exe" /B "C:\PROGRA~1\ANSYSI~1\v252\fluent\ntbin\win64\tell.exe" DESKTOP-9QC59QP 64973 CLEANUP_EXITING
timeout /t 1
"C:\PROGRA~1\ANSYSI~1\v252\fluent\ntbin\win64\kill.exe" tell.exe
if /i "%LOCALHOST%"=="DESKTOP-9QC59QP" (%KILL_CMD% 36496) 
if /i "%LOCALHOST%"=="DESKTOP-9QC59QP" (%KILL_CMD% 30900) 
if /i "%LOCALHOST%"=="DESKTOP-9QC59QP" (%KILL_CMD% 36140)
del "Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cleanup-fluent-DESKTOP-9QC59QP-30900.bat"
