import panel as pn
import param
from panel_app.pipeline import (
    StageSelect, StageUpload, StageSearch, StageAcquireTargets, 
    StageAudit, StageRouting, StageDownload
)


def create_panel_app():
    pn.extension('ipywidgets', 'filedropper')
    pipeline = pn.pipeline.Pipeline()

    pipeline.add_stage('Select', StageSelect)
    # pipeline.add_stage('Upload', StageUpload)
    # pipeline.add_stage('Search', StageSearch)
    # pipeline.add_stage('Targeting', StageAcquireTargets)
    # pipeline.add_stage('Audit', StageAudit)
    pipeline.add_stage('Routing', StageRouting)
    pipeline.add_stage('Download', StageDownload)

    return pipeline

pipeline = create_panel_app()
pipeline.servable()

if __name__ == "__main__":
    pipeline.show()