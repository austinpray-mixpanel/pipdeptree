from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Final

from pipdeptree._models import ReversedPackageDAG

if TYPE_CHECKING:
    from pipdeptree._models import PackageDAG

_RESERVED_IDS: Final[frozenset[str]] = frozenset(
    [
        "C4Component",
        "C4Container",
        "C4Deployment",
        "C4Dynamic",
        "_blank",
        "_parent",
        "_self",
        "_top",
        "call",
        "class",
        "classDef",
        "click",
        "end",
        "flowchart",
        "flowchart-v2",
        "graph",
        "interpolate",
        "linkStyle",
        "style",
        "subgraph",
    ],
)


def render_mermaid(tree: PackageDAG) -> str:  # noqa: C901
    """
    Produce a Mermaid flowchart from the dependency graph.

    :param tree: dependency graph
    """
    # List of reserved keywords in Mermaid that cannot be used as node names.
    # See: https://github.com/mermaid-js/mermaid/issues/4182#issuecomment-1454787806

    node_ids_map: dict[str, str] = {}

    def mermaid_id(key: str) -> str:
        """Returns a valid Mermaid node ID from a string."""
        # If we have already seen this key, return the canonical ID.
        canonical_id = node_ids_map.get(key)
        if canonical_id is not None:
            return canonical_id
        # If the key is not a reserved keyword, return it as is, and update the map.
        if key not in _RESERVED_IDS:
            node_ids_map[key] = key
            return key
        # If the key is a reserved keyword, append a number to it.
        number = 0
        while True:
            new_id = f"{key}_{number}"
            if new_id not in node_ids_map:
                node_ids_map[key] = new_id
                return new_id
            number += 1

    # Use a sets to avoid duplicate entries.
    nodes: set[str] = set()
    edges: set[str] = set()

    if isinstance(tree, ReversedPackageDAG):
        for package, reverse_dependencies in tree.items():
            package_label = "\\n".join(
                (package.project_name, "(missing)" if package.is_missing else package.installed_version),
            )
            package_key = mermaid_id(package.key)
            nodes.add(f'{package_key}["{package_label}"]')
            for reverse_dependency in reverse_dependencies:
                edge_label = reverse_dependency.req.version_spec or "any"
                reverse_dependency_key = mermaid_id(reverse_dependency.key)
                edges.add(f'{package_key} -- "{edge_label}" --> {reverse_dependency_key}')
    else:
        for package, dependencies in tree.items():
            package_label = f"{package.project_name}\\n{package.version}"
            package_key = mermaid_id(package.key)
            nodes.add(f'{package_key}["{package_label}"]')
            for dependency in dependencies:
                edge_label = dependency.version_spec or "any"
                dependency_key = mermaid_id(dependency.key)
                if dependency.is_missing:
                    dependency_label = f"{dependency.project_name}\\n(missing)"
                    nodes.add(f'{dependency_key}["{dependency_label}"]:::missing')
                    edges.add(f"{package_key} -.-> {dependency_key}")
                else:
                    edges.add(f'{package_key} -- "{edge_label}" --> {dependency_key}')

    # Produce the Mermaid Markdown.
    indent = " " * 4
    output = dedent(
        f"""\
        flowchart TD
        {indent}classDef missing stroke-dasharray: 5
        """,
    )
    # Sort the nodes and edges to make the output deterministic.
    output += indent
    output += f"\n{indent}".join(node for node in sorted(nodes))
    output += "\n" + indent
    output += f"\n{indent}".join(edge for edge in sorted(edges))
    output += "\n"
    return output


__all__ = [
    "render_mermaid",
]