"""Memory page for SafeClaw"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta

from models.memory import MemoryLayer

def render():
    """Render the memory page"""
    st.title("📚 Memory Management")
    st.caption("Browse and manage SafeClaw's memory system")
    
    if not st.session_state.get('memory_manager'):
        st.error("❌ Memory manager not initialized.")
        return
    
    memory_manager = st.session_state.memory_manager
    
    # Memory statistics
    st.subheader("📊 Memory Statistics")
    stats = memory_manager.get_memory_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active", stats['active_count'])
    with col2:
        st.metric("Dormant", stats['dormant_count'])
    with col3:
        st.metric("Deep", stats['deep_count'])
    with col4:
        st.metric("Forgotten", stats['forgotten_count'])
    
    st.markdown("---")
    
    # Memory search
    st.subheader("🔍 Search Memories")
    search_query = st.text_input("Search memories...")
    max_results = st.slider("Max results", 1, 50, 10)
    
    if search_query and st.button("Search"):
        with st.spinner("Searching memories..."):
            results = memory_manager.search_memories(search_query, max_results)
            
            if results:
                st.success(f"Found {len(results)} memories")
                
                for i, result in enumerate(results, 1):
                    with st.expander(f"Result {i}: {result.memory.content[:50]}... (Score: {result.score:.2f})"):
                        st.write(f"**Content:** {result.memory.content}")
                        st.write(f"**Layer:** {result.memory.layer}")
                        st.write(f"**Importance:** {result.memory.importance_score:.2f}")
                        st.write(f"**Created:** {result.memory.created_at}")
                        st.write(f"**Accessed:** {result.memory.accessed_at}")
                        st.write(f"**Access Count:** {result.memory.access_count}")
                        
                        if result.memory.keywords:
                            st.write(f"**Keywords:** {', '.join(result.memory.keywords)}")
                        
                        if result.memory.metadata:
                            st.write("**Metadata:**")
                            st.json(result.memory.metadata)
            else:
                st.info("No memories found matching your search.")
    
    st.markdown("---")
    
    # Memory browser
    st.subheader("📖 Browse Memories")
    
    # Layer selection
    selected_layer = st.selectbox(
        "Select memory layer",
        ["active", "dormant", "deep", "forgotten"],
        format_func=lambda x: x.capitalize()
    )
    
    # Time filter
    time_filter = st.selectbox(
        "Time filter",
        ["all", "last_hour", "last_24h", "last_week", "last_month"]
    )
    
    if st.button("Load Memories"):
        with st.spinner(f"Loading {selected_layer} memories..."):
            memories = get_filtered_memories(memory_manager, selected_layer, time_filter)
            
            if memories:
                st.success(f"Loaded {len(memories)} memories from {selected_layer} layer")
                
                # Display memories in a table
                memory_data = []
                for memory in memories:
                    memory_data.append({
                        "ID": memory.id[:8] + "...",
                        "Content": memory.content[:100] + ("..." if len(memory.content) > 100 else ""),
                        "Importance": f"{memory.importance_score:.2f}",
                        "Created": memory.created_at.strftime("%Y-%m-%d %H:%M"),
                        "Accessed": memory.accessed_at.strftime("%Y-%m-%d %H:%M"),
                        "Access Count": memory.access_count
                    })
                
                df = pd.DataFrame(memory_data)
                st.dataframe(df, width='stretch')
                
                # Detailed view
                st.subheader("Detailed View")
                selected_memory = st.selectbox(
                    "Select a memory to view details",
                    range(len(memories)),
                    format_func=lambda i: f"Memory {i+1}: {memories[i].content[:50]}..."
                )
                
                if selected_memory is not None:
                    memory = memories[selected_memory]
                    
                    st.write(f"**ID:** {memory.id}")
                    st.write(f"**Content:** {memory.content}")
                    st.write(f"**Layer:** {memory.layer}")
                    st.write(f"**Importance Score:** {memory.importance_score}")
                    st.write(f"**Created:** {memory.created_at}")
                    st.write(f"**Last Accessed:** {memory.accessed_at}")
                    st.write(f"**Access Count:** {memory.access_count}")
                    
                    if memory.keywords:
                        st.write(f"**Keywords:** {', '.join(memory.keywords)}")
                    
                    if memory.metadata:
                        st.write("**Metadata:**")
                        st.json(memory.metadata)
                    
                    # Update importance
                    st.subheader("Update Memory")
                    new_importance = st.slider(
                        "Update Importance Score",
                        0.0, 1.0, memory.importance_score, 0.1
                    )
                    
                    if st.button("Update Importance") and new_importance != memory.importance_score:
                        if memory_manager.update_memory_importance(memory.id, new_importance):
                            st.success(f"Updated memory importance to {new_importance}")
                            st.rerun()
                        else:
                            st.error("Failed to update memory importance")
            else:
                st.info(f"No memories found in {selected_layer} layer with selected time filter.")
    
    st.markdown("---")
    
    # Memory operations
    st.subheader("⚙️ Memory Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 Memory Cleanup"):
            with st.spinner("Performing memory cleanup..."):
                memory_manager.cleanup_old_memories()
                st.success("Memory cleanup completed!")
                st.rerun()
    
    with col2:
        if st.button("📊 Refresh Stats"):
            st.rerun()
    
    # Add new memory
    st.subheader("➕ Add Memory")
    with st.expander("Manually add a memory"):
        memory_content = st.text_area("Memory content")
        importance_score = st.slider("Importance score", 0.0, 1.0, 0.5, 0.1)
        keywords = st.text_input("Keywords (comma-separated)")
        
        if st.button("Add Memory") and memory_content:
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
            memory_id = memory_manager.add_memory(
                content=memory_content,
                importance_score=importance_score,
                keywords=keyword_list,
                metadata={"source": "manual_add", "timestamp": datetime.now().isoformat()}
            )
            
            if memory_id:
                st.success(f"Memory added with ID: {memory_id}")
                st.rerun()
            else:
                st.error("Failed to add memory")

def get_filtered_memories(memory_manager, layer: str, time_filter: str) -> List:
    """Get filtered memories based on layer and time"""
    layer_enum = MemoryLayer(layer)
    
    # Get time cutoff
    if time_filter == "all":
        cutoff = None
    elif time_filter == "last_hour":
        cutoff = datetime.now() - timedelta(hours=1)
    elif time_filter == "last_24h":
        cutoff = datetime.now() - timedelta(hours=24)
    elif time_filter == "last_week":
        cutoff = datetime.now() - timedelta(days=7)
    elif time_filter == "last_month":
        cutoff = datetime.now() - timedelta(days=30)
    else:
        cutoff = None
    
    if cutoff:
        return memory_manager.get_recent_memories(
            hours=int((datetime.now() - cutoff).total_seconds() / 3600),
            layer=layer_enum
        )
    else:
        # Get all memories from the layer
        if layer_enum == MemoryLayer.ACTIVE:
            return memory_manager.active_layer.get_all_memories()
        elif layer_enum == MemoryLayer.DORMANT:
            return memory_manager.dormant_layer.get_all_memories()
        elif layer_enum == MemoryLayer.DEEP:
            return memory_manager.deep_layer.get_all_memories()
        elif layer_enum == MemoryLayer.FORGOTTEN:
            return memory_manager.forgotten_layer.get_all_memories()
    
    return []
