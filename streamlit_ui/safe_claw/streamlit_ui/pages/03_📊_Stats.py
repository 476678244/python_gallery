"""Statistics page for SafeClaw"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from core.memory.manager import MemoryManager

logger = logging.getLogger(__name__)

def render():
    """Render the statistics page"""
    logger.info("📊 Stats page render started")
    st.title("📊 Statistics & Analytics")
    st.caption("Monitor SafeClaw performance and usage")
    
    memory_manager = st.session_state.get('memory_manager')
    logger.info(f"🔍 memory_manager in session: {memory_manager is not None}")
    
    if not memory_manager:
        logger.error("❌ Memory manager not available in session state")
        st.error("❌ Services not available")
        return
    
    logger.info("✅ Memory manager available, proceeding with stats display")
    
    # Overview metrics
    st.subheader("📈 Overview")
    
    stats = memory_manager.get_memory_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Memories",
            stats['active_count'] + stats['dormant_count'] + stats['deep_count'] + stats['forgotten_count']
        )
    
    with col2:
        st.metric("Active Memories", stats['active_count'])
    
    with col3:
        st.metric("Avg Importance", calculate_avg_importance(memory_manager))
    
    with col4:
        st.metric("Sessions", len(st.session_state.messages))
    
    st.markdown("---")
    
    # Memory distribution chart
    st.subheader("🧠 Memory Distribution")
    
    # Create pie chart
    fig = px.pie(
        values=[
            stats['active_count'],
            stats['dormant_count'], 
            stats['deep_count'],
            stats['forgotten_count']
        ],
        names=['Active', 'Dormant', 'Deep', 'Forgotten'],
        title="Memory Layer Distribution"
    )
    st.plotly_chart(fig, width='stretch')
    
    # Memory timeline
    st.subheader("📅 Memory Timeline")
    
    time_range = st.selectbox(
        "Time Range",
        ["Last 24 Hours", "Last Week", "Last Month", "All Time"]
    )
    
    timeline_data = get_timeline_data(memory_manager, time_range)
    
    if timeline_data:
        fig = px.line(
            timeline_data,
            x='date',
            y='count',
            title="Memories Created Over Time",
            markers=True
        )
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No memory data available for selected time range.")
    
    st.markdown("---")
    
    # Performance metrics
    st.subheader("⚡ Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Response Times**")
        # Calculate average response time from message metadata
        response_times = get_response_times()
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            st.metric("Avg Response Time", f"{avg_time:.2f}s")
            
            fig = px.histogram(
                x=response_times,
                nbins=20,
                title="Response Time Distribution"
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No response time data available.")
    
    with col2:
        st.write("**Agent Usage**")
        agent_stats = get_agent_usage_stats()
        if agent_stats:
            fig = px.bar(
                x=list(agent_stats.keys()),
                y=list(agent_stats.values()),
                title="Agent Usage Count"
            )
            st.plotly_chart(fig, width='stretch')
        else:
            st.info("No agent usage data available.")
    
    st.markdown("---")
    
    # Memory content analysis
    st.subheader("📝 Content Analysis")
    
    # Get recent memories for analysis
    recent_memories = get_recent_memories_for_analysis(memory_manager)
    
    if recent_memories:
        # Word frequency analysis
        word_freq = analyze_word_frequency(recent_memories)
        
        if word_freq:
            st.write("**Top Keywords**")
            top_words = dict(list(word_freq.items())[:20])
            
            fig = px.bar(
                x=list(top_words.values()),
                y=list(top_words.keys()),
                orientation='h',
                title="Most Common Keywords in Recent Memories"
            )
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, width='stretch')
        
        # Importance distribution
        importance_scores = [m.importance_score for m in recent_memories]
        
        fig = px.histogram(
            x=importance_scores,
            nbins=20,
            title="Memory Importance Score Distribution",
            labels={'x': 'Importance Score', 'y': 'Count'}
        )
        st.plotly_chart(fig, width='stretch')
    
    st.markdown("---")
    
    # System health
    st.subheader("🏥 System Health")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Memory health
        memory_health = calculate_memory_health(memory_manager)
        st.metric("Memory Health", f"{memory_health:.1f}%")
        
        # Storage usage
        storage_info = get_storage_info(memory_manager)
        if storage_info:
            st.metric("Storage Used", f"{storage_info['total_mb']:.1f} MB")
    
    with col2:
        # LLM service status
        llm_status = "✅ Healthy" if st.session_state.get('llm_service') else "❌ Unavailable"
        st.metric("LLM Service", llm_status)
        
        # Graph status
        graph_status = "✅ Ready" if st.session_state.get('current_graph') else "❌ Not Ready"
        st.metric("Workflow", graph_status)
    
    with col3:
        # Session info
        st.metric("Current Session", st.session_state.session_id[:8] + "...")
        st.metric("Uptime", calculate_uptime())
    
    st.markdown("---")
    
    # Detailed statistics
    st.subheader("🔍 Detailed Statistics")
    
    if st.button("Generate Detailed Report"):
        with st.spinner("Generating detailed report..."):
            report = generate_detailed_report(memory_manager)
            st.json(report)

def calculate_avg_importance(memory_manager) -> float:
    """Calculate average importance score across all memories"""
    try:
        all_memories = []
        all_memories.extend(memory_manager.active_layer.get_all_memories())
        all_memories.extend(memory_manager.dormant_layer.get_all_memories())
        all_memories.extend(memory_manager.deep_layer.get_all_memories())
        
        if not all_memories:
            return 0.0
        
        total_importance = sum(m.importance_score for m in all_memories)
        return total_importance / len(all_memories)
    except:
        return 0.0

def get_timeline_data(memory_manager, time_range: str) -> List[Dict]:
    """Get timeline data for memory creation"""
    try:
        # Determine cutoff date
        if time_range == "Last 24 Hours":
            cutoff = datetime.now() - timedelta(hours=24)
        elif time_range == "Last Week":
            cutoff = datetime.now() - timedelta(days=7)
        elif time_range == "Last Month":
            cutoff = datetime.now() - timedelta(days=30)
        else:
            cutoff = None
        
        # Get memories from all layers
        all_memories = []
        all_memories.extend(memory_manager.active_layer.get_all_memories())
        all_memories.extend(memory_manager.dormant_layer.get_all_memories())
        all_memories.extend(memory_manager.deep_layer.get_all_memories())
        
        # Filter by time
        if cutoff:
            all_memories = [m for m in all_memories if m.created_at >= cutoff]
        
        # Group by date
        date_counts = {}
        for memory in all_memories:
            date = memory.created_at.date()
            date_counts[date] = date_counts.get(date, 0) + 1
        
        # Convert to list for plotting
        timeline_data = []
        for date in sorted(date_counts.keys()):
            timeline_data.append({
                'date': date,
                'count': date_counts[date]
            })
        
        return timeline_data
    except:
        return []

def get_response_times() -> List[float]:
    """Extract response times from message metadata"""
    response_times = []
    for message in st.session_state.messages:
        if message.get('role') == 'assistant' and 'metadata' in message:
            processing_time = message['metadata'].get('processing_time')
            if processing_time:
                response_times.append(processing_time)
    return response_times

def get_agent_usage_stats() -> Dict[str, int]:
    """Get agent usage statistics"""
    agent_counts = {}
    for message in st.session_state.messages:
        if message.get('role') == 'assistant' and 'metadata' in message:
            agent = message['metadata'].get('agent', 'unknown')
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
    return agent_counts

def get_recent_memories_for_analysis(memory_manager) -> List:
    """Get recent memories for content analysis"""
    try:
        recent_memories = memory_manager.get_recent_memories(hours=168)  # Last week
        return recent_memories[:100]  # Limit to 100 for analysis
    except:
        return []

def analyze_word_frequency(memories: List) -> Dict[str, int]:
    """Analyze word frequency in memories"""
    from collections import Counter
    import re
    
    word_count = Counter()
    
    for memory in memories:
        # Extract words from content and keywords
        text = memory.content.lower()
        words = re.findall(r'\b\w+\b', text)
        
        # Add keywords
        for keyword in memory.keywords:
            words.append(keyword.lower())
        
        # Filter common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        word_count.update(filtered_words)
    
    return dict(word_count.most_common(50))

def calculate_memory_health(memory_manager) -> float:
    """Calculate memory system health score"""
    try:
        stats = memory_manager.get_memory_stats()
        total = stats['active_count'] + stats['dormant_count'] + stats['deep_count']
        
        if total == 0:
            return 100.0  # Perfect health if no memories
        
        # Health factors
        active_ratio = stats['active_count'] / total
        forgotten_ratio = stats['forgotten_count'] / total
        
        # Calculate health score (0-100)
        health_score = (active_ratio * 60) + ((1 - forgotten_ratio) * 40)
        return min(100.0, max(0.0, health_score))
    except:
        return 0.0

def get_storage_info(memory_manager) -> Dict[str, float]:
    """Get storage information"""
    try:
        stats = memory_manager.storage.get_layer_stats('active')
        total_size = stats.get('total_size_bytes', 0)
        
        # Get stats for all layers
        for layer in ['dormant', 'deep', 'forgotten']:
            layer_stats = memory_manager.storage.get_layer_stats(layer)
            total_size += layer_stats.get('total_size_bytes', 0)
        
        return {
            'total_bytes': total_size,
            'total_mb': total_size / (1024 * 1024)
        }
    except:
        return {}

def calculate_uptime() -> str:
    """Calculate session uptime"""
    # This is a placeholder - would need actual session start time
    return "Unknown"

def generate_detailed_report(memory_manager) -> Dict[str, Any]:
    """Generate comprehensive statistics report"""
    try:
        stats = memory_manager.get_memory_stats()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "memory_stats": stats,
            "session_info": {
                "session_id": st.session_state.session_id,
                "message_count": len(st.session_state.messages),
                "workspace_path": str(st.session_state.workspace_path)
            },
            "system_status": {
                "llm_service": bool(st.session_state.get('llm_service')),
                "memory_manager": bool(st.session_state.get('memory_manager')),
                "workflow_graph": bool(st.session_state.get('current_graph'))
            },
            "agent_usage": get_agent_usage_stats(),
            "performance": {
                "avg_response_time": sum(get_response_times()) / len(get_response_times()) if get_response_times() else 0,
                "response_times": get_response_times()
            }
        }
        
        return report
    except Exception as e:
        return {"error": str(e)}
