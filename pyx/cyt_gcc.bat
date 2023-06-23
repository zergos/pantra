# build.bat
set PATH=C:\cygwin64\bin;%path%
set PROJECT_NAME=pantra
set PYTHON_DIR=/cygdrive/C/Python310
rem cython --embed -o %PROJECT_NAME%.c %PROJECT_NAME%.pyx
C:\cygwin64\bin\gcc -Os -I %PYTHON_DIR%/include -B %PYTHON_DIR%/libs -o %PROJECT_NAME%.exe %PROJECT_NAME%.c -lpython310 -lm -L %PYTHON_DIR%\libs
