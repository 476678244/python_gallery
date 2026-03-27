"""Memory browser component for SafeClaw"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from safe_claw.models.memory import Memory, MemoryLayer

def render_memory_browser(memory_manager, show_controls: bool = True):
    """Render memory browser interface"""
    
    st.subheader("🧠 Memory Browser")
    
    # Get memory statistics
    stats = memory_manager.get_memory_stats()
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active", stats["active_count"], "🟢")
    with col2:
        st.metric("Dormant", stats["dormant_count"], "🟡")
    with col3:
        st.metric("Deep", stats["deep_count"], "🔵")
    with col4:
        st.metric("Forgotten", stats["forgotten_count"], "⚫")
    
    if show_controls:
        # Layer selection and controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected_layer = st.selectbox(
                "Select Memory Layer:",
                ["active", "dormant", "deep", "forgotten"],
                format_func=lambda x: x.capitalize()
            )
        
        with col2:
            refresh_btn = st.button("🔄 Refresh", key="refresh_memories")
        
        with col3:
            cleanup_btn = st.button("🧹 Cleanup", key="cleanup_memories")
        
        if cleanup_btn:
            with st.spinner("Cleaning up old memories..."):
                memory_manager.cleanup_old_memories()
                st.success("Memory cleanup completed!")
                st.rerun()
    
    # Search functionality
    st.subheader("🔍 Search Memories")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "Search memories:",
            placeholder="Enter keywords to search...",
            key="memory_search"
        )
    
    with col2:
        max_results = st.number_input(
            "Max Results:",
            min_value=5,
            max_value=100,
            value=20,
            step=5,
            key="max_results"
        )
    
    if search_query:
        with st.spinner("Searching memories..."):
            search_results = memory_manager.search_memories(search_query, max_results)
            render_search_results(search_results, search_query)
    
    # Memory layer browser
    st.subheader(f"📚 {selected_layer.capitalize()} Memories")
    
    # Get memories from selected layer
    memories = get_layer_memories(memory_manager, selected_layer)
    
    if memories:
        render_memory_table(memories, selected_layer)
        
        # Memory details
        if st.checkbox("Show Memory Details", key="show_memory_details"):
            render_memory_details(memories, memory_manager, selected_layer)
    else:
        st.info(f"No memories in {selected_layer} layer.")
    
    # Memory operations
    if show_controls and memories:
        st.subheader("⚙️ Memory Operations")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📤 Export Layer", key="export_layer"):
                export_memories(memories, selected_layer)
        
        with col2:
            if st.button("📊 Layer Statistics", key="layer_stats"):
                show_layer_statistics(memory_manager, selected_layer)
        
        with col3:
            if st.button("🔄 Promote/Demote", key="promote_demote"):
                show_promote_demote_interface(memory_manager, selected_layer)

def get_layer_memories(memory_manager, layer: str) -> List[Memory]:
    """Get memories from specific layer"""
    layer_map = {
        "active": memory_manager.active_layer,
        "dormant": memory_manager.dormant_layer,
        "deep": memory_manager.deep_layer,
        "forgotten": memory_manager.forgotten_layer
    }
    
    layer_obj = layer_map.get(layer)
    if layer_obj:
        return layer_obj.get_all_memories()
    return []

def render_search_results(results: List, query: str):
    """Render search results"""
    if results:
        st.success(f"Found {len(results)} memories matching '{query}'")
        
        for i, result in enumerate(results):
            with st.expander(f"📄 {result.memory.content[:100]}...", expanded=i == 0):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Content:** {result.memory.content}")
                    st.write(f"**Score:** {result.score:.3f}")
                    st.write(f"**Match Type:** {result.match_type}")
                
                with col2:
                    st.write(f"**Layer:** {result.memory.layer.value}")
                    st.write(f"**Importance:** {result.memory.importance_score:.2f}")
                    st.write(f"**Access Count:** {result.memory.access_count}")
    else:
        st.warning(f"No memories found matching '{query}'")

def render_memory_table(memories: List[Memory], layer: str):
    """Render memories in a table format"""
    
    # Prepare data for table
    memory_data = []
    for memory in memories:
        memory_data.append({
            "ID": memory.id[:8] + "...",
            "Content": memory.content[:80] + "..." if len(memory.content) > 80 else memory.content,
            "Importance": f"{memory.importance_score:.2f}",
            "Access Count": memory.access_count,
            "Created": memory.created_at.strftime("%Y-%m-%d %H:%M"),
            "Last Accessed": memory.accessed_at.strftime("%Y-%m-%d %H:%M"),
            "Keywords": ", ".join(memory.keywords[:3]) if memory.keywords else "None"
        })
    
    if memory_data:
        df = pd.DataFrame(memory_data)
        st.dataframe(df, width='stretch', hide_index=True)
        
        # Selection for detailed view
        st.subheader("📋 Select Memory for Details")
        selected_indices = st.multiselect(
            "Select memories to view details:",
            options=range(len(memories)),
            format_func=lambda x: f"Memory {x+1}: {memories[x].content[:50]}...",
            key="memory_selection"
        )
        
        return selected_indices
    return []

def render_memory_details(memories: List[Memory], memory_manager, layer: str):
    """Render detailed memory information"""
    
    selected_indices = st.session_state.get("memory_selection", [])
    
    if selected_indices:
        for idx in selected_indices:
            if idx < len(memories):
                memory = memories[idx]
                
                with st.expander(f"📄 {memory.content[:100]}...", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write("**Full Content:**")
                        st.text_area("", memory.content, height=100, key=f"content_{memory.id}", disabled=True)
                        
                        if memory.keywords:
                            st.write("**Keywords:**")
                            st.write(", ".join(memory.keywords))
                        
                        if memory.metadata:
                            st.write("**Metadata:**")
                            st.json(memory.metadata)
                    
                    with col2:
                        st.write("**Memory Information:**")
                        st.write(f"• **ID:** {memory.id}")
                        st.write(f"• **Layer:** {memory.layer.value}")
                        st.write(f"• **Importance:** {memory.importance_score:.3f}")
                        st.write(f"• **Access Count:** {memory.access_count}")
                        st.write(f"• **Created:** {memory.created_at}")
                        st.write(f"• **Last Accessed:** {memory.accessed_at}")
                        
                        # Memory operations
                        st.write("**Operations:**")
                        
                        if st.button(f"📝 Edit", key=f"edit_{memory.id}"):
                            edit_memory(memory, memory_manager)
                        
                        if st.button(f"🗑️ Delete", key=f"delete_{memory.id}"):
                            delete_memory(memory, memory_manager, layer)
                        
                        if st.button(f"📤 Export", key=f"export_{memory.id}"):
                            export_single_memory(memory)

def edit_memory(memory: Memory, memory_manager):
    """Edit memory content and metadata"""
    st.subheader(f"✏️ Edit Memory: {memory.id[:8]}...")
    
    # Edit content
    new_content = st.text_area(
        "Content:",
        value=memory.content,
        height=150,
        key=f"edit_content_{memory.id}"
    )
    
    # Edit importance
    new_importance = st.slider(
        "Importance Score:",
        min_value=0.0,
        max_value=1.0,
        value=memory.importance_score,
        step=0.1,
        key=f"edit_importance_{memory.id}"
    )
    
    # Edit keywords
    keywords_str = ", ".join(memory.keywords) if memory.keywords else ""
    new_keywords_str = st.text_input(
        "Keywords (comma-separated):",
        value=keywords_str,
        key=f"edit_keywords_{memory.id}"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Changes", key=f"save_{memory.id}"):
            # Update memory
            memory.content = new_content
            memory.importance_score = new_importance
            memory.keywords = [k.strip() for k in new_keywords_str.split(",") if k.strip()]
            
            # Save to layer
            layer_map = {
                MemoryLayer.ACTIVE: memory_manager.active_layer,
                MemoryLayer.DORMANT: memory_manager.dormant_layer,
                MemoryLayer.DEEP: memory_manager.deep_layer,
                MemoryLayer.FORGOTTEN: memory_manager.forgotten_layer
            }
            
            layer_obj = layer_map[memory.layer]
            layer_obj.update_memory(memory)
            
            st.success("Memory updated successfully!")
            st.rerun()
    
    with col2:
        if st.button("❌ Cancel", key=f"cancel_{memory.id}"):
            st.rerun()

def delete_memory(memory: Memory, memory_manager, layer: str):
    """Delete memory with confirmation"""
    st.warning(f"⚠️ Are you sure you want to delete this memory?")
    st.write(f"**Content:** {memory.content}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Yes, Delete", key=f"confirm_delete_{memory.id}"):
            # Remove from layer
            layer_map = {
                "active": memory_manager.active_layer,
                "dormant": memory_manager.dormant_layer,
                "deep": memory_manager.deep_layer,
                "forgotten": memory_manager.forgotten_layer
            }
            
            layer_obj = layer_map[layer]
            success = layer_obj.remove_memory(memory.id)
            
            if success:
                st.success("Memory deleted successfully!")
                st.rerun()
            else:
                st.error("Failed to delete memory.")
    
    with col2:
        if st.button("❌ Cancel", key=f"cancel_delete_{memory.id}"):
            st.rerun()

def export_memories(memories: List[Memory], layer: str):
    """Export memories to JSON"""
    export_data = {
        "layer": layer,
        "exported_at": datetime.now().isoformat(),
        "memories": [
            {
                "id": memory.id,
                "content": memory.content,
                "layer": memory.layer.value,
                "importance_score": memory.importance_score,
                "keywords": memory.keywords,
                "created_at": memory.created_at.isoformat(),
                "accessed_at": memory.accessed_at.isoformat(),
                "access_count": memory.access_count,
                "metadata": memory.metadata
            }
            for memory in memories
        ]
    }
    
    st.json(export_data)
    
    # Download button
    st.download_button(
        label="📥 Download JSON",
        data=st.json.dumps(export_data),
        file_name=f"memories_{layer}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def export_single_memory(memory: Memory):
    """Export single memory"""
    export_data = {
        "id": memory.id,
        "content": memory.content,
        "layer": memory.layer.value,
        "importance_score": memory.importance_score,
        "keywords": memory.keywords,
        "created_at": memory.created_at.isoformat(),
        "accessed_at": memory.accessed_at.isoformat(),
        "access_count": memory.access_count,
        "metadata": memory.metadata,
        "exported_at": datetime.now().isoformat()
    }
    
    st.json(export_data)
    
    st.download_button(
        label="📥 Download Memory",
        data=st.json.dumps(export_data),
        file_name=f"memory_{memory.id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def show_layer_statistics(memory_manager, layer: str):
    """Show detailed statistics for a layer"""
    layer_map = {
        "active": memory_manager.active_layer,
        "dormant": memory_manager.dormant_layer,
        "deep": memory_manager.deep_layer,
        "forgotten": memory_manager.forgotten_layer
    }
    
    layer_obj = layer_map[layer]
    stats = layer_obj.get_stats()
    
    st.subheader(f"📊 {layer.capitalize()} Layer Statistics")
    
    # Basic stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Memories", stats["count"])
    with col2:
        st.metric("Avg Importance", f"{stats.get('avg_importance', 0):.3f}")
    with col3:
        st.metric("Avg Access Count", f"{stats.get('avg_access_count', 0):.1f}")
    with col4:
        st.metric("Total Size", f"{stats.get('total_size_bytes', 0) / 1024:.1f} KB")
    
    # Time distribution
    if stats.get("oldest_memory") and stats.get("newest_memory"):
        st.subheader("📅 Time Distribution")
        
        oldest = datetime.fromisoformat(stats["oldest_memory"])
        newest = datetime.fromisoformat(stats["newest_memory"])
        age_range = newest - oldest
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Oldest Memory:** {oldest.strftime('%Y-%m-%d %H:%M')}")
            st.write(f"**Newest Memory:** {newest.strftime('%Y-%m-%d %H:%M')}")
        
        with col2:
            st.write(f"**Age Range:** {age_range.days} days")
            st.write(f"**Avg Age:** {age_range.days / 2:.1f} days")
    
    # Importance distribution
    memories = layer_obj.get_all_memories()
    if memories:
        st.subheader("📈 Importance Distribution")
        
        importance_ranges = {
            "Low (0.0-0.3)": 0,
            "Medium (0.3-0.7)": 0,
            "High (0.7-1.0)": 0
        }
        
        for memory in memories:
            if memory.importance_score < 0.3:
                importance_ranges["Low (0.0-0.3)"] += 1
            elif memory.importance_score < 0.7:
                importance_ranges["Medium (0.3-0.7)"] += 1
            else:
                importance_ranges["High (0.7-1.0)"] += 1
        
        # Create bar chart
        import plotly.express as px
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(importance_ranges.keys()),
                y=list(importance_ranges.values()),
                marker_color=['red', 'yellow', 'green']
            )
        ])
        
        fig.update_layout(
            title=f"Importance Distribution - {layer.capitalize()} Layer",
            xaxis_title="Importance Range",
            yaxis_title="Count"
        )
        
        st.plotly_chart(fig, width='stretch')

def show_promote_demote_interface(memory_manager, layer: str):
    """Show interface for promoting/demoting memories"""
    st.subheader("🔄 Promote/Demote Memories")
    
    memories = get_layer_memories(memory_manager, layer)
    
    if not memories:
        st.info("No memories available for promotion/demotion.")
        return
    
    # Select memory
    memory_options = {
        i: f"{mem.content[:50]}... (Importance: {mem.importance_score:.2f})"
        for i, mem in enumerate(memories)
    }
    
    selected_idx = st.selectbox(
        "Select Memory:",
        options=list(memory_options.keys()),
        format_func=lambda x: memory_options[x],
        key="promote_demote_select"
    )
    
    if selected_idx is not None:
        memory = memories[selected_idx]
        
        # Show current state
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Current Memory:**")
            st.write(memory.content[:100] + "..." if len(memory.content) > 100 else memory.content)
            st.write(f"**Layer:** {memory.layer.value}")
            st.write(f"**Importance:** {memory.importance_score:.3f}")
        
        with col2:
            st.write("**Available Actions:**")
            
            # Determine available actions
            available_actions = []
            
            if layer == "forgotten":
                available_actions.append("promote_to_deep")
            elif layer == "deep":
                available_actions.extend(["promote_to_dormant", "demote_to_forgotten"])
            elif layer == "dormant":
                available_actions.extend(["promote_to_active", "demote_to_deep"])
            elif layer == "active":
                available_actions.extend(["demote_to_dormant"])
            
            # Action buttons
            for action in available_actions:
                action_label = action.replace("_", " ").title()
                if st.button(f"🔄 {action_label}", key=f"action_{action}"):
                    execute_promote_demote(memory, action, memory_manager)
                    st.success(f"Memory {action_label} successfully!")
                    st.rerun()

def execute_promote_demote(memory: Memory, action: str, memory_manager):
    """Execute promote/demote action"""
    layer_map = {
        "active": memory_manager.active_layer,
        "dormant": memory_manager.dormant_layer,
        "deep": memory_manager.deep_layer,
        "forgotten": memory_manager.forgotten_layer
    }
    
    # Remove from current layer
    current_layer = layer_map[memory.layer]
    current_layer.remove_memory(memory.id)
    
    # Add to new layer
    if action == "promote_to_active":
        memory.layer = MemoryLayer.ACTIVE
        memory_manager.active_layer.add_memory(memory)
    elif action == "promote_to_dormant":
        memory.layer = MemoryLayer.DORMANT
        memory_manager.dormant_layer.add_memory(memory)
    elif action == "promote_to_deep":
        memory.layer = MemoryLayer.DEEP
        memory_manager.deep_layer.add_memory(memory)
    elif action == "demote_to_dormant":
        memory.layer = MemoryLayer.DORMANT
        memory_manager.dormant_layer.add_memory(memory)
    elif action == "demote_to_deep":
        memory.layer = MemoryLayer.DEEP
        memory_manager.deep_layer.add_memory(memory)
    elif action == "demote_to_forgotten":
        memory.layer = MemoryLayer.FORGOTTEN
        memory_manager.forgotten_layer.add_memory(memory)
