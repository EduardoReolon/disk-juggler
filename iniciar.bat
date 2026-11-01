@echo off
:: Força o diretório de trabalho a ser a pasta exata onde este .bat está salvo
cd /d "%~dp0"

:: Ativa o ambiente virtual 
call venv\Scripts\activate

:: Executa o programa
python main.py
pause