import panel as pn
import param
import geoviews as gv
from panel_app.pipeline import (
    StageSelect, StageUpload, StageSearch, StageAcquireTargets, 
    StageAudit, StageRouting, StageDownload
)
from brush_targeting.persistence.project import ProjectManager, Project


import logging
import sys

# pn.extension('ipywidgets', 'filedropper')
# pn.extension('filedropper')

# gv.extension('bokeh')
# pn.extension('filedropper')
# pn.extension('ipywidgets')
pn.extension('modal')
pn.extension()



FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

@pn.cache
def get_logger(name, format_=FORMAT, level=logging.INFO):
    logger = logging.getLogger(name)

    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setStream(sys.stdout)
    formatter = logging.Formatter(format_)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    logger.setLevel(level)
    logger.info("Logger successfully configured")
    return logger

# get_logger(name="bokeh", level=logging.DEBUG)
# get_logger(name="panel", level=logging.DEBUG)
# logger = get_logger(name="app", level=logging.DEBUG)

def create_panel_app():

    pipeline = pn.pipeline.Pipeline()

    pipeline.add_stage('Select', StageSelect)
    # pipeline.add_stage('Upload', StageUpload)
    # pipeline.add_stage('Search', StageSearch)
    # pipeline.add_stage('Targeting', StageAcquireTargets)
    pipeline.add_stage('Audit', StageAudit)
    # pipeline.add_stage('Routing', StageRouting)
    pipeline.add_stage('Download', StageDownload)

    return pipeline

def serve_panel_stage():
    pm = ProjectManager()
    get_project = pm.load_project('test1')
    stage = StageAudit(project=get_project)

    return stage

# pipeline = create_panel_app()
# pipeline.servable()

audit = serve_panel_stage()
audit.panel().servable()

if __name__ == "__main__":
    print("Running as python script")
    # pipeline.show() # Only when running with python
    # pn.serve(pipeline)