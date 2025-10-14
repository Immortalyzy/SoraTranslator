.\.venv\Scripts\pyinstaller app.py ^
  --name SoraBackend ^
  --onefile ^
  --noconsole ^
  --add-data "Integrators;Integrators"    ^
  --paths "." ^
  --distpath dist_py ^
  --workpath build_py ^
  --clean