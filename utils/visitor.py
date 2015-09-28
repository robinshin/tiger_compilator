# This visitor pattern implementation has been found on Stack Overflow and
# enhanced by using a default case (use None).
__author__ = 'Joren Van Severen & Samuel Tardieu'

def _qualname(obj):
    """Get the fully-qualified name of an object (including module)."""
    return obj.__module__ + '.' + obj.__qualname__

def _declaring_class(obj):
    """Get the name of the class that declared an object."""
    name = _qualname(obj)
    return name[:name.rfind('.')]

# Stores the actual visitor methods
_methods = {}

# Delegating visitor implementation
def _visitor_impl(self, arg):
    """Actual visitor method implementation. None means default."""
    method = _methods.get((_qualname(type(self)), type(arg)), None)
    method = method if method is not None else _methods.get((_qualname(type(self)), None), None)
    return method(self, arg) if method is not None else None

# The actual @visitor decorator
def visitor(arg_type):
    """Decorator that creates a visitor method."""

    def decorator(fn):
        declaring_class = _declaring_class(fn)
        _methods[(declaring_class, arg_type)] = fn

        # Replace all decorated methods with _visitor_impl
        return _visitor_impl

    return decorator

# An abstract visitor type that lets you visit children easily
class Visitor:

    def visit_all(self, children):
        """Visit all children in turn unless they are None and return the list of results."""
        return [x.accept(self) for x in children]
