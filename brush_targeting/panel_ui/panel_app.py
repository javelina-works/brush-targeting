import panel as pn

pn.extension(
    disconnect_notification='Connection lost, try reloading the page!',
    ready_notification='Application fully loaded.',
)


sidebar=[
            pn.pane.Markdown("# Navigation"),
            pn.pane.HTML('<a href="/" class="pn-button primary full-width">Home</a>'),
            pn.pane.HTML('<a href="/projects" class="pn-button primary full-width">Projects</a>'),
            pn.pane.HTML('<a href="/processing" class="pn-button primary full-width">Processing</a>'),
            pn.pane.HTML('<a href="/map" class="pn-button primary full-width">Map</a>'),
        ] 

def get_panel_template():
    """Creates a Panel UI with a dynamic template and navigation buttons."""

    # Define the Panel template
    template = pn.template.BootstrapTemplate(
        title="Brush Targeting Dashboard",
        sidebar=[
            pn.pane.Markdown("# Navigation"),
            pn.pane.HTML('<a href="/" class="pn-button primary full-width">Home</a>'),
            pn.pane.HTML('<a href="/projects" class="pn-button primary full-width">Projects</a>'),
            pn.pane.HTML('<a href="/processing" class="pn-button primary full-width">Processing</a>'),
            pn.pane.HTML('<a href="/map" class="pn-button primary full-width">Map</a>'),
        ],
    )
    return template

def get_projects():
    doc = pn.state.curdoc # Ensure session is scoped.
    template = get_panel_template()
    body = pn.Column("# Projects", pn.pane.Markdown("Manage your projects here."))
    # template.main[:] = [body]
    template.main.append(body)
    return template
    # return body

def get_processing():
    # template = get_panel_template()
    # body = pn.Column("# Processing", pn.pane.Markdown("Run image processing tasks."))
    # template.main[:] = [body]
    # return body
    template = pn.template.VanillaTemplate(
        title="Processing",
        main=[pn.Column("# Processing", pn.pane.Markdown("Run image processing tasks."))],
        # sidebar=sidebar,
    )
    return template

def get_maps():
    template = get_panel_template()
    body = pn.Column("# Map", pn.pane.Markdown("View geospatial data and waypoints."))
    # template.main[:] = [body]
    # return template

    # pn.state.add_periodic_callback()

    def cleanup(session_context):
        session_id = session_context.id
        print(f"🧹 Cleaning up session: {session_id}")

        # Remove the session from Bokeh's storage
        if session_id in pn.state.curdoc.session_context:
            del pn.state.curdoc.session_context[session_id]

    # Register cleanup function to remove session on exit
    pn.state.curdoc.on_session_destroyed(cleanup)
    # pn.state.curdoc.
    print(f"📝 Session Context at Init: {pn.state.curdoc.session_context.id}")

    return body

  

# Run as a standalone Panel server (optional, for testing Panel separately)
if __name__ == "__main__":
    # create_panel_app().servable()
    print("NO. Removed this. Go back and fill in.")
