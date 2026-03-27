"""Tools page for SafeClaw - Advanced tools and utilities"""

import streamlit as st
from typing import Dict, Any

def render():
    """Render the tools page"""
    
    # Check if required services are available
    if not check_services():
        st.error("❌ Required services not available. Please check your configuration.")
        return
    
    # Get services
    skill_registry = get_skill_registry()
    safety_checker = get_safety_checker()
    audit_logger = get_audit_logger()
    
    # Tab interface
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔧 Skill Manager", 
        "🛡️ Safety Dashboard", 
        "🤖 Agent Monitor", 
        "🖥️ System Monitor",
        "📊 Analytics"
    ])
    
    with tab1:
        from streamlit_ui.components.skill_manager import render_skill_manager
        render_skill_manager(skill_registry)
    
    with tab2:
        from streamlit_ui.components.safety_dashboard import render_safety_dashboard
        render_safety_dashboard(safety_checker, audit_logger)
    
    with tab3:
        from streamlit_ui.components.agent_monitor import render_agent_monitor
        graph_builder = get_graph_builder()
        current_graph = st.session_state.get('current_graph')
        render_agent_monitor(graph_builder, current_graph)
    
    with tab4:
        from streamlit_ui.components.system_monitor import render_system_monitor
        render_system_monitor()
    
    with tab5:
        render_analytics()

def check_services() -> bool:
    """Check if required services are available"""
    required_services = [
        'skill_registry',
        'safety_checker', 
        'graph_builder'
    ]
    
    return all(service in st.session_state for service in required_services)

def get_skill_registry():
    """Get skill registry from session state"""
    return st.session_state.get('skill_registry')

def get_safety_checker():
    """Get safety checker from session state"""
    return st.session_state.get('safety_checker')

def get_audit_logger():
    """Get audit logger from session state"""
    return st.session_state.get('audit_logger')

def get_graph_builder():
    """Get graph builder from session state"""
    return st.session_state.get('graph_builder')

def render_analytics():
    """Render analytics dashboard"""
    
    st.subheader("📊 Analytics Dashboard")
    
    # Get data from various sources
    skill_registry = get_skill_registry()
    safety_checker = get_safety_checker()
    audit_logger = get_audit_logger()
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Skill usage
        if skill_registry:
            stats = skill_registry.get_usage_stats()
            st.metric("Total Skill Executions", stats["total_executions"])
    
    with col2:
        # Safety checks
        if safety_checker:
            safety_stats = safety_checker.get_safety_stats()
            st.metric("Safety Checks", safety_stats["total_checks"])
    
    with col3:
        # Audit events
        if audit_logger:
            audit_stats = audit_logger.get_statistics()
            st.metric("Audit Events", audit_stats["total_events"])
        else:
            st.metric("Audit Events", "N/A")
    
    with col4:
        # Sessions
        session_service = st.session_state.get('session_service')
        if session_service:
            st.metric("Total Sessions", session_service.get_total_session_count())
    
    # Analytics sections
    analytics_tab1, analytics_tab2, analytics_tab3 = st.tabs([
        "📈 Usage Analytics", 
        "🔍 Performance Analytics", 
        "📋 System Analytics"
    ])
    
    with analytics_tab1:
        render_usage_analytics(skill_registry, safety_checker, audit_logger)
    
    with analytics_tab2:
        render_performance_analytics()
    
    with analytics_tab3:
        render_system_analytics()

def render_usage_analytics(skill_registry, safety_checker, audit_logger):
    """Render usage analytics"""
    
    st.subheader("📈 Usage Analytics")
    
    # Time range selection
    time_range = st.selectbox(
        "Select Time Range:",
        ["Last Hour", "Last 24 Hours", "Last Week", "Last Month"],
        key="usage_time_range"
    )
    
    # Skill usage analytics
    if skill_registry:
        st.subheader("🔧 Skill Usage")
        
        skill_stats = skill_registry.get_usage_stats()
        
        if skill_stats["skill_usage"]:
            # Create skill usage chart
            import plotly.express as px
            import plotly.graph_objects as go
            
            skill_names = list(skill_stats["skill_usage"].keys())
            skill_counts = list(skill_stats["skill_usage"].values())
            
            fig = go.Figure(data=[
                go.Bar(
                    x=skill_names,
                    y=skill_counts,
                    marker_color='lightblue'
                )
            ])
            
            fig.update_layout(
                title="Skill Usage Distribution",
                xaxis_title="Skill",
                yaxis_title="Usage Count"
            )
            
            st.plotly_chart(fig, width='stretch')
            
            # Skill usage table
            import pandas as pd
            skill_data = []
            for name, count in skill_stats["skill_usage"].items():
                skill_data.append({
                    "Skill": name,
                    "Usage Count": count,
                    "Category": skill_registry.get_skill(name).category if skill_registry.get_skill(name) else "Unknown"
                })
            
            df = pd.DataFrame(skill_data)
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No skill usage data available.")
    
    # Safety analytics
    if safety_checker:
        st.subheader("🛡️ Safety Analytics")
        
        safety_stats = safety_checker.get_safety_stats()
        
        # Risk distribution
        if safety_stats["risk_distribution"]:
            import plotly.graph_objects as go
            
            risk_levels = list(safety_stats["risk_distribution"].keys())
            risk_counts = list(safety_stats["risk_distribution"].values())
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=risk_levels,
                    values=risk_counts,
                    hole=0.3,
                    marker_colors=['green', 'yellow', 'orange', 'red']
                )
            ])
            
            fig.update_layout(
                title="Risk Level Distribution"
            )
            
            st.plotly_chart(fig, width='stretch')
        
        # Safety metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Checks", safety_stats["total_checks"])
        with col2:
            st.metric("Blocked", safety_stats["blocked_requests"])
        with col3:
            st.metric("Confirmations", safety_stats["confirmation_required"])
        with col4:
            block_rate = safety_stats["block_rate"] * 100
            st.metric("Block Rate", f"{block_rate:.1f}%")

def render_performance_analytics():
    """Render performance analytics"""
    
    st.subheader("🔍 Performance Analytics")
    
    # Get performance data from various sources
    memory_manager = st.session_state.get('memory_manager')
    session_service = st.session_state.get('session_service')
    
    # Memory performance
    if memory_manager:
        st.subheader("🧠 Memory Performance")
        
        memory_stats = memory_manager.get_memory_stats()
        
        # Memory layer distribution
        import plotly.graph_objects as go
        
        layers = ['Active', 'Dormant', 'Deep', 'Forgotten']
        counts = [
            memory_stats["active_count"],
            memory_stats["dormant_count"],
            memory_stats["deep_count"],
            memory_stats["forgotten_count"]
        ]
        
        fig = go.Figure(data=[
            go.Bar(
                x=layers,
                y=counts,
                marker_color=['green', 'yellow', 'blue', 'gray']
            )
        ])
        
        fig.update_layout(
            title="Memory Distribution Across Layers",
            xaxis_title="Memory Layer",
            yaxis_title="Count"
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Memory statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Memories", memory_stats["total_count"])
        with col2:
            st.metric("Active Memories", memory_stats["active_count"])
        with col3:
            st.metric("Dormant Memories", memory_stats["dormant_count"])
        with col4:
            st.metric("Deep Memories", memory_stats["deep_count"])

def render_system_analytics():
    """Render system analytics"""
    
    st.subheader("📋 System Analytics")
    
    # Get system information
    try:
        import psutil
        
        # System resource usage over time
        st.subheader("💻 System Resource Trends")
        
        # Get current system info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Current system metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("CPU Usage", f"{cpu_percent:.1f}%")
        with col2:
            st.metric("Memory Usage", f"{memory.percent:.1f}%")
        with col3:
            disk_percent = (disk.used / disk.total) * 100
            st.metric("Disk Usage", f"{disk_percent:.1f}%")
        
        # System information
        st.subheader("🖥️ System Information")
        
        import platform
        
        system_info = {
            "System": platform.system(),
            "Release": platform.release(),
            "Version": platform.version(),
            "Machine": platform.machine(),
            "Processor": platform.processor(),
            "Python Version": platform.python_version(),
            "CPU Count": psutil.cpu_count(),
            "Total Memory": f"{memory.total / (1024**3):.1f} GB",
            "Total Disk": f"{disk.total / (1024**3):.1f} GB"
        }
        
        # Display system info
        for key, value in system_info.items():
            st.write(f"**{key}:** {value}")
    
    except ImportError:
        st.error("psutil library not available. System analytics require psutil to be installed.")
        st.info("Install with: pip install psutil")
    
    except Exception as e:
        st.error(f"Error getting system analytics: {str(e)}")

# Page initialization
if __name__ == "__main__":
    render()
