from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from panel.io.fastapi import add_applications, add_application
import panel as pn

from brush_targeting.routes import (
    health, files,
    # project, processing, map
)
from brush_targeting.panel_ui.panel_app import get_projects, get_processing, get_maps



# Initialize FastAPI app
app = FastAPI(title="Brush Targeting App", version="1.0")

# CORS Middleware (optional, useful for a future JS frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(health.router) # Health check
app.include_router(files.router) # 

# app.include_router(project.router, prefix="/projects", tags=["Projects"])
# app.include_router(processing.router, prefix="/processing", tags=["Processing"])
# app.include_router(map.router, prefix="/map", tags=["Map"])

# Serve Panel UI as a FastAPI route
@app.get("/")
async def read_root():
    return {"Hello": "World"}

# @add_application('/panel', app=app, title='My Panel App', admin=True)
# def create_panel_app():
#     slider = pn.widgets.IntSlider(name='Slider', start=0, end=10, value=3)
#     return slider.rx() * '⭐'

bokeh_fast_api = add_applications({
        "/projects": get_projects,
        "/processing": get_processing,
        "/map": get_maps,
    }, 
    app=app,
    location=True,
    liveness=False, # No liveness handler
    admin=False, # enable admin panel
    session_history=100, # How much history to accumulate
    
    check_unused_sessions_milliseconds=1000,
    unused_session_lifetime_milliseconds=10,
)


import json
from fastapi.encoders import jsonable_encoder

@app.get("/huh")
async def read_root():
    apps = bokeh_fast_api._applications
    results = {}

    for slug, app in apps.items():
        
        # Convert Panel app attributes to a readable format
        app_attrs = {k: str(v) for k, v in app.__dict__.items()}

        # Bokeh Server Application inside the Panel Application
        application = app._application
        app_server_attrs = {k: str(v) for k, v in application.__dict__.items()}

        results[slug] = {
            "panel_app_attrs": app_attrs,
            "bokeh_app_attrs": app_server_attrs,
        }

    return jsonable_encoder(results)  # Ensures FastAPI can return it as JSON
    

# Run the app if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)






# import panel as pn
# import param
# import geoviews as gv
# from panel_app.pipeline import (
#     StageSelect, StageUpload, StageSearch, StageAcquireTargets, 
#     StageAudit, StageRouting, StageDownload
# )
# from brush_targeting.persistence.project import ProjectManager, Project


# import logging
# import sys

# # pn.extension('ipywidgets', 'filedropper')
# # pn.extension('filedropper')

# # gv.extension('bokeh')
# # pn.extension('filedropper')
# # pn.extension('ipywidgets')
# pn.extension('modal')
# pn.extension()



# FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

# @pn.cache
# def get_logger(name, format_=FORMAT, level=logging.INFO):
#     logger = logging.getLogger(name)

#     logger.handlers.clear()

#     handler = logging.StreamHandler()
#     handler.setStream(sys.stdout)
#     formatter = logging.Formatter(format_)
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)
#     logger.propagate = False

#     logger.setLevel(level)
#     logger.info("Logger successfully configured")
#     return logger

# # get_logger(name="bokeh", level=logging.DEBUG)
# # get_logger(name="panel", level=logging.DEBUG)
# # logger = get_logger(name="app", level=logging.DEBUG)

# def create_panel_app():

#     pipeline = pn.pipeline.Pipeline()

#     pipeline.add_stage('Select', StageSelect)
#     # pipeline.add_stage('Upload', StageUpload)
#     # pipeline.add_stage('Search', StageSearch)
#     # pipeline.add_stage('Targeting', StageAcquireTargets)
#     pipeline.add_stage('Audit', StageAudit)
#     # pipeline.add_stage('Routing', StageRouting)
#     pipeline.add_stage('Download', StageDownload)

#     return pipeline

# def serve_panel_stage():
#     pm = ProjectManager()
#     get_project = pm.load_project('test1')
#     stage = StageAudit(project=get_project)

#     return stage

# pipeline = create_panel_app()
# pipeline.servable()

# # audit = serve_panel_stage()
# # audit.panel().servable()

# if __name__ == "__main__":
#     print("Running as python script")
#     # pipeline.show() # Only when running with python
#     # pn.serve(pipeline)