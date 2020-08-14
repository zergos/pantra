@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
cython pantra.pyx --embed -3
cl.exe  /nologo /Ox /MD /W3 /GS- /DNDEBUG -Ic:\Python37\include /Tcpantra.c /link /OUT:"pantra.exe" /SUBSYSTEM:CONSOLE /LIBPATH:c:\Python37\libs /MACHINE:x64
pantra
