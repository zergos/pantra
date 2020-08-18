@echo off
set PYTHON_DIR=C:\python37
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cython pantra.pyx --embed -3
cl.exe  /nologo /Ox /MD /W3 /GS- /DNDEBUG -I%PYTHON_DIR%\include /Tcpantra.c /link /OUT:"pantra.exe" /SUBSYSTEM:CONSOLE /LIBPATH:%PYTHON_DIR%\libs /MACHINE:x64
pantra
