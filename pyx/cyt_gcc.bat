# build.bat
set PROJECT_NAME=fruits
set PYTHON_DIR=C:\python37
%PYTHON_DIR%\python -m cython --embed -o %PROJECT_NAME%.c %PROJECT_NAME%.py
gcc -Os -I %PYTHON_DIR%\include -o %PROJECT_NAME%.exe %PROJECT_NAME%.c -lpython37 -lm -L %PYTHON_DIR%\libs
