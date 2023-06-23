@echo off
copy t64.exe pantra.exe
echo #!%VIRTUAL_ENV%\Scripts\python.exe>> pantra.exe
tar -a -c -f out.zip __main__.py
type out.zip >> pantra.exe
del out.zip
echo Done
