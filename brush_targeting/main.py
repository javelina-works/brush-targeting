import panel as pn
import param

# from panel_app.pipeline import (
#     StageUpload, StageSearch, StageAcquireTargets, StageAudit
# )

# pn.extension('ipywidgets', 'filedropper')
# pipeline = pn.pipeline.Pipeline()

# pipeline.add_stage('Upload', StageUpload)
# pipeline.add_stage('Search', StageSearch)
# pipeline.add_stage('Targeting', StageAcquireTargets)
# pipeline.add_stage('Audit', StageAudit)

# # pipeline.show()
# pipeline.servable()



import brush_targeting.panel_app
import brush_targeting.plant_search
import brush_targeting.macro_planning

from brush_targeting import panel_app, plant_search, macro_planning


from brush_targeting.panel_app.pipeline import (
    StageUpload, StageSearch, StageAcquireTargets, StageAudit
)


def create_panel_app():
    pn.extension('ipywidgets', 'filedropper')
    pipeline = pn.pipeline.Pipeline()

    pipeline.add_stage('Upload', StageUpload)
    pipeline.add_stage('Search', StageSearch)
    pipeline.add_stage('Targeting', StageAcquireTargets)
    pipeline.add_stage('Audit', StageAudit)

    return pipeline