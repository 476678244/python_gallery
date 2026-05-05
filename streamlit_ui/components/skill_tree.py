"""Skill Tree Component - Tree-structured skill management with enable/disable controls"""

import streamlit as st
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from streamlit_ui.safe_claw.core.skills.scanner import get_skill_scanner, SkillIndexEntry
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class SkillTreeNode:
    """Node in the skill tree"""
    name: str
    path: str  # Relative path from skills root
    is_folder: bool
    skill_entry: Optional[SkillIndexEntry] = None
    children: List["SkillTreeNode"] = field(default_factory=lambda: [])
    enabled: bool = True
    expanded: bool = False
    node_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])  # Unique identifier for widget keys
    
    def __post_init__(self):
        """Ensure children is always a list"""
        if self.children is None:
            self.children = []


def build_skill_tree(
    base_path: Path,
    enabled_skills: Optional[Set[str]] = None,
) -> List[SkillTreeNode]:
    """Build skill tree from filesystem structure for a single base path
    
    Args:
        base_path: Root skills directory
        enabled_skills: Set of skill names that are enabled (None = all enabled)
        
    Returns:
        List of root nodes (usually category folders)
    """
    if enabled_skills is None:
        enabled_skills = set()
    
    # Ensure base_path is absolute
    base_path = base_path.resolve()
        
    scanner = get_skill_scanner()
    if not scanner.loaded:
        scanner.scan_all_skills()
    
    # Build a map of path -> node
    path_to_node: Dict[str, SkillTreeNode] = {}
    root_nodes: List[SkillTreeNode] = []
    
    # First pass: create nodes for all directories containing skills
    for skill_name, entry in scanner.index.items():
        skill_path = Path(entry.path).resolve()
        
        # Check if skill is under base_path
        try:
            rel_path = skill_path.relative_to(base_path)
        except ValueError:
            # Skill not under base_path, skip
            continue
            
        # Build folder hierarchy
        current_path = base_path
        parent_node = None
        
        for part in rel_path.parts[:-1]:  # Exclude the skill folder itself
            current_path = current_path / part
            path_key = str(current_path)
            
            if path_key not in path_to_node:
                # Create folder node - folders start enabled
                node = SkillTreeNode(
                    name=part,
                    path=str(current_path.relative_to(base_path)),
                    is_folder=True,
                    enabled=True,
                    expanded=False
                )
                path_to_node[path_key] = node
                
                if parent_node:
                    parent_node.children.append(node)
                else:
                    root_nodes.append(node)
                    
            parent_node = path_to_node[path_key]
        
        # Create skill node (leaf) - only enabled if in enabled_skills set
        is_enabled = skill_name in enabled_skills if enabled_skills else True
            
        skill_node = SkillTreeNode(
            name=skill_name,
            path=str(rel_path),
            is_folder=False,
            skill_entry=entry,
            enabled=is_enabled,
            expanded=False
        )
        
        if parent_node:
            parent_node.children.append(skill_node)
        else:
            root_nodes.append(skill_node)
    
    # Sort nodes: folders first, then alphabetically
    def sort_nodes(nodes: List[SkillTreeNode]) -> List[SkillTreeNode]:
        sorted_nodes = sorted(nodes, key=lambda n: (not n.is_folder, n.name.lower()))
        for node in sorted_nodes:
            if node.children:
                node.children = sort_nodes(node.children)
        return sorted_nodes
    
    return sort_nodes(root_nodes)


# Directories and files to ignore during skill scanning
IGNORE_PATTERNS = {
    "__pycache__", ".git", ".idea", ".DS_Store", ".pytest_cache", ".venv",
    "node_modules", ".vscode", "__init__.py", ".env", ".gitignore",
    "*.pyc", "*.pyo", "*.egg-info", ".mypy_cache", ".tox", "dist", "build"
}


def _should_ignore_skill(skill_name: str) -> bool:
    """Check if a skill/directory should be ignored"""
    if skill_name in IGNORE_PATTERNS:
        return True
    if skill_name.startswith(".") or skill_name.startswith("__"):
        return True
    if skill_name.endswith(".pyc") or skill_name.endswith(".pyo"):
        return True
    return False


def _resolve_skill_collection(skill_name: str, skill_path: Path, parts: tuple) -> tuple:
    """Resolve skill collection using robust path inference
    
    Supports multiple directory structures:
    1. built_in/<skill> -> collection="built_in"
    2. linked_skills/<collection>/<skill> -> collection=<collection>
    3. streamlit_ui/skills/<collection>/<skill> -> collection=<collection>
    4. */skills/<skill> -> collection="custom" (fallback for standalone repos)
    
    Returns: (collection_name, collection_path) or (None, None) if unresolved
    """
    path_str = str(skill_path)
    
    # Pattern 1: built_in skills
    if "built_in" in path_str or "built-in" in path_str:
        for i, part in enumerate(parts):
            if part in ["built_in", "built-in"]:
                collection_path = Path(*parts[:i+1])
                logger.info(f"[SkillTree]   -> built_in collection")
                return ("built_in", collection_path)
    
    # Pattern 2: linked_skills/<collection>/<skill>
    for i, part in enumerate(parts):
        if part == "linked_skills":
            if i + 1 < len(parts):
                collection_name = parts[i + 1]  # e.g., "ljg-skills", "superpowers_skills"
                collection_path = Path(*parts[:i+2])
                logger.info(f"[SkillTree]   -> {collection_name} (linked_skills)")
                return (collection_name, collection_path)
    
    # Pattern 3: streamlit_ui/skills/<collection>/<skill>
    for i, part in enumerate(parts):
        if part == "skills" and i > 0 and parts[i-1] == "streamlit_ui":
            if i + 1 < len(parts):
                collection_name = parts[i + 1]  # e.g., "private_skills"
                collection_path = Path(*parts[:i+2])
                logger.info(f"[SkillTree]   -> {collection_name} (streamlit_ui/skills)")
                return (collection_name, collection_path)
    
    # Pattern 4: */skills/<skill> (standalone repo with skills/ subdirectory)
    # Auto-assign to "custom" collection
    for i, part in enumerate(parts):
        if part == "skills":
            if i + 1 < len(parts):
                # Check if the parent directory looks like a repo name
                if i > 0:
                    repo_name = parts[i-1]  # e.g., "ljg-skills" from .../ljg-skills/skills/xxx
                    collection_name = f"{repo_name}-skills"
                else:
                    collection_name = "custom"
                collection_path = Path(*parts[:i+1])
                logger.info(f"[SkillTree]   -> {collection_name} (standalone repo, skills/)")
                return (collection_name, collection_path)
    
    # Pattern 5: Last resort - use parent directory name as collection
    if len(parts) >= 2:
        parent_name = parts[-2]  # parent directory of the skill
        if parent_name not in ["skills", "linked_skills", "streamlit_ui"]:
            collection_path = Path(*parts[:-1])  # parent directory
            logger.info(f"[SkillTree]   -> {parent_name} (parent directory fallback)")
            return (parent_name, collection_path)
    
    # Unresolvable
    return (None, None)


def build_complete_skill_tree(
    root_name: str = "All Skills",
    enabled_skills: Optional[Set[str]] = None,
) -> SkillTreeNode:
    """Build complete skill tree from scanner
    
    Skills are grouped by their collection folder:
    - ljg-skills/ (under linked_skills)
    - superpowers_skills/ (under linked_skills)  
    - private_skills/ (under streamlit_ui/skills)
    - built_in/
    
    Args:
        root_name: Name for the virtual root node
        enabled_skills: Set of skill names that are enabled (None = all enabled)
        
    Returns:
        Root node containing all skill collections
    """
    if enabled_skills is None:
        enabled_skills = set()
        
    scanner = get_skill_scanner()
    if not scanner.loaded:
        scanner.scan_all_skills()
    
    # Create virtual root
    root = SkillTreeNode(
        name=root_name,
        path="",
        is_folder=True,
        enabled=True,
        expanded=False
    )
    
    # Map: collection_name -> SkillTreeNode
    collections: Dict[str, SkillTreeNode] = {}
    
    # Process each skill
    for skill_name, entry in scanner.index.items():
        skill_path = Path(entry.path).resolve()
        path_str = str(skill_path)
        parts = skill_path.parts
        
        # DEBUG: Log the actual path we're processing
        logger.info(f"[SkillTree] Processing skill '{skill_name}' at path: {path_str}")
        
        # Find the collection folder name using robust inference
        collection_name, collection_path = _resolve_skill_collection(skill_name, skill_path, parts)
        
        if not collection_name or not collection_path:
            raise ValueError(
                f"[SkillTree] Cannot determine collection for skill '{skill_name}'\n"
                f"  Path: {path_str}\n"
                f"  Tried: built_in, linked_skills/*, streamlit_ui/skills/*, */skills/*"
            )
        
        # Create collection node if not exists
        if collection_name not in collections:
            collection_node = SkillTreeNode(
                name=collection_name,
                path=collection_name,
                is_folder=True,
                enabled=True,
                expanded=False
            )
            collections[collection_name] = collection_node
            root.children.append(collection_node)
        
        collection_node = collections[collection_name]
        
        # Get relative path from collection_path
        try:
            rel_path = skill_path.relative_to(collection_path)
        except ValueError:
            rel_path = Path(skill_path.name)
        
        # Build folder hierarchy under collection
        path_to_node: Dict[str, SkillTreeNode] = {}
        current_path = collection_path
        parent_node = collection_node
        
        for part in rel_path.parts[:-1]:  # Exclude the skill folder itself
            current_path = current_path / part
            path_key = f"{collection_name}:{part}"
            
            if path_key not in path_to_node:
                node = SkillTreeNode(
                    name=part,
                    path=path_key,
                    is_folder=True,
                    enabled=True,
                    expanded=False
                )
                path_to_node[path_key] = node
                parent_node.children.append(node)
                    
            parent_node = path_to_node[path_key]
        
        # Create skill node (leaf) - only enabled if in enabled_skills set
        is_enabled = skill_name in enabled_skills if enabled_skills else True
            
        skill_node = SkillTreeNode(
            name=skill_name,
            path=str(rel_path),
            is_folder=False,
            skill_entry=entry,
            enabled=is_enabled,
            expanded=False
        )
        
        parent_node.children.append(skill_node)
    
    # Sort all children recursively
    def sort_nodes(node: SkillTreeNode):
        node.children = sorted(node.children, key=lambda n: (not n.is_folder, n.name.lower()))
        for child in node.children:
            if child.children:
                sort_nodes(child)
    
    sort_nodes(root)
    
    # Remove empty collection nodes
    root.children = [c for c in root.children if c.children]
    
    return root


def count_skills_in_node(node: SkillTreeNode) -> int:
    """Count total skills (non-folder nodes) under a node"""
    if not node.is_folder:
        return 1
    return sum(count_skills_in_node(child) for child in node.children)


def count_enabled_skills(node: SkillTreeNode) -> int:
    """Count enabled skills under a node"""
    if not node.is_folder:
        return 1 if node.enabled else 0
    return sum(count_enabled_skills(child) for child in node.children)


def set_node_enabled(node: SkillTreeNode, enabled: bool, recursive: bool = True):
    """Set enabled state for a node
    
    Args:
        node: The node to update
        enabled: New enabled state
        recursive: If True, also update all children
    """
    node.enabled = enabled
    
    if recursive and node.children:
        for child in node.children:
            set_node_enabled(child, enabled, recursive=True)


def collect_enabled_skills(nodes) -> Set[str]:
    """Collect all enabled skill names from tree
    
    Args:
        nodes: Either a single SkillTreeNode or a list of SkillTreeNode
        
    Returns:
        Set of enabled skill names
    """
    enabled = set()
    
    # Handle single node
    if isinstance(nodes, SkillTreeNode):
        nodes = [nodes]
    
    def traverse(node: SkillTreeNode):
        if not node.is_folder and node.enabled:
            enabled.add(node.name)
        for child in node.children:
            traverse(child)
    
    for node in nodes:
        traverse(node)
    
    return enabled


def collect_disabled_folders(nodes) -> Set[str]:
    """Collect all disabled folder paths from tree
    
    Args:
        nodes: Either a single SkillTreeNode or a list of SkillTreeNode
        
    Returns:
        Set of disabled folder paths
    """
    disabled = set()
    
    # Handle single node
    if isinstance(nodes, SkillTreeNode):
        nodes = [nodes]
    
    def traverse(node: SkillTreeNode):
        if node.is_folder and not node.enabled:
            disabled.add(str(node.path))
        for child in node.children:
            traverse(child)
    
    for node in nodes:
        traverse(node)
    
    return disabled


def collect_disabled_folders_from_root(root: SkillTreeNode) -> Set[str]:
    """Collect all disabled folder paths from a single root node"""
    disabled = set()
    
    def traverse(node: SkillTreeNode):
        if node.is_folder and not node.enabled:
            disabled.add(str(node.path))
        for child in node.children:
            traverse(child)
    
    traverse(root)
    return disabled


def render_skill_tree(
    nodes: List[SkillTreeNode],
    level: int = 0,
    parent_enabled: bool = True,
    parent_path: str = ""
) -> List[SkillTreeNode]:
    """Render skill tree nodes recursively using Streamlit
    
    Args:
        nodes: List of nodes to render
        level: Current indentation level
        parent_enabled: Whether parent folder is enabled
        parent_path: Path of parent node for unique key generation
        
    Returns:
        Updated nodes with new states
    """
    # Ensure nodes is a list
    if nodes is None:
        nodes = []
    elif isinstance(nodes, SkillTreeNode):
        # If a single node was passed, wrap it in a list
        nodes = [nodes]
    
    updated_nodes = []
    
    for node in nodes:
        # Calculate indentation - use level to shift columns for visual tree structure
        indent_width = level * 0.8  # Each level adds 0.8 width for indentation
        base_col1_width = 0.6
        base_col2_width = 3
        base_col3_width = 1
        
        # Generate unique key using node.path with node_id for guaranteed uniqueness
        # node_id is generated once when node is created and persists with the node
        path_key = node.path.replace('/', '_').replace('\\', '_').replace('.', '_').replace(':', '_')
        unique_key = f"{path_key}_{node.node_id}"
        
        # Create columns with indentation - level 0 has no indent columns
        if level > 0:
            # Add empty columns for indentation
            indent_cols = st.columns([indent_width, base_col1_width, base_col2_width, base_col3_width])
            icon_col = indent_cols[1]
            name_col = indent_cols[2]
            toggle_col = indent_cols[3]
        else:
            cols = st.columns([base_col1_width, base_col2_width, base_col3_width])
            icon_col = cols[0]
            name_col = cols[1]
            toggle_col = cols[2]
        
        if node.is_folder:
            # Folder node with expand/collapse and toggle - compact display
            total_skills = count_skills_in_node(node)
            enabled_count = count_enabled_skills(node)

            with icon_col:
                # Expand/collapse button
                icon = "📂" if node.expanded else "📁"
                if st.button(
                    icon,
                    key=f"toggle_{unique_key}_{level}",
                    help=f"Expand/collapse ({enabled_count}/{total_skills} enabled)",
                    use_container_width=True
                ):
                    node.expanded = not node.expanded
                    st.rerun()

            with name_col:
                # Compact: name and count on same line
                folder_name = f"**{node.name}** <span style='color: #888; font-size: 0.75em;'>({enabled_count}/{total_skills})</span>"
                st.markdown(folder_name, unsafe_allow_html=True)

            with toggle_col:
                # Folder-level toggle (enables/disables all children)
                new_enabled = st.toggle(
                    "Enable",
                    value=node.enabled and parent_enabled,
                    key=f"folder_{unique_key}_{level}",
                    disabled=not parent_enabled,
                    label_visibility="collapsed"
                )
                
                # Update state if changed
                if new_enabled != node.enabled:
                    set_node_enabled(node, new_enabled, recursive=True)
                    st.rerun()
            
            # Render children if expanded
            if node.expanded:
                # Pass node.path as parent_path for children (not full_path) to avoid duplication
                # since children already have collection:path format in their node.path
                node.children = render_skill_tree(
                    node.children,
                    level + 1,
                    parent_enabled=node.enabled and parent_enabled,
                    parent_path=node.path
                )
        else:
            # Skill node (leaf) - compact single row
            with icon_col:
                st.markdown("🔧", unsafe_allow_html=True)

            with name_col:
                skill_name = node.name
                description = ""
                if node.skill_entry:
                    description = node.skill_entry.description[:40] + "..." if len(node.skill_entry.description) > 40 else node.skill_entry.description

                # Compact display: name and description on same line
                if description:
                    display_text = f"**{skill_name}** <span style='color: #888; font-size: 0.75em;'>| {description}</span>"
                else:
                    display_text = f"**{skill_name}**"
                st.markdown(display_text, unsafe_allow_html=True)

            with toggle_col:
                new_enabled = st.toggle(
                    "Enable",
                    value=node.enabled and parent_enabled,
                    key=f"skill_{unique_key}_{level}",
                    disabled=not parent_enabled,
                    label_visibility="collapsed"
                )

                if new_enabled != node.enabled:
                    node.enabled = new_enabled
                    st.rerun()
        
        updated_nodes.append(node)
    
    return updated_nodes


def render_skill_tree_component(
    base_path: Optional[Path] = None,
    session_state_key: str = "skill_tree_state",
    use_complete_tree: bool = True
):
    """Main component for skill tree management
    
    Args:
        base_path: Root skills directory (defaults to private_skills, only used if use_complete_tree=False)
        session_state_key: Key for storing state in st.session_state
        use_complete_tree: If True, shows all skills from all sources (private, linked, public, built-in)
    """
    st.subheader("🌳 Skill Tree")
    
    # Initialize base path (legacy support)
    if base_path is None:
        base_path = Path(__file__).parent.parent.parent / "skills" / "private_skills"
    
    # Get enabled skills from SkillsManager if available (backend owns state)
    skills_manager_enabled = None
    if "skills_manager" in st.session_state:
        skills_manager = st.session_state["skills_manager"]
        skills_manager_enabled = skills_manager.get_enabled_skills_state()
        if skills_manager_enabled is not None:
            logger.info(f"Loaded {len(skills_manager_enabled)} enabled skills from SkillsManager")
    
    # Initialize session state
    if session_state_key not in st.session_state:
        st.session_state[session_state_key] = {
            "enabled_skills": skills_manager_enabled if skills_manager_enabled else set(),
            "tree": None,
            "use_complete_tree": use_complete_tree
        }
    
    state = st.session_state[session_state_key]
    
    # Sync with SkillsManager state if changed
    if skills_manager_enabled is not None and skills_manager_enabled != state.get("enabled_skills"):
        state["enabled_skills"] = skills_manager_enabled
        state["tree"] = None  # Force rebuild with new state
    
    # Check if we need to rebuild tree (format changed or first run)
    previous_format = state.get("use_complete_tree", None)
    if previous_format != use_complete_tree:
        state["tree"] = None  # Force rebuild
        state["use_complete_tree"] = use_complete_tree
    
    # Build or rebuild tree
    if state["tree"] is None:
        if use_complete_tree:
            # Build complete tree with all skill sources
            state["tree"] = build_complete_skill_tree(
                enabled_skills=state["enabled_skills"] if state["enabled_skills"] else None
            )
        else:
            # Legacy: build tree for single base path
            state["tree"] = build_skill_tree(
                base_path,
                enabled_skills=state["enabled_skills"] if state["enabled_skills"] else None
            )
    
    # Summary stats
    if isinstance(state["tree"], list):
        total_skills = sum(count_skills_in_node(node) for node in state["tree"])
        enabled_skills = sum(count_enabled_skills(node) for node in state["tree"])
    else:
        total_skills = count_skills_in_node(state["tree"])
        enabled_skills = count_enabled_skills(state["tree"])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Skills", total_skills)
    with col2:
        st.metric("Enabled", enabled_skills)
    with col3:
        st.metric("Disabled", total_skills - enabled_skills)
    
    st.divider()
    
    # Render tree
    if state["tree"]:
        with st.container():
            st.markdown("""
                <style>
                .stColumn {
                    padding: 0px !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            # Handle both single root node and list of nodes
            if isinstance(state["tree"], list):
                state["tree"] = render_skill_tree(state["tree"], parent_path="root")
            else:
                # Single root node - render its children
                # Ensure children is a list
                if not hasattr(state["tree"], 'children') or state["tree"].children is None:
                    state["tree"].children = []
                state["tree"].children = render_skill_tree(state["tree"].children, level=0, parent_path=state["tree"].path or "root")
    else:
        st.info("No skills found in the configured directory.")
    
    # Sync enabled skills to SkillsManager (backend owns state)
    if state.get("tree"):
        if isinstance(state["tree"], list):
            current_enabled = set()
            for node in state["tree"]:
                current_enabled.update(collect_enabled_skills(node))
        else:
            current_enabled = collect_enabled_skills(state["tree"])
        
        # Sync to SkillsManager and save preferences if changed
        if current_enabled != state.get("enabled_skills"):
            state["enabled_skills"] = current_enabled
            
            # Update SkillsManager (backend state)
            if "skills_manager" in st.session_state:
                st.session_state["skills_manager"].set_enabled_skills(list(current_enabled))
                logger.info(f"Synced {len(current_enabled)} enabled skills to SkillsManager")
            
            # Save to user preferences for persistence
            try:
                import sys
                project_root = Path(__file__).parent.parent
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                from streamlit_ui.app import save_skill_tree_preferences
                save_skill_tree_preferences(current_enabled)
            except Exception as e:
                logger.debug(f"Failed to auto-save skill tree preferences: {e}")
    
    # Export current configuration
    st.divider()
    with st.expander("📤 Export Configuration"):
        if isinstance(state["tree"], list):
            current_enabled = set()
            for node in state["tree"]:
                current_enabled.update(collect_enabled_skills(node))
        else:
            # Single root node
            current_enabled = collect_enabled_skills(state["tree"])
        
        config = {
            "enabled_skills": sorted(list(current_enabled)),
            "base_path": str(base_path) if base_path else ""
        }
        
        st.json(config)
        
        import json
        st.download_button(
            "Download Config",
            data=json.dumps(config, indent=2),
            file_name="skill_tree_config.json",
            mime="application/json",
            use_container_width=True
        )


def get_enabled_skills_from_tree(session_state_key: str = "skill_tree_state") -> List[str]:
    """Get list of enabled skill names from SkillsManager (backend owns state)
    
    Args:
        session_state_key: Key used in session state (kept for API compatibility)
        
    Returns:
        List of enabled skill names
    """
    # Get from SkillsManager (backend owns state)
    if "skills_manager" in st.session_state:
        skills_manager = st.session_state["skills_manager"]
        return skills_manager.get_enabled_skills()
    
    # Fallback: try session state (for when SkillsManager not yet initialized)
    if session_state_key in st.session_state:
        state = st.session_state[session_state_key]
        if state.get("tree"):
            tree = state["tree"]
            if isinstance(tree, list):
                enabled = set()
                for node in tree:
                    enabled.update(collect_enabled_skills(node))
                return list(enabled)
            else:
                return list(collect_enabled_skills(tree))
        return list(state.get("enabled_skills", []))
    
    return []


def is_skill_enabled(skill_name: str, session_state_key: str = "skill_tree_state") -> bool:
    """Check if a specific skill is enabled in the tree
    
    Args:
        skill_name: Name of the skill to check
        session_state_key: Key used in session state
        
    Returns:
        True if skill is enabled, False otherwise
    """
    enabled_skills = get_enabled_skills_from_tree(session_state_key)
    return skill_name in enabled_skills
