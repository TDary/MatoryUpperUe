"""Widget element model layer."""

__all__ = ["Widget", "ButtonWidget", "TextWidget"]


def __getattr__(name):
    """Lazy imports — dependent modules may not exist yet during early scaffolding."""
    _imports = {
        "Widget": "matory.elements.widget",
        "ButtonWidget": "matory.elements.button",
        "TextWidget": "matory.elements.text",
    }
    if name in _imports:
        import importlib
        module = importlib.import_module(_imports[name])
        return getattr(module, name)
    raise AttributeError(f"module 'matory.elements' has no attribute {name!r}")
