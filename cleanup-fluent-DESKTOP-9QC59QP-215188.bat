echo off
set LOCALHOST=%COMPUTERNAME%
set KILL_CMD="C:\PROGRA~1\ANSYSI~1\v252\fluent/ntbin/win64/winkill.exe"

start "tell.exe" /B "C:\PROGRA~1\ANSYSI~1\v252\fluent\ntbin\win64\tell.exe" DESKTOP-9QC59QP 51808 CLEANUP_EXITING
timeout /t 1
"C:\PROGRA~1\ANSYSI~1\v252\fluent\ntbin\win64\kill.exe" tell.exe
if /i "%LOCALHOST%"=="DESKTOP-9QC59QP" (%KILL_CMD% 251556) 
if /i "%LOCALHOST%"=="DESKTOP-9QC59QP" (%KILL_CMD% 252224) 
if /i "%LOCALHOST%"=="DESKTOP-9QC59QP" (%KILL_CMD% 185904) 
if /i "%LOCALHOST%"=="DESKTOP-9QC59QP" (%KILL_CMD% 251260) 
if /i "%LOCALHOST%"=="DESKTOP-9QC59QP" (%KILL_CMD% 215188) 
if /i "%LOCALHOST%"=="DESKTOP-9QC59QP" (%KILL_CMD% 250916)
del "Z:\UFX_dilhara\Ansys\3D_CFD_Optimizer\Manual\cleanup-fluent-DESKTOP-9QC59QP-215188.bat"
