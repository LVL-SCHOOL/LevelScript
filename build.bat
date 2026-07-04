@echo off
pyinstaller --onedir --hidden-import=requests --hidden-import=pygame --icon=assets\icon.ico --add-data "src\core\extend;src\core\extend" --add-data "src\core\docs_generate;src\core\docs_generate" .\lvl.py

xcopy /E /I examples dist\lvl\examples\
copy hello_world.lvl dist\lvl\
copy lvl_config.env_sample dist\lvl\
