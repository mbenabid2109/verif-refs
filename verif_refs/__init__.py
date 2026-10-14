"""verif-refs : audit de références bibliographiques."""

__version__ = "5.2.0"

try:                       # `adk web` charge la chaîne d'agents par ce module
    from . import agent    # noqa: F401
except ImportError:        # ADK absent : seule la ligne de commande est disponible
    pass
