import panel as pn
import param

from panel_app.pipeline import (
    StageUpload, StageSearch, StageAcquireTargets, StageAudit
)


pn.extension('ipywidgets', 'filedropper')
pipeline = pn.pipeline.Pipeline()

pipeline.add_stage('Upload', StageUpload)
pipeline.add_stage('Search', StageSearch)
pipeline.add_stage('Targeting', StageAcquireTargets)
pipeline.add_stage('Audit', StageAudit)

# pipeline.show()
pipeline.servable()