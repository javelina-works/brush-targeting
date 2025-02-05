import panel as pn

def create_panel_app():
    """Creates a Panel UI with a consistent template."""
    
    template = pn.template.FastListTemplate(
        title="Brush Targeting Dashboard",
        sidebar=[pn.pane.Markdown("# Navigation"),
                 pn.widgets.Button(name="Projects", button_type="primary"),
                 pn.widgets.Button(name="Processing", button_type="primary"),
                 pn.widgets.Button(name="Map", button_type="primary")],
    )

    # Function to generate views dynamically
    def get_page_content(page_name):
        if page_name == "projects":
            return pn.Column("# Projects", pn.pane.Markdown("Manage your projects here."))
        elif page_name == "processing":
            return pn.Column("# Processing", pn.pane.Markdown("Run image processing tasks."))
        elif page_name == "map":
            return pn.Column("# Map", pn.pane.Markdown("View geospatial data and waypoints."))
        else:
            return pn.Column("# Home", pn.pane.Markdown("Welcome to the dashboard!"))

    # Default to home view
    template.main[:] = [get_page_content("home")]

    return template

# Run as a standalone Panel server (optional, for testing Panel separately)
if __name__ == "__main__":
    create_panel_app().servable()
