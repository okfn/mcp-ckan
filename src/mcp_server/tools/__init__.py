"""Server-level (core) tools, registered on every instance regardless of
which plugins it loads. Each module exposes a ``register_core_tools`` (or
similarly named) function that ``server.py`` wires up under the ``core``
namespace.
"""
