from fastapi import FastAPI
from backend.routes import files, health, panel

from panel.io.fastapi import add_applications, add_application
from brush_targeting.main import create_panel_app

app = FastAPI(title="FastAPI Backend for Panel App")

# Include routes
app.include_router(files.router)
app.include_router(health.router)

# Run Panel app in FastAPI
# https://panel.holoviz.org/how_to/integrations/FastAPI.html#tips-tricks
add_applications({
    "/": panel.create_panel_app,
    "/widget": panel.create_panel_widget,
}, app=app)


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)
