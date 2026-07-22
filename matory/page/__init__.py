"""Page Object pattern layer."""

__all__ = ["Page", "WidgetDescriptor"]


def __getattr__(name):
    """Lazy imports — dependent modules may not exist yet during early scaffolding."""
    _imports = {
        "Page": "matory.page.page",
        "WidgetDescriptor": "matory.page.page",
    }
    if name in _imports:
        import importlib
        module = importlib.import_module(_imports[name])
        return getattr(module, name)
    raise AttributeError(f"module 'matory.page' has no attribute {name!r}")
