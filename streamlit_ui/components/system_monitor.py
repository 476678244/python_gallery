"""System monitor component for SafeClaw"""

import streamlit as st
import pandas as pd
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

def render_system_monitor():
    """Render system monitoring interface"""
    
    st.subheader("🖥️ System Monitor")
    
    # Get system information
    system_info = get_system_info()
    
    # Overview metrics
    render_system_overview(system_info)
    
    # Tab interface
    tab1, tab2, tab3, tab4 = st.tabs([
        "💻 System Resources", 
        "📊 Performance History", 
        "🔧 Configuration", 
        "📋 System Logs"
    ])
    
    with tab1:
        render_system_resources(system_info)
    
    with tab2:
        render_performance_history()
    
    with tab3:
        render_system_configuration()
    
    with tab4:
        render_system_logs()

def get_system_info() -> Dict[str, Any]:
    """Get current system information"""
    try:
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        # Memory information
        memory = psutil.virtual_memory()
        
        # Disk information
        disk = psutil.disk_usage('/')
        
        # Network information
        network = psutil.net_io_counters()
        
        # Process information
        process = psutil.Process()
        
        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
                "frequency": cpu_freq.current if cpu_freq else 0,
                "per_cpu": psutil.cpu_percent(percpu=True)
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            },
            "process": {
                "pid": process.pid,
                "name": process.name(),
                "cpu_percent": process.cpu_percent(),
                "memory_percent": process.memory_percent(),
                "memory_info": process.memory_info(),
                "create_time": process.create_time(),
                "status": process.status()
            }
        }
    except Exception as e:
        st.error(f"Error getting system information: {str(e)}")
        return {}

def render_system_overview(system_info: Dict[str, Any]):
    """Render system overview metrics"""
    
    if not system_info:
        st.error("Unable to retrieve system information.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("CPU Usage", f"{system_info['cpu']['percent']:.1f}%")
    
    with col2:
        st.metric("Memory Usage", f"{system_info['memory']['percent']:.1f}%")
    
    with col3:
        st.metric("Disk Usage", f"{system_info['disk']['percent']:.1f}%")
    
    with col4:
        uptime = get_system_uptime()
        st.metric("Uptime", uptime)

def render_system_resources(system_info: Dict[str, Any]):
    """Render detailed system resources"""
    
    if not system_info:
        st.error("Unable to retrieve system information.")
        return
    
    # CPU Information
    st.subheader("💻 CPU Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Usage:** {system_info['cpu']['percent']:.1f}%")
        st.write(f"**Cores:** {system_info['cpu']['count']}")
        st.write(f"**Frequency:** {system_info['cpu']['frequency']:.1f} MHz")
    
    with col2:
        # CPU usage chart
        import plotly.graph_objects as go
        
        per_cpu = system_info['cpu']['per_cpu']
        cpu_labels = [f"Core {i}" for i in range(len(per_cpu))]
        
        fig = go.Figure(data=[
            go.Bar(
                x=cpu_labels,
                y=per_cpu,
                marker_color='lightblue'
            )
        ])
        
        fig.update_layout(
            title="CPU Usage by Core",
            xaxis_title="CPU Core",
            yaxis_title="Usage (%)"
        )
        
        st.plotly_chart(fig, width='stretch')
    
    # Memory Information
    st.subheader("🧠 Memory Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        memory = system_info['memory']
        st.write(f"**Total:** {format_bytes(memory['total'])}")
        st.write(f"**Used:** {format_bytes(memory['used'])}")
        st.write(f"**Free:** {format_bytes(memory['free'])}")
        st.write(f"**Available:** {format_bytes(memory['available'])}")
        st.write(f"**Usage:** {memory['percent']:.1f}%")
    
    with col2:
        # Memory usage chart
        fig = go.Figure(data=[
            go.Pie(
                labels=["Used", "Free"],
                values=[memory['used'], memory['free']],
                hole=0.3,
                marker_colors=['lightcoral', 'lightgreen']
            )
        ])
        
        fig.update_layout(
            title="Memory Usage Distribution"
        )
        
        st.plotly_chart(fig, width='stretch')
    
    # Disk Information
    st.subheader("💾 Disk Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        disk = system_info['disk']
        st.write(f"**Total:** {format_bytes(disk['total'])}")
        st.write(f"**Used:** {format_bytes(disk['used'])}")
        st.write(f"**Free:** {format_bytes(disk['free'])}")
        st.write(f"**Usage:** {disk['percent']:.1f}%")
    
    with col2:
        # Disk usage chart
        fig = go.Figure(data=[
            go.Bar(
                x=["Used", "Free"],
                y=[disk['used'], disk['free']],
                marker_color=['lightcoral', 'lightgreen']
            )
        ])
        
        fig.update_layout(
            title="Disk Usage",
            yaxis_title="Size (bytes)"
        )
        
        st.plotly_chart(fig, width='stretch')
    
    # Network Information
    st.subheader("🌐 Network Information")
    
    network = system_info['network']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Bytes Sent:** {format_bytes(network['bytes_sent'])}")
        st.write(f"**Bytes Received:** {format_bytes(network['bytes_recv'])}")
        st.write(f"**Packets Sent:** {network['packets_sent']:,}")
        st.write(f"**Packets Received:** {network['packets_recv']:,}")
    
    with col2:
        # Network traffic chart
        fig = go.Figure(data=[
            go.Bar(
                x=["Sent", "Received"],
                y=[network['bytes_sent'], network['bytes_recv']],
                marker_color=['lightblue', 'lightgreen']
            )
        ])
        
        fig.update_layout(
            title="Network Traffic",
            yaxis_title="Bytes"
        )
        
        st.plotly_chart(fig, width='stretch')
    
    # Process Information
    st.subheader("🔄 Process Information")
    
    process = system_info['process']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**PID:** {process['pid']}")
        st.write(f"**Name:** {process['name']}")
        st.write(f"**Status:** {process['status']}")
        st.write(f"**CPU Usage:** {process['cpu_percent']:.1f}%")
        st.write(f"**Memory Usage:** {process['memory_percent']:.1f}%")
    
    with col2:
        memory_info = process['memory_info']
        st.write(f"**RSS:** {format_bytes(memory_info.rss)}")
        st.write(f"**VMS:** {format_bytes(memory_info.vms)}")
        
        # Handle different memory info objects safely
        try:
            if hasattr(memory_info, 'shared'):
                st.write(f"**Shared:** {format_bytes(memory_info.shared)}")
            if hasattr(memory_info, 'text'):
                st.write(f"**Text:** {format_bytes(memory_info.text)}")
            if hasattr(memory_info, 'lib'):
                st.write(f"**Lib:** {format_bytes(memory_info.lib)}")
            if hasattr(memory_info, 'data'):
                st.write(f"**Data:** {format_bytes(memory_info.data)}")
            if hasattr(memory_info, 'pfm'):
                st.write(f"**PFM:** {format_bytes(memory_info.pfm)}")
        except Exception as e:
            st.write(f"Memory info details unavailable: {str(e)}")

def render_performance_history():
    """Render performance history charts"""
    
    st.subheader("📊 Performance History")
    
    # Time range selection
    time_range = st.selectbox(
        "Select Time Range:",
        ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last Week"],
        key="performance_time_range"
    )
    
    # Get historical data (simulated for now)
    historical_data = get_historical_performance_data(time_range)
    
    if historical_data:
        # CPU usage history
        st.subheader("💻 CPU Usage History")
        
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[
            go.Scatter(
                x=historical_data['timestamps'],
                y=historical_data['cpu_usage'],
                mode='lines+markers',
                name='CPU Usage',
                line=dict(color='blue')
            )
        ])
        
        fig.update_layout(
            title=f"CPU Usage - {time_range}",
            xaxis_title="Time",
            yaxis_title="Usage (%)"
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Memory usage history
        st.subheader("🧠 Memory Usage History")
        
        fig = go.Figure(data=[
            go.Scatter(
                x=historical_data['timestamps'],
                y=historical_data['memory_usage'],
                mode='lines+markers',
                name='Memory Usage',
                line=dict(color='green')
            )
        ])
        
        fig.update_layout(
            title=f"Memory Usage - {time_range}",
            xaxis_title="Time",
            yaxis_title="Usage (%)"
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Performance statistics
        st.subheader("📈 Performance Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_cpu = sum(historical_data['cpu_usage']) / len(historical_data['cpu_usage'])
            st.metric("Avg CPU", f"{avg_cpu:.1f}%")
        
        with col2:
            avg_memory = sum(historical_data['memory_usage']) / len(historical_data['memory_usage'])
            st.metric("Avg Memory", f"{avg_memory:.1f}%")
        
        with col3:
            max_cpu = max(historical_data['cpu_usage'])
            st.metric("Peak CPU", f"{max_cpu:.1f}%")
        
        with col4:
            max_memory = max(historical_data['memory_usage'])
            st.metric("Peak Memory", f"{max_memory:.1f}%")
    else:
        st.info("No historical data available.")

def render_system_configuration():
    """Render system configuration interface"""
    
    st.subheader("🔧 System Configuration")
    
    # Environment variables
    st.subheader("🌍 Environment Variables")
    
    # Filter environment variables
    env_filter = st.text_input(
        "Filter Environment Variables:",
        placeholder="Enter filter...",
        key="env_filter"
    )
    
    # Get environment variables
    env_vars = dict(os.environ)
    
    if env_filter:
        filtered_env = {k: v for k, v in env_vars.items() if env_filter.lower() in k.lower()}
    else:
        # Show only SafeClaw-related variables by default
        safeclaw_env = {k: v for k, v in env_vars.items() if 'safeclaw' in k.lower() or 'llm' in k.lower()}
        if safeclaw_env:
            filtered_env = safeclaw_env
        else:
            filtered_env = dict(list(env_vars.items())[:20])  # Show first 20 if no SafeClaw vars
    
    if filtered_env:
        env_data = []
        for key, value in filtered_env.items():
            # Mask sensitive values
            if any(sensitive in key.lower() for sensitive in ['key', 'token', 'password', 'secret']):
                value = "***MASKED***"
            
            env_data.append({
                "Variable": key,
                "Value": value[:100] + "..." if len(value) > 100 else value
            })
        
        df = pd.DataFrame(env_data)
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No environment variables match the filter.")
    
    # Python environment
    st.subheader("🐍 Python Environment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        import sys
        st.write(f"**Python Version:** {sys.version}")
        st.write(f"**Python Executable:** {sys.executable}")
        st.write(f"**Platform:** {sys.platform}")
        
        import platform
        st.write(f"**System:** {platform.system()}")
        st.write(f"**Release:** {platform.release()}")
        st.write(f"**Version:** {platform.version()}")
    
    with col2:
        import site
        st.write("**Python Path:**")
        for path in sys.path[:5]:  # Show first 5 paths
            st.code(path)
        
        if len(sys.path) > 5:
            st.write(f"... and {len(sys.path) - 5} more paths")
    
    # Installed packages
    st.subheader("📦 Installed Packages")
    
    try:
        import pkg_resources
        
        packages = []
        for package in pkg_resources.working_set:
            packages.append({
                "Package": package.project_name,
                "Version": package.version,
                "Location": package.location
            })
        
        # Sort by package name
        packages.sort(key=lambda x: x["Package"])
        
        # Filter packages
        package_filter = st.text_input(
            "Filter Packages:",
            placeholder="Enter filter...",
            key="package_filter"
        )
        
        if package_filter:
            filtered_packages = [p for p in packages if package_filter.lower() in p["Package"].lower()]
        else:
            # Show SafeClaw-related packages first
            safeclaw_packages = [p for p in packages if 'safeclaw' in p["Package"].lower()]
            other_packages = [p for p in packages if 'safeclaw' not in p["Package"].lower()]
            filtered_packages = safeclaw_packages + other_packages[:20]
        
        if filtered_packages:
            df = pd.DataFrame(filtered_packages)
            st.dataframe(df, width='stretch', hide_index=True)
        else:
            st.info("No packages match the filter.")
    
    except ImportError:
        st.info("pkg_resources not available. Cannot list installed packages.")

def render_system_logs():
    """Render system logs interface"""
    
    st.subheader("📋 System Logs")
    
    # Log file selection
    log_files = get_available_log_files()
    
    if log_files:
        selected_log = st.selectbox(
            "Select Log File:",
            options=log_files,
            key="log_file_selection"
        )
        
        if selected_log:
            render_log_file(selected_log)
    else:
        st.info("No log files found.")
    
    # Log filtering
    st.subheader("🔍 Log Filtering")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_level = st.selectbox(
            "Log Level:",
            ["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            key="log_level_filter"
        )
    
    with col2:
        time_range = st.selectbox(
            "Time Range:",
            ["All", "Last Hour", "Last 6 Hours", "Last 24 Hours"],
            key="log_time_range"
        )
    
    with col3:
        search_term = st.text_input(
            "Search Term:",
            placeholder="Enter search term...",
            key="log_search_term"
        )
    
    # Refresh logs
    if st.button("🔄 Refresh Logs", key="refresh_logs"):
        st.rerun()

def get_available_log_files() -> List[str]:
    """Get list of available log files"""
    log_files = []
    
    # Common log locations
    log_locations = [
        "./logs",
        "./workspace/logs",
        "/var/log",
        os.path.expanduser("~/.local/share/logs")
    ]
    
    for location in log_locations:
        if os.path.exists(location):
            for file in os.listdir(location):
                if file.endswith('.log'):
                    log_files.append(os.path.join(location, file))
    
    return log_files

def render_log_file(log_file: str):
    """Render contents of a log file"""
    
    try:
        with open(log_file, 'r') as f:
            log_content = f.read()
        
        st.subheader(f"📄 {os.path.basename(log_file)}")
        
        # Show file info
        file_stat = os.stat(log_file)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Size:** {format_bytes(file_stat.st_size)}")
        
        with col2:
            st.write(f"**Modified:** {datetime.fromtimestamp(file_stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col3:
            st.write(f"**Lines:** {len(log_content.splitlines())}")
        
        # Display log content
        line_count = st.number_input(
            "Number of lines to display:",
            min_value=10,
            max_value=1000,
            value=100,
            step=10,
            key="log_line_count"
        )
        
        # Get last N lines
        lines = log_content.splitlines()
        display_lines = lines[-line_count:] if len(lines) > line_count else lines
        
        # Display logs
        log_text = "\n".join(display_lines)
        
        st.text_area(
            "Log Content:",
            value=log_text,
            height=400,
            key="log_content_display"
        )
        
        # Download log
        st.download_button(
            label="📥 Download Log File",
            data=log_content,
            file_name=os.path.basename(log_file),
            mime="text/plain"
        )
    
    except Exception as e:
        st.error(f"Error reading log file: {str(e)}")

def get_system_uptime() -> str:
    """Get system uptime"""
    try:
        boot_time = psutil.boot_time()
        uptime = datetime.now() - datetime.fromtimestamp(boot_time)
        
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m {seconds}s"
    except:
        return "Unknown"

def format_bytes(bytes_value: int) -> str:
    """Format bytes in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} PB"

def get_historical_performance_data(time_range: str) -> Dict[str, List]:
    """Get historical performance data (simulated)"""
    # In a real implementation, this would fetch from a database or log files
    # For now, we'll simulate some data
    
    import random
    from datetime import datetime, timedelta
    
    # Determine time range
    if time_range == "Last Hour":
        points = 60
        interval = timedelta(minutes=1)
    elif time_range == "Last 6 Hours":
        points = 72
        interval = timedelta(minutes=5)
    elif time_range == "Last 24 Hours":
        points = 96
        interval = timedelta(minutes=15)
    elif time_range == "Last Week":
        points = 168
        interval = timedelta(hours=1)
    else:
        points = 24
        interval = timedelta(hours=1)
    
    # Generate simulated data
    timestamps = []
    cpu_usage = []
    memory_usage = []
    
    current_time = datetime.now()
    
    for i in range(points):
        timestamp = current_time - (interval * i)
        timestamps.append(timestamp)
        
        # Simulate CPU usage (0-100%)
        cpu_usage.append(random.uniform(10, 80))
        
        # Simulate memory usage (0-100%)
        memory_usage.append(random.uniform(20, 70))
    
    # Reverse to get chronological order
    timestamps.reverse()
    cpu_usage.reverse()
    memory_usage.reverse()
    
    return {
        "timestamps": timestamps,
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage
    }
