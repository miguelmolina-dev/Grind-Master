@echo off
:: Asegura que estamos en el directorio donde reside el .bat
cd G:\Proyectos_Python\resolvers-log

:: Ejecuta el ejecutable de python dentro del venv directamente
:: Esto evita tener que "activar" el entorno manualmente
.\.venv\Scripts\python.exe -m streamlit run src/ui/app.py

pause