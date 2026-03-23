"""Dashboard component for SafeClaw overview"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import plotly.graph_objects as go
import plotly.express as px

def render_dashboard():
    """Render main dashboard with system overview"""
    
    st.title("🏠 SafeClaw Dashboard")
    st.caption("System overview and quick access to all features")
    
    # Quick stats
    render_quick_stats()
    
    # Main grid layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Activity feed
        render_activity_feed()
    
    with col2:
        # Quick actions
        render_quick_actions()
        
        # System status
        render_system_status()
    
    # Bottom row
    render_bottom_row()

def render_quick_stats():
    """Render quick statistics overview"""
    
    # Get data from various services
    memory_manager = st.session_state.get('memory_manager')
    session_service = st.session_state.get('session_service')
    skill_registry = st.session_state.get('skill_registry')
    safety_checker = st.session_state.get('safety_checker')
    
    # Calculate stats
    stats = calculate_dashboard_stats(memory_manager, session_service, skill_registry, safety_checker)
    
    # Display stats in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🧠 Active Memories", 
            stats["active_memories"],
            delta=stats["memory_delta"],
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "💬 Chat Sessions", 
            stats["total_sessions"],
            delta=stats["session_delta"],
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "🔧 Skill Executions", 
            stats["skill_executions"],
            delta=stats["skill_delta"],
            delta_color="normal"
        )
    
    with col4:
        st.metric(
            "🛡️ Safety Checks", 
            stats["safety_checks"],
            delta=stats["safety_delta"],
            delta_color="normal"
        )

def calculate_dashboard_stats(memory_manager, session_service, skill_registry, safety_checker) -> Dict[str, Any]:
    """Calculate dashboard statistics"""
    
    stats = {
        "active_memories": 0,
        "memory_delta": 0,
        "total_sessions": 0,
        "session_delta": 0,
        "skill_executions": 0,
        "skill_delta": 0,
        "safety_checks": 0,
        "safety_delta": 0
    }
    
    # Memory stats
    if memory_manager:
        memory_stats = memory_manager.get_memory_stats()
        stats["active_memories"] = memory_stats["active_count"]
        stats["memory_delta"] = memory_stats.get("active_delta", 0)
    
    # Session stats
    if session_service:
        stats["total_sessions"] = session_service.get_total_session_count()
        stats["session_delta"] = session_service.get_session_count() - stats["total_sessions"]
    
    # Skill stats
    if skill_registry:
        skill_stats = skill_registry.get_usage_stats()
        stats["skill_executions"] = skill_stats["total_executions"]
        stats["skill_delta"] = skill_stats.get("execution_delta", 0)
    
    # Safety stats
    if safety_checker:
        safety_stats = safety_checker.get_safety_stats()
        stats["safety_checks"] = safety_stats["total_checks"]
        stats["safety_delta"] = safety_stats.get("check_delta", 0)
    
    return stats

def render_activity_feed():
    """Render activity feed"""
    
    st.subheader("📊 Recent Activity")
    
    # Get recent activities
    activities = get_recent_activities()
    
    if activities:
        # Create activity timeline
        for activity in activities:
            render_activity_item(activity)
    else:
        st.info("No recent activity")

def get_recent_activities() -> List[Dict[str, Any]]:
    """Get recent activities from various sources"""
    
    activities = []
    
    # Get recent chat messages
    if 'messages' in st.session_state and st.session_state['messages']:
        recent_messages = st.session_state['messages'][-5:]  # Last 5 messages
        
        for message in recent_messages:
            activities.append({
                "type": "chat",
                "icon": "💬",
                "title": f"New {message.get('role', 'message')}",
                "description": message.get('content', '')[:100] + "..." if len(message.get('content', '')) > 100 else message.get('content', ''),
                "timestamp": message.get('timestamp', datetime.now()),
                "metadata": message.get('metadata', {})
            })
    
    # Get recent skill executions
    skill_registry = st.session_state.get('skill_registry')
    if skill_registry:
        # Get recent skill executions from usage stats
        skill_stats = skill_registry.get_usage_stats()
        skill_activities = [
            {
                "type": "skill",
                "icon": "🔧",
                "title": skill_name,
                "description": f"Skill execution in {skill_registry.get_skill(skill_name).category if skill_registry.get_skill(skill_name) else 'unknown'} category",
                "timestamp": datetime.now(),
                "metadata": {"usage_count": count}
            }
            for skill_name, count in list(skill_stats.get("skill_usage", {}).items())[:5]
        ]
        activities.extend(skill_activities)
    
    # Get recent safety checks
    safety_checker = st.session_state.get('safety_checker')
    if safety_checker:
        # Get recent safety checks from audit log
        audit_logger = st.session_state.get('audit_logger')
        if audit_logger:
            recent_events = audit_logger.get_events(limit=5)
            safety_activities = [
                {
                    "type": "safety",
                    "icon": "🛡️",
                    "title": f"Safety Check - {event.event_type}",
                    "description": f"Safety event: {event.level.value}",
                    "timestamp": event.timestamp,
                    "metadata": {"event_type": event.event_type, "level": event.level.value}
                }
                for event in recent_events
                if event.event_type in ["safety_check", "security_event"]
            ]
            activities.extend(safety_activities)
    
    # Sort by timestamp
    activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return activities[:10]  # Return top 10

def render_activity_item(activity: Dict[str, Any]):
    """Render individual activity item"""
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.markdown(f"### {activity['icon']}")
    
    with col2:
        st.markdown(f"**{activity['title']}**")
        st.markdown(f"{activity['description']}")
        st.caption(f"🕐 {activity['timestamp'].strftime('%H:%M:%S')}")

def render_quick_actions():
    """Render quick action buttons"""
    
    st.subheader("⚡ Quick Actions")
    
    # Quick action buttons
    if st.button("💬 New Chat", key="new_chat", width='stretch'):
        start_new_chat()
    
    if st.button("🧠 Memory Manager", key="memory_manager", width='stretch'):
        st.switch_page("pages/01_📚_Memory.py")
    
    if st.button("🔧 Skill Manager", key="skill_manager", width='stretch'):
        st.switch_page("pages/04_🔧_Tools.py")
    
    if st.button("🛡️ Safety Dashboard", key="safety_dashboard", width='stretch'):
        st.switch_page("pages/04_🔧_Tools.py")
    
    # Quick stats
    st.subheader("📈 Quick Stats")
    
    # Memory usage chart
    render_memory_usage_chart()
    
    # Recent performance
    render_recent_performance()

def render_memory_usage_chart():
    """Render memory usage chart"""
    
    memory_manager = st.session_state.get('memory_manager')
    
    if memory_manager:
        memory_stats = memory_manager.get_memory_stats()
        
        # Create pie chart
        fig = go.Figure(data=[
            go.Pie(
                labels=["Active", "Dormant", "Deep", "Forgotten"],
                values=[
                    memory_stats["active_count"],
                    memory_stats["dormant_count"],
                    memory_stats["deep_count"],
                    memory_stats["forgotten_count"]
                ],
                hole=0.3,
                marker_colors=['lightgreen', 'yellow', 'blue', 'gray']
            )
        ])
        
        fig.update_layout(
            title="Memory Distribution",
            height=300
        )
        
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Memory manager not available")

def render_recent_performance():
    """Render recent performance metrics"""
    
    # Get performance data
    performance_data = get_recent_performance_data()
    
    if performance_data:
        # Create line chart
        fig = go.Figure(data=[
            go.Scatter(
                x=performance_data['timestamps'],
                y=performance_data['response_times'],
                mode='lines+markers',
                name='Response Time',
                line=dict(color='blue')
            )
        ])
        
        fig.update_layout(
            title="Recent Response Times",
            xaxis_title="Time",
            yaxis_title="Response Time (s)",
            height=300
        )
        
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No performance data available")

def get_recent_performance_data() -> Dict[str, List]:
    """Get recent performance data"""
    
    # This would get actual performance data
    # For now, return simulated data
    
    import random
    from datetime import datetime, timedelta
    
    timestamps = []
    response_times = []
    
    for i in range(10):
        timestamp = datetime.now() - timedelta(minutes=i*5)
        timestamps.append(timestamp)
        response_times.append(random.uniform(0.5, 3.0))
    
    return {
        "timestamps": timestamps,
        "response_times": response_times
    }

def render_system_status():
    """Render system status panel"""
    
    st.subheader("🖥️ System Status")
    
    # Check system status
    status_items = get_system_status()
    
    for item in status_items:
        render_status_item(item)

def get_system_status() -> List[Dict[str, Any]]:
    """Get system status items"""
    
    status_items = []
    
    # Check LLM service
    llm_service = st.session_state.get('llm_service')
    if llm_service:
        status_items.append({
            "name": "LLM Service",
            "status": "healthy" if llm_service else "unhealthy",
            "description": "LLM gateway and model access"
        })
    
    # Check memory manager
    memory_manager = st.session_state.get('memory_manager')
    if memory_manager:
        status_items.append({
            "name": "Memory System",
            "status": "healthy",
            "description": "4-layer memory management"
        })
    
    # Check safety system
    safety_checker = st.session_state.get('safety_checker')
    if safety_checker:
        status_items.append({
            "name": "Safety System",
            "status": "healthy",
            "description": "Safety checks and policies"
        })
    
    # Check skill registry
    skill_registry = st.session_state.get('skill_registry')
    if skill_registry:
        status_items.append({
            "name": "Skill System",
            "status": "healthy",
            "description": f"{len(skill_registry.get_all_skills())} skills available"
        })
    
    return status_items

def render_status_item(status_item: Dict[str, Any]):
    """Render individual status item"""
    
    status_color = {
        "healthy": "🟢",
        "warning": "🟡",
        "unhealthy": "🔴",
        "unknown": "⚪"
    }
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown(status_color.get(status_item["status"], "⚪"))
    
    with col2:
        st.markdown(f"**{status_item['name']}**")
        st.caption(status_item['description'])

def render_bottom_row():
    """Render bottom row with additional widgets"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_recent_files()
    
    with col2:
        render_recent_skills()
    
    with col3:
        render_system_health()

def render_recent_files():
    """Render recent files widget"""
    
    st.subheader("📁 Recent Files")
    
    # Get recent file operations
    recent_files = get_recent_files()
    
    if recent_files:
        for file_item in recent_files:
            with st.expander(f"📄 {file_item['name']}", expanded=False):
                st.write(f"**Type:** {file_item['type']}")
                st.write(f"**Size:** {file_item['size']}")
                st.write(f"**Modified:** {file_item['modified']}")
    else:
        st.info("No recent file operations")

def get_recent_files() -> List[Dict[str, Any]]:
    """Get recent file operations"""
    
    # This would get actual file operations from audit log
    # For now, return simulated data
    
    return [
        {
            "name": "example.py",
            "type": "Python File",
            "size": "1.2 KB",
            "modified": "2 hours ago"
        },
        {
            "name": "config.json",
            "type": "JSON File",
            "size": "0.5 KB",
            "modified": "5 hours ago"
        }
    ]

def render_recent_skills():
    """Render recent skills widget"""
    
    st.subheader("🔧 Recent Skills")
    
    # Get recent skill executions
    recent_skills = get_recent_skills()
    
    if recent_skills:
        for skill_item in recent_skills:
            with st.expander(f"🔧 {skill_item['name']}", expanded=False):
                st.write(f"**Category:** {skill_item['category']}")
                st.write(f"**Executed:** {skill_item['executed']}")
                st.write(f"**Status:** {skill_item['status']}")
    else:
        st.info("No recent skill executions")

def get_recent_skills() -> List[Dict[str, Any]]:
    """Get recent skill executions"""
    
    # This would get actual skill executions
    # For now, return simulated data
    
    return [
        {
            "name": "read_file",
            "category": "file_operations",
            "executed": "10 minutes ago",
            "status": "success"
        },
        {
            "name": "analyze_code",
            "category": "code_analysis",
            "executed": "30 minutes ago",
            "status": "success"
        }
    ]

def render_system_health():
    """Render system health widget"""
    
    st.subheader("🏥 System Health")
    
    # Get system health metrics
    health_metrics = get_system_health_metrics()
    
    for metric in health_metrics:
        render_health_metric(metric)

def get_system_health_metrics() -> List[Dict[str, Any]]:
    """Get system health metrics"""
    
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        return [
            {
                "name": "CPU Usage",
                "value": f"{cpu_percent:.1f}%",
                "status": "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "unhealthy"
            },
            {
                "name": "Memory Usage",
                "value": f"{memory.percent:.1f}%",
                "status": "healthy" if memory.percent < 80 else "warning" if memory.percent < 95 else "unhealthy"
            },
            {
                "name": "Disk Usage",
                "value": f"{(disk.used / disk.total) * 100:.1f}%",
                "status": "healthy" if (disk.used / disk.total) * 100 < 80 else "warning" if (disk.used / disk.total) * 100 < 95 else "unhealthy"
            }
        ]
    
    except ImportError:
        return [
            {
                "name": "System Monitor",
                "value": "Unavailable",
                "status": "unknown"
            }
        ]

def render_health_metric(metric: Dict[str, Any]):
    """Render individual health metric"""
    
    status_color = {
        "healthy": "🟢",
        "warning": "🟡",
        "unhealthy": "🔴",
        "unknown": "⚪"
    }
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.markdown(status_color.get(metric["status"], "⚪"))
    
    with col2:
        st.markdown(f"**{metric['name']}**")
        st.caption(metric['value'])

def start_new_chat():
    """Start a new chat session"""
    
    # Clear current messages
    if 'messages' in st.session_state:
        st.session_state['messages'] = []
    
    # Create new session ID
    import uuid
    st.session_state['session_id'] = str(uuid.uuid4())
    
    # Update session start time
    st.session_state['session_start'] = datetime.now()
    
    st.success("New chat started!")
    st.rerun()
