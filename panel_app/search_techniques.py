from skimage.exposure import equalize_adapthist
from skimage.filters import threshold_otsu
from skimage.morphology import opening, closing, disk
import cv2
import numpy as np
from PIL import Image
import param
import panel as pn

import sys
from pathlib import Path
sys.path.append(str(Path.cwd().parent))

from plant_search.vegetation_indices import normalize_rgb, calculate_exg



class ProcessingTechnique(param.Parameterized):
    enabled = param.Boolean(default=True, doc="Choose to enable processing technique")
    input_image = param.Parameter(default=None, doc="Input image to process")
    output_image = param.Parameter(default=None, doc="Processed image after applying the technique")

    def __init__(self, **params):
        super().__init__(**params)
        # Assume output=input until technique is applied
        if self.output_image is None:
            self.output_image = self.input_image

        self._apply_button_widget = pn.widgets.Button(name="Apply", button_type="primary")
        self._apply_button_widget.on_click(self._handle_update_button)
        self._reset_button_widget = pn.widgets.Button(name="Reset Parameters", button_type="warning")
        self._reset_button_widget.on_click(self._reset_params)
        self.image_outdated = False
        self._watch_for_outdated()

    def perform_technique(self, image):
        raise NotImplementedError("Each technique must implement the `apply` method.")

    def _watch_for_outdated(self):
        """Set up watchers to mark the image as outdated when any parameter changes."""
        for name, parameter in self.param.objects("existing").items():
            if name not in {"output_image", "image_outdated"} and not parameter.constant and not parameter.readonly:
                self.param.watch(self._mark_outdated, name)

    def _mark_outdated(self, event=None):
        """Mark the image as outdated."""
        self.image_outdated = True

    def _handle_update_button(self, event):
            # Manually apply technique to prevent large overhead
            # Originally auto-computed, but cascading updates too expensive
            self.image_outdated = False
            self.update_output() # Calculate technique, update output

    def _reset_params(self, event=None):
        """Reset all parameters to their default values."""
        defaults = {
            name: param.default 
            for name, param in self.param.objects('existing').items()
            if (
                not param.constant and 
                not param.readonly and
                name != 'input_image' # Don't remove input image
            )
        }
        self.param.update(**defaults)
        self.image_outdated = True # Need to apply to get new computation

    def _prepare_np_image(self, image):
        updated = image
        if len(updated.shape) >= 3 and updated.shape[2] > 3:
            updated = updated[:, :, :3] # Max 3 bands
        if updated.dtype != np.uint8:
            updated = (updated).astype(np.uint8)  # Scale to [0, 255]
        return updated

    def apply(self, image):
        """
        Performs technique on passed image. However, this does NOT
        assume argument is 'input_image', and does NOT update the 
        param's 'output_image'. 
        """
        if self.enabled:
            prep_image = self._prepare_np_image(image) # Get to standard np_array form
            return self.perform_technique(prep_image)
        else:
            return image # Pass along without updating


    @param.depends("input_image", "enabled", watch=True)
    def _passthrough_output(self):
        """
        We assume multiple techniques may be used in sequence.

        If 'input_image' is updated and technique is disabled, simply
        pass 'input_image' through to output.

        This allows later stages to have their inputs auto-updated if
        watching for updates to this stage's output_image.
        """
        if not self.enabled:
            self.output_image = self.input_image

    def update_output(self):
        """
        Performs technique on own 'input_image', and updates 'output_image'.

        This is the only method that computes and sets 'output_image' from
        the object's own 'input_image'.
        """
        if self.input_image is not None:
            self.output_image = self.apply(self.input_image)

    def view_outdated_warning(self):
        """Return the complete UI for this technique."""
        warning_message = (
            pn.pane.Markdown(
                "**Apply to update**"
            )
            if self.image_outdated
            else ""
        )
        return warning_message

    def view_image(self):
        if self.input_image is not None:
            try:
                # output = self.apply(self.input_image)
                # output_image = Image.fromarray(output)
                input_image = Image.fromarray(self.input_image)
                if self.output_image is not None:
                    output_image = Image.fromarray(self.output_image)
                else:
                    output_image = Image.fromarray(self.input_image)

                images_row = pn.Row(
                    pn.pane.Image(input_image, height=500, width=500),
                    pn.pane.Image(output_image, height=500, width=500)
                )
                return images_row 
            except Exception as e:
                return f"{self.name}: Error displaying image: {e}"
        else:
            return "No image uploaded."

    def view(self):
        panel_column = pn.Row(
            pn.Column(
                self.param,
                self._reset_button_widget,
                pn.Row(self._apply_button_widget, self.view_outdated_warning),
            ),
            self.view_image
        )
        return panel_column



class VegetationIndex(ProcessingTechnique):
    selected_vegetation_index = param.Selector(objects=["exg"])

    def perform_technique(self, image):
        exg = calculate_exg(*normalize_rgb(image))
        exg_normalized = (exg - np.min(exg)) / (np.max(exg) - np.min(exg))  # Normalize to [0, 1]
        exg_uint8 = (exg_normalized * 255).astype(np.uint8)
        return exg_uint8


class Smoothing(ProcessingTechnique):
    smoothing_diameter = param.Integer(default=9, bounds=(3, 20), doc="Diameter of each pixel neighborhood used during filtering.")
    smoothing_sigma_color = param.Number(default=50, bounds=(20,70), doc="Controls how much influence the color difference between pixels has on the filtering")
    smoothing_sigma_spatial = param.Number(default=15, bounds=(0,45), doc="Controls the influence of the spatial distance between pixels.")

    def perform_technique(self, image):
        bilateral_smoothed_img = cv2.bilateralFilter(
            image , d=self.smoothing_diameter, 
            sigmaColor=self.smoothing_sigma_color, 
            sigmaSpace=self.smoothing_sigma_spatial
        )
        # bilateral_smoothed_img = (bilateral_smoothed_img * 255).astype(np.uint8)
        # bilateral_smoothed_exg = bilateral_smoothed_exg / 255.0  # Scale back to [0, 1]
        return bilateral_smoothed_img
    

class ContrastEnhancement(ProcessingTechnique):
    contrast_clip_limit = param.Number(default=0.02, step=0.1, bounds=(0.0, 0.15), doc="Defines the maximum allowed height of the histogram bins in each tile")

    def perform_technique(self, image):
        # image = image / 255
        
        if len(image.shape) == 3 and image.shape[2] == 4:  # RGBA
            image = image[:, :, 1]
        elif len(image.shape) == 3:  # RGB
            image = image[:, :, 1]
        # else:  # Grayscale
        #     pil_image = Image.fromarray(image)
        equal = equalize_adapthist(image, clip_limit=self.contrast_clip_limit)
        equal_int8 = (equal).astype(np.uint8) # Needs conversion back to uint8
        return equal_int8


class MorphologicalRefinement(ProcessingTechnique):
    morphological_disk_size = param.Integer(default=7, bounds=(1, 20), doc="Radius of structuring element for contour adjustment")

    def perform_technique(self, image):
        selem = disk(7)  # Structuring element
        morph_img = closing(opening(image, selem), selem)
        return morph_img
    

class ManualThresholding(ProcessingTechnique):
    enabled = param.Boolean(default=True, readonly=True)
    threshold = param.Number(default=0.5, step=0.01, bounds=(0.0, 1.0))

    def perform_technique(self, image):
        scale_image = image / 255.0 # Scale to [0,1] range
        binary_mask = scale_image > self.threshold
        mask_image = ((binary_mask).astype(np.uint8) * 255) # Convert fromi boolean to inmage
        return mask_image
    
