@echo off
setlocal
echo ----------------------------------------------------
echo  🚀 AI Bazi PRO - Windows to WSL Launcher
echo ----------------------------------------------------

:: 获取当前目录相对于 WSL 的路径
:: 假设项目位于 WSL 的 /home/jin/bazi_predict
:: 如果路径不同，请手动修改下面的 WSL_PATH
set "WSL_PATH=/home/jin/bazi_predict"

echo 📂 WSL Project Path: %WSL_PATH%
echo 📋 Running start script in WSL...

:: 通过 WSL 执行启动脚本
wsl bash -c "cd %WSL_PATH% && ./run_wsl.sh"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ⚠️  Error occurred while starting the app.
    echo Please ensure WSL is installed and the path is correct.
    pause
)

endlocal
