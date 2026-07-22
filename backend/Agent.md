## Python environment

Use the existing Windows virtual environment at `.venv`.

Never install this project's dependencies into global Python.

Do not use plain `python`, `pip`, `pytest`, or `uvicorn`.

Use these commands:

- Install project:
  `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`
- Run tests:
  `.\.venv\Scripts\python.exe -m pytest`
- Run modules:
  `.\.venv\Scripts\python.exe -m <module>`

Before installing anything, verify:

`.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"`