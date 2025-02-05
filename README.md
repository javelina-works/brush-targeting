# brush-targeting
A local-first app for identifying woody brush from an orthophoto and planning efficient treatment routes.

Here's a section you can include in your documentation to explain how to download dependencies using Poetry:


## Running the Apps

Just the Panel Server:
```bash
poetry run panel serve brush_targeting/main.py --dev
```

or 

```bash
poetry run panel serve brush_targeting/main.py --dev --admin
```

/app
│── main.py               # FastAPI entry point
│── panel_app.py          # Panel UI served within FastAPI
│── routers/              # FastAPI API endpoints
│   ├── project.py        # CRUD operations for Projects
│   ├── processing.py     # Routes to trigger computations
│   ├── map.py            # Routes for map-related data
│── models/               # Data models & schemas
│   ├── project.py        # Project model
│── services/             # Core logic (not tied to FastAPI)
│   ├── project_manager.py  # Handles project creation & file storage
│   ├── processing.py       # Image & geospatial computations
│   ├── optimization.py     # Optimization algorithms
│── static/               # Future: Frontend assets (if moving to JS)
│── requirements.txt      # Dependencies
│── Dockerfile            # Container setup


/app                     # ✅ New main package
│── /models              # ✅ Data models (Pydantic, DB schemas)
│   ├── project.py       # ✅ Project schema & model
│   ├── user.py          # ✅ (If needed) User authentication schema
│   ├── processing.py    # ✅ Data models for processing tasks
│── /routes              # ✅ FastAPI route definitions
│── /services            # ✅ Core business logic (processing, optimization)
│── /panel_ui            # ✅ Panel application (UI components)
│── /persistence         # ✅ File management & project persistence
│── /macro_planning      # ✅ Drone path optimization
│── /plant_search        # ✅ Image analysis & feature detection
│── main.py              # ✅ FastAPI entry point
│── panel_app.py         # ✅ Panel UI served in FastAPI
│── __init__.py          # ✅ Marks this as a package



## Installation Instructions
### Installing Dependencies with Poetry

To set up your environment and install the dependencies for this project, follow these steps:

#### Prerequisites
1. Ensure you have **Poetry** installed on your system. If you don’t have it installed, you can install it using the guide at [Python-Poetry](https://python-poetry.org/docs/#installation).
2. Make sure you have Python installed (version `3.x`, as specified in `pyproject.toml`).

#### Installing Dependencies
1. **Clone the repository** (if you haven’t already):
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Install the dependencies** using Poetry:
   ```bash
   poetry install
   ```
   This will:
   - Create a virtual environment (if not already created).
   - Install all dependencies specified in the `pyproject.toml` file.
   - Resolve exact versions based on the `poetry.lock` file.

3. **Activate the Virtual Environment** (Optional):
   If you want to work inside the virtual environment Poetry creates, activate it:
   ```bash
   poetry shell
   ```

4. **Run the Application**:
   After installing the dependencies, you can run the application (example for a Panel app):
   ```bash
   poetry run panel serve panel_app/main.py
   ```


#### Poetry Management Notes
- If you need to add new dependencies, use:
  ```bash
  poetry add <package-name>
  ```
  For development-only dependencies (e.g., testing tools or linters), use:
  ```bash
  poetry add --dev <package-name>
  ```

- If you want to generate a `requirements.txt` for compatibility with other tools:
  ```bash
  poetry export -f requirements.txt --output requirements.txt
  ```

---
 
## Running The App
Run the app via the FastAPI server with the following command:

```bash
poetry run uvicorn brush_targeting.main:app --reload
```