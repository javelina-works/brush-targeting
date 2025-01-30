import panel as pn
import param
from brush_targeting.persistence.project import ProjectManager, Project

pn.extension('modal')

class ProjectManagerWidget(ProjectManager):
    """Panel UI widget for managing projects."""
    
    selected_project = param.ClassSelector(class_=Project, allow_None=True, doc="Currently selected project")
    project_name_input = param.String(default="", doc="User input for new project")
    status_message = param.String(default="", doc="Status feedback for the user")

    def __init__(self, **params):
        pn.extension('modal')
        super().__init__(**params)
        self._initialize_ui()

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
        """Constructs the UI elements."""
        self.project_selector = pn.widgets.Select(
            name="Existing Projects", options=self.list_projects(), value=""
        )
        self.project_selector.param.watch(self._update_selected_project, "value")

        # Create project interface is in a hidden modal
        self._create_project_modal()
        self.create_button = self.modal.create_button('toggle', name="➕ New Project")

    def _update_selected_project(self, event):
        """Loads and sets the selected project."""
        project_name = event.new
        if project_name:
            self.selected_project = self.load_project(project_name)
        else:
            self.selected_project = None

    def _handle_create_project(self, event):
        """Handles the creation of a new project."""
        project_name = self.project_input.value.strip()
        if not project_name:
            self.status_message = "⚠️ Project name cannot be empty."
        else:
            try:
                self.selected_project = self.create_project(project_name)  # Now returns a Project instance
                self.status_message = f"✅ Project '{project_name}' created successfully!"
                self._refresh_project_list()
                # Clear input field and close modal
                self.project_input.value = ""  
                self.modal.visible = False 
            except FileExistsError:
                self.status_message = f"⚠️ Project '{project_name}' already exists."
            except ValueError as e:
                self.status_message = f"⚠️ {str(e)}"
        
        self.status_pane.object = self.status_message  # Update UI

    def _refresh_project_list(self):
        """Refresh the project dropdown after adding a new project."""
        self.project_selector.options = self.list_projects()

    def panel(self):
        """Builds the UI layout."""
        projects_buttons = pn.FlexBox(
            self.create_button,
            align_items="flex-end",
            justify_content="end"
        )

        layout = pn.Column(
            "# Targeting Projects",
            "Open an existing project or create a new one!",
            projects_buttons,
            "## Existing Projects",
            self.project_selector,
            self.modal
        )
        return layout
