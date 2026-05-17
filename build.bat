@echo off
echo Building Gym Fingerprint Bridge executable...
echo.

pip install pyinstaller -q
pip install -r requirements.txt -q

pyinstaller --onefile ^
    --name gym-bridge ^
    --hidden-import=uvicorn.logging ^
    --hidden-import=uvicorn.protocols.http ^
    --hidden-import=uvicorn.protocols.websockets ^
    --hidden-import=uvicorn.lifespan.on ^
    --hidden-import=zk ^
    main.py

echo.
echo Done! Executable is at dist\gym-bridge.exe
pause
