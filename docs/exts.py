def setup(app):
    app.add_crossref_type(
        directivename="admin",
        rolename="admin",
        indextemplate="pair: %s; admin",
    )
    app.add_crossref_type(
        directivename="command",
        rolename="command",
        indextemplate="pair: %s; command",
    )
    app.add_crossref_type(
        directivename="form",
        rolename="form",
        indextemplate="pair: %s; form",
    )
    app.add_crossref_type(
        directivename="manager",
        rolename="manager",
        indextemplate="pair: %s; manager",
    )
    app.add_crossref_type(
        directivename="mixin",
        rolename="mixin",
        indextemplate="pair: %s; mixin",
    )
    app.add_crossref_type(
        directivename="model",
        rolename="model",
        indextemplate="pair: %s; model",
    )
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )
    app.add_crossref_type(
        directivename="shortcut",
        rolename="shortcut",
        indextemplate="pair: %s; shortcut",
    )
