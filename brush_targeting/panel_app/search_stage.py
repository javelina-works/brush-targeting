import param
import panel as pn
import numpy as np
from PIL import Image



class TargetSearch(param.Parameterized):
    input_image = param.Parameter(default=None, doc="Input orthophoto to search")
    techniques = param.List(default=[])
    sample_downscaling = param.Integer(default=4, bounds=(1,10), doc="Downscale ratio of image shown in intermediate steps")
    output_image = param.Parameter(default=None, doc="Final output image after running the pipeline")

    def __init__(self, **params):
        super().__init__(**params)

        self.sample_image = None
        self.output_image = None
        self._downsample_image()
        self._setup_reactivity()
        # self._chain_techniques()
        self.progress_bar = pn.widgets.Progress(name="Pipeline Progress", value=0, max=100)
        self._pipeline_button_widget = pn.widgets.Button(name="Run full pipeline", button_type="primary")
        self._pipeline_button_widget.on_click(self._handle_pipeline_button)

    @param.depends("input_image", "sample_downscaling", watch=True)
    def _downsample_image(self):
        if self.input_image is not None:
            ds = self.sample_downscaling # Ratio of pixels to ignore
            self.sample_image = self.input_image[::ds, ::ds]
        else:
            self.sample_image = None

    # def _chain_techniques(self):
    #     prev_output = self.input_image
        
    #     for technique in self.techniques:
    #         technique.input_image = prev_output
    #         output = technique.apply(prev_output)
    #         technique.output_image = output  # Store the output in the technique
    #         prev_output = output

    def _setup_reactivity(self):
        """
        Chain the child techniques together reactively.
        
        Each technique will react and update it's input in the event its predecessor's
        'output_image' is updated. 
        """
        for i, technique in enumerate(self.techniques):
            if i == 0: # First technique takes the main input_image as input
                technique.param.update(input_image=self.sample_image)
                # print(f"Linking {technique.__class__.__name__} input_image to TargetSearch input_image.")
                self.param.watch(lambda event, tech=technique: tech.param.update(input_image=event.new), "input_image")
            else: # Subsequent techniques depend on the output of the previous one
                prev_technique = self.techniques[i - 1]
                # print(f"Linking {technique.__class__.__name__} input_image to {prev_technique.__class__.__name__} output_image.")
                prev_technique.param.watch(
                    lambda event, tech=technique: tech.param.update(input_image=event.new),
                    "output_image"
                )

    def _handle_pipeline_button(self, event=None):
        # TODO: trigger full pipeline run event
        output = self.search_targets()
        self.output_image = output


    def update_output(self):
        return

    def search_image(self, image):
        """
        Performs the full search pipeline as configured on an arbitrary image.
        """
        prev_output = image
        output = prev_output # output starts with no changes
        for technique in self.techniques:
            output = technique.apply(prev_output)
            prev_output = output
        return output

    # @param.output()
    def search_targets(self):
        """
        Run the full pipeline and update the progress bar.
        
        """
        if self.input_image is None:
            return None # no image to process
        num_techniques = len(self.techniques)
        if num_techniques == 0:
            print("No techniques to run in the pipeline.")
            return None
        
        self.progress_bar.value = 0
        self.progress_bar.max = num_techniques

        prev_output = self.input_image
        output = prev_output # output starts with no changes
        for i, technique in enumerate(self.techniques):
            output = technique.apply(prev_output)
            prev_output = output
            self.progress_bar.value = i + 1
            
        self.progress_bar.value = self.progress_bar.max
        return output
    
        # for technique in self.techniques:
        #     technique.update_output()
        # return self.techniques[-1].output_image if self.techniques else None

    def _downscale_for_display(self, image, max_width=1000, max_height=1000):
        """Downscale an image for display purposes."""
        if len(image.shape) == 3 and image.shape[2] == 4:  # RGBA
            pil_image = Image.fromarray(image[:, :, :3])  # Strip alpha for display
        elif len(image.shape) == 3:  # RGB
            pil_image = Image.fromarray(image)
        else:  # Grayscale
            pil_image = Image.fromarray(image)

        pil_image.thumbnail((max_width, max_height))  # Resize while maintaining aspect ratio
        return pil_image

    @param.depends("output_image", watch=False)
    def view_images(self):
        if self.input_image is not None:
            try:
                input_image = self._downscale_for_display(self.input_image)
                input_image_pane = pn.pane.Image(input_image, height=500, width=500)
            except Exception as e:
                input_image_pane = f"{self.name}: Error displaying input image: {e}"
        else:
            input_image_pane = "No image uploaded."
        
        if self.output_image is not None:
            try:
                output_image = self._downscale_for_display(self.output_image)
                output_image_pane = pn.pane.Image(output_image, height=500, width=500)
            except Exception as e:
                output_image_pane = f"{self.name}: Error displaying output image: {e}"
        else:
            output_image_pane = "Output not yet generated!"
            
        return pn.Row(input_image_pane, output_image_pane)

    @param.depends()
    def view(self):
        # panels = [technique.view() for technique in self.techniques]
        tabs = pn.Tabs(
            *[  (technique.__class__.__name__, technique.view())
                for technique in self.techniques
            ])

        target_panel = pn.Column(
            pn.Row("**Find targets from image**"),
            tabs,
            pn.layout.Divider(),
            pn.Row(self._pipeline_button_widget, self.progress_bar,),
            self.view_images,
        )
        return target_panel
