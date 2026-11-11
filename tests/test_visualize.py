"""РўРµСЃС‚С‹ РґР»СЏ РјРѕРґСѓР»СЏ РІРёР·СѓР°Р»РёР·Р°С†РёРё."""

import pytest

from src.graph import DependencyGraph
from src.visualize import VisualizeError, generate_ascii_tree, generate_d2_code


def _make_graph() -> DependencyGraph:
    """РЎРѕР·РґР°С‘С‚ С‚РµСЃС‚РѕРІС‹Р№ РіСЂР°С„."""
    graph = DependencyGraph()
    graph.add_node("A", "1.0")
    graph.add_node("B", "1.0")
    graph.add_node("C", "1.0")
    graph.add_edge("A", "B")
    graph.add_edge("A", "C")
    graph.add_edge("B", "C")
    return graph


class TestGenerateD2:
    """РўРµСЃС‚С‹ РіРµРЅРµСЂР°С†РёРё РєРѕРґР° D2."""

    def test_d2_code_contains_edges(self) -> None:
        """Р’ D2-РєРѕРґРµ РµСЃС‚СЊ РІСЃРµ СЃРІСЏР·Рё."""
        graph = _make_graph()
        code = generate_d2_code(graph)
        assert '"A" -> "B"' in code
        assert '"A" -> "C"' in code
        assert '"B" -> "C"' in code

    def test_d2_direction(self) -> None:
        """Р—Р°РґР°РЅРѕ РЅР°РїСЂР°РІР»РµРЅРёРµ РіСЂР°С„Р°."""
        graph = _make_graph()
        code = generate_d2_code(graph)
        assert "direction: right" in code


class TestAsciiTree:
    """РўРµСЃС‚С‹ ASCII-РґРµСЂРµРІР°."""

    def test_tree_root_present(self) -> None:
        """РљРѕСЂРµРЅСЊ РїСЂРёСЃСѓС‚СЃС‚РІСѓРµС‚ РІ РґРµСЂРµРІРµ."""
        graph = _make_graph()
        tree = generate_ascii_tree(graph, "A")
        assert tree.startswith("A")

    def test_tree_children_present(self) -> None:
        """Р”РѕС‡РµСЂРЅРёРµ СѓР·Р»С‹ РїСЂРёСЃСѓС‚СЃС‚РІСѓСЋС‚."""
        graph = _make_graph()
        tree = generate_ascii_tree(graph, "A")
        assert "B" in tree
        assert "C" in tree

    def test_missing_root(self) -> None:
        """РќРµСЃСѓС‰РµСЃС‚РІСѓСЋС‰РёР№ РєРѕСЂРµРЅСЊ вЂ” РѕС€РёР±РєР°."""
        graph = _make_graph()
        with pytest.raises(VisualizeError):
            generate_ascii_tree(graph, "Missing")
