"""armverse: automatic rhythm (syllable-group) analysis of Armenian verse."""

from .phonology import analyze_word, is_classical
from .scan import analyze_line
from .meter import scan_poem, fmt

__all__ = ["analyze_word", "analyze_line", "scan_poem", "fmt", "is_classical"]
