import geopandas as gpd
import param
import panel as pn
from PIL import Image
from ..plant_search.image_preprocess import identify_targets, assign_target_metadata
from ..plant_search.load_image import load_image

class AcquireTargetsWidget(param.Parameterized):
    binary_mask = param.Parameter(allow_None=False, doc="2D np.array of binary mask")
    input_image_transform=param.Parameter(allow_None=False, doc="Transform to map image np.ndarray to geospatial reference")
    region_name = param.String(default="Region Outline", doc="Name of region for which we have an outline")
    region_version = param.String(default="Region version", doc="The outline version to associate with each target")
    targets_gdf = param.Parameter(default=None, doc="GDF of potential targets")


    def __init__(self, **params):
        super().__init__(**params)
        self.find_targets() # Auto-search on init

        self._get_targets_button_widget = pn.widgets.Button(name="Find targets from binary mask", button_type="primary")
        self._get_targets_button_widget.on_click(self._handle_targets_button_click)

    def _handle_targets_button_click(self, event=None):
        self.find_targets()

    @param.depends("binary_mask", watch=True)
    def find_targets(self):
        if self.binary_mask is None:
            print("Binary mask is None!")
            return None # Need binary mask to perform
        only_targets_gdf = identify_targets(self.binary_mask, self.input_image_transform)
        self.targets_gdf = assign_target_metadata(only_targets_gdf, self.region_name, self.region_version)

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


    def view_output_targets(self):
        output_panel = "Output here"
        return output_panel

    @param.depends("binary_mask", watch=False)
    def view_binary_mask(self):
        if self.binary_mask is not None:
            input_mask = self._downscale_for_display(self.binary_mask)
            return pn.Row(
                "Input binary mask",
                pn.pane.Image(input_mask, height=500, width=500)
            )
        else:
            return "No binary mask image uploaded!"

    def view(self):
        targeting_panel = pn.Column(
            pn.Row("# Find Targets from Mask"),
            self._get_targets_button_widget,
            self.view_binary_mask,
        )
        return targeting_panel

