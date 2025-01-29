import panel as pn

from fastapi import FastAPI
from panel.io.fastapi import add_application

from brush_targeting import panel_app, plant_search, macro_planning
from brush_targeting.panel_app.pipeline import (
    StageUpload, StageSearch, StageAcquireTargets, StageAudit
)


def create_panel_widget():
    slider = pn.widgets.IntSlider(name='Slider', start=0, end=10, value=3)
    return slider.rx() * '⭐'


def create_panel_app():
    pn.extension('ipywidgets', 'filedropper')
    pipeline = pn.pipeline.Pipeline()

    pipeline.add_stage('Upload', StageUpload)
    pipeline.add_stage('Search', StageSearch)
    pipeline.add_stage('Targeting', StageAcquireTargets)
    pipeline.add_stage('Audit', StageAudit)

    return pipeline