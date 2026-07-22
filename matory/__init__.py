"""Matory — UE UI automation framework."""

__all__ = [
    "MatoryError",
    "CommandError",
    "Session",
    "Widget",
    "ButtonWidget",
    "TextWidget",
    "Page",
    "WidgetDescriptor",
]


def __getattr__(name):
    """Lazy imports — dependent modules may not exist yet during early scaffolding."""
    _imports = {
        "MatoryError": "matory.errors",
        "CommandError": "matory.errors",
        "Session": "matory.session",
        "Widget": "matory.elements.widget",
        "ButtonWidget": "matory.elements.button",
        "TextWidget": "matory.elements.text",
        "Page": "matory.page.page",
        "WidgetDescriptor": "matory.page.page",
    }
    if name in _imports:
        import importlib
        module = importlib.import_module(_imports[name])
        return getattr(module, name)
    raise AttributeError(f"module 'matory' has no attribute {name!r}")
