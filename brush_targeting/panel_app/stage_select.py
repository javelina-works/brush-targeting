import panel as pn
from panel.io import hold
import param
import os
import datetime
from brush_targeting.persistence.project import ProjectManager, Project

pn.extension('modal')

class ProjectManagerWidget(ProjectManager):
    """Panel UI widget for managing projects."""
    
    # project_list = param.Selector(objects=['a','b','c'], doc="Available projects")
    project_list = param.Selector(objects=[], doc="Available projects")
    selected_project = param.ClassSelector(class_=Project, allow_None=True, doc="Currently selected project")
    project_name_input = param.String(default="", doc="User input for new project")
    status_message = param.String(default="", doc="Status feedback for the user")

    def __init__(self, **params):
        pn.extension('modal')
        super().__init__(**params)

        project_list = self.list_projects() or []
        self.param.project_list.objects = project_list  # Sync available projects
        self.project_list = project_list[0] if project_list else None  # Ensure default selection
        # print(f"Projects: {self.project_list}, type of {type(self.project_list)}")
        self._initialize_ui()
        self.selected_project = self.load_project(self.project_list) if self.project_list else None
        # print(f"Project: {self.selected_project}, type of {type(self.selected_project)}")
        

    def _create_project_modal(self):
        """Modal for creating a new project."""
        self.project_input = pn.widgets.TextInput(name="Name", placeholder="Enter project name")
        
        self.status_pane = pn.pane.Markdown(self.status_message)
        self.confirm_create_button = pn.widgets.Button(name="Create Project", button_type="primary")
        self.confirm_create_button.on_click(self._handle_create_project)

        # Modal: Initially hidden
        self.modal = pn.Modal(
            pn.pane.Markdown("## New Project"),
            pn.layout.Divider(),
            self.status_pane,
            self.project_input,
            self.confirm_create_button,
            name="Create Project",
            margin=40
        )

    def _initialize_ui(self):
        """Constructs the UI elements and initializes project selection."""
        # Metadata Pane
        self.metadata_pane = pn.pane.Markdown("", visible=False, sizing_mode="stretch_width")
        self.param.watch(self._update_metadata_pane, ['selected_project'], precedence=2)

        # Create project interface in a hidden modal
        self._create_project_modal()
        self.create_button = self.modal.create_button('toggle', name="➕ New Project")
        
        self.delete_button = pn.widgets.Button(name="🗑 Delete Project", button_type="danger")
        self.delete_button.on_click(self._handle_delete_project)


    @param.depends('project_list', watch=True)
    def _update_selected_project(self):
        project_name = self.project_list # Current value of selector
        self.selected_project = self.load_project(project_name) if project_name else None

    def _update_metadata_pane(self, event):
        """Updates the metadata pane with project details."""
        if not self.selected_project:
            self.metadata_pane.object = ""  # Clear content
            self.metadata_pane.visible = False
            return
        
        metadata = self.selected_project.load_metadata() # Fetch metadata
        last_modified = datetime.datetime.fromtimestamp(
            os.path.getmtime(self.selected_project.metadata_path)
        ).strftime("%Y-%m-%d %H:%M:%S")

        # Format and update pane
        metadata_text = f"""
        ## 📂 Project Metadata
        - **Project Name:** {self.selected_project.name}
        - **Input Files:** {len(metadata.get("inputs", []))}
        - **Output Files:** {len(metadata.get("outputs", []))}
        - **Last Modified:** {last_modified}
        """
        self.metadata_pane.object = metadata_text
        self.metadata_pane.visible = True  # Make it visible

    def _handle_delete_project(self, event):
        """Deletes the selected project and updates the UI."""
        if not self.selected_project: return  # No project selected

        project_name = self.selected_project.name
        try:
            self.delete_project(project_name)  # Delete from disk
            self._refresh_project_list()  # Refresh the UI
            self.status_message = f"✅ Project '{project_name}' deleted successfully!"

            # Auto-select the next available project
            self.selected_project = self.project_list[0] if self.project_list else None
        except Exception as e:
            self.status_message = f"⚠️ Error deleting project '{project_name}': {e}"

        print(self.status_message)

    def _handle_create_project(self, event):
        """Handles the creation of a new project."""
        project_name = self.project_input.value.strip()
        if not project_name:
            self.status_message = "⚠️ Project name cannot be empty."
        else:
            try:
                self.selected_project = self.create_project(project_name)  # Now returns a Project instance
                self.status_message = f"✅ Project '{project_name}' created successfully!"
                self._refresh_project_list(project_name)
                self.project_input.value = ""  # Clear input field and close modal
                self.modal.visible = False
            except FileExistsError:
                self.status_message = f"⚠️ Project '{project_name}' already exists."
            except ValueError as e:
                self.status_message = f"⚠️ {str(e)}"
        
        self.status_pane.object = self.status_message  # Update UI

    def _refresh_project_list(self, new_name=None):
        """Refresh the project dropdown after adding a new project."""
        project_list = self.list_projects()
        self.param.project_list.objects = project_list  # Sync available projects
        if new_name:
            self.project_list = new_name  # Update to latest value
        else:
            self.project_list = project_list[0] if project_list else None  # Ensure default selection

        self.selected_project = self.load_project(self.project_list) if self.project_list else None

    def panel(self):
        """Builds the UI layout."""
        projects_buttons = pn.FlexBox(
            self.create_button,
            align_items="flex-end",
            justify_content="start"
        )
        layout = pn.Column(
            "# Targeting Projects",
            "Open an existing project or create a new one!",
            projects_buttons,
            "## Existing Projects",
            pn.Row(
                self.param.project_list,
                pn.Column(
                    self.delete_button,
                    self.metadata_pane,  # Display metadata
                ),
            ),
            self.modal
        )
        return layout