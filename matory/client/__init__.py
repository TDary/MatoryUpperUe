"""Protocol and connection layer."""

__all__ = ["Cmd", "Method", "Key", "Button", "encode_request", "decode_response", "Connection"]


def __getattr__(name):
    """Lazy imports — dependent modules may not exist yet during early scaffolding."""
    _imports = {
        "Cmd": "matory.client.protocol",
        "Method": "matory.client.protocol",
        "Key": "matory.client.protocol",
        "Button": "matory.client.protocol",
        "encode_request": "matory.client.protocol",
        "decode_response": "matory.client.protocol",
        "Connection": "matory.client.connection",
    }
    if name in _imports:
        import importlib
        module = importlib.import_module(_imports[name])
        return getattr(module, name)
    raise AttributeError(f"module 'matory.client' has no attribute {name!r}")
