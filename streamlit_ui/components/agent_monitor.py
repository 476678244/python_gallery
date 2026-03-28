"""Agent monitor component for SafeClaw"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from streamlit_ui.safe_claw.core.agents.base_agent import BaseAgent
from streamlit_ui.safe_claw.core.graph.state import SafeClawState

def render_agent_monitor(graph_builder, current_graph=None):
    """Render agent monitoring interface"""
    
    st.subheader("🤖 Agent Monitor")
    
    # Get available agents
    agents = get_available_agents(graph_builder)
    
    if not agents:
        st.info("No agents available for monitoring.")
        return
    
    # Agent overview
    render_agent_overview(agents)
    
    # Tab interface
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Agent Status", 
        "🔄 Execution Flow", 
        "📈 Performance Metrics", 
        "🧪 Agent Testing"
    ])
    
    with tab1:
        render_agent_status(agents, graph_builder)
    
    with tab2:
        render_execution_flow(graph_builder, current_graph)
    
    with tab3:
        render_performance_metrics(agents)
    
    with tab4:
        render_agent_testing(graph_builder, agents)

def get_available_agents(graph_builder) -> Dict[str, BaseAgent]:
    """Get available agents from graph builder"""
    agents = {}
    
    # Get agents from graph builder
    if hasattr(graph_builder, 'chat_agent'):
        agents['chat_agent'] = graph_builder.chat_agent
    if hasattr(graph_builder, 'router_agent'):
        agents['router_agent'] = graph_builder.router_agent
    if hasattr(graph_builder, 'memory_agent'):
        agents['memory_agent'] = graph_builder.memory_agent
    if hasattr(graph_builder, 'safety_agent'):
        agents['safety_agent'] = graph_builder.safety_agent
    
    return agents

def render_agent_overview(agents: Dict[str, BaseAgent]):
    """Render agent overview"""
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Agents", len(agents))
    with col2:
        active_agents = sum(1 for agent in agents.values() if hasattr(agent, 'is_active') and agent.is_active)
        st.metric("Active Agents", active_agents)
    with col3:
        total_executions = sum(getattr(agent, 'execution_count', 0) for agent in agents.values())
        st.metric("Total Executions", total_executions)
    with col4:
        if agents:
            avg_executions = total_executions / len(agents)
            st.metric("Avg Executions", f"{avg_executions:.1f}")
    
    # Agent list
    st.subheader("📋 Available Agents")
    
    for name, agent in agents.items():
        with st.expander(f"🤖 {name}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Type:** {type(agent).__name__}")
                st.write(f"**Description:** {getattr(agent, 'description', 'No description')}")
                st.write(f"**Execution Count:** {getattr(agent, 'execution_count', 0)}")
            
            with col2:
                if hasattr(agent, 'is_active'):
                    status = "🟢 Active" if agent.is_active else "🔴 Inactive"
                    st.write(f"**Status:** {status}")
                
                if hasattr(agent, 'last_execution'):
                    st.write(f"**Last Execution:** {agent.last_execution}")
                
                if hasattr(agent, 'average_execution_time'):
                    st.write(f"**Avg Time:** {agent.average_execution_time:.3f}s")

def render_agent_status(agents: Dict[str, BaseAgent], graph_builder):
    """Render detailed agent status"""
    
    st.subheader("📊 Agent Status")
    
    # Agent selection
    selected_agent = st.selectbox(
        "Select Agent:",
        options=list(agents.keys()),
        key="agent_status_selection"
    )
    
    if selected_agent:
        agent = agents[selected_agent]
        
        # Agent details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader(f"🤖 {selected_agent}")
            
            st.write(f"**Type:** {type(agent).__name__}")
            st.write(f"**Description:** {getattr(agent, 'description', 'No description')}")
            
            if hasattr(agent, 'capabilities'):
                st.write("**Capabilities:**")
                for capability in agent.capabilities:
                    st.write(f"• {capability}")
            
            if hasattr(agent, 'configuration'):
                st.write("**Configuration:**")
                st.json(agent.configuration)
        
        with col2:
            st.write("**Status Metrics:**")
            
            execution_count = getattr(agent, 'execution_count', 0)
            st.metric("Executions", execution_count)
            
            if hasattr(agent, 'success_rate'):
                st.metric("Success Rate", f"{agent.success_rate:.1%}")
            
            if hasattr(agent, 'average_execution_time'):
                st.metric("Avg Time", f"{agent.average_execution_time:.3f}s")
            
            if hasattr(agent, 'last_execution'):
                st.metric("Last Execution", agent.last_execution.strftime("%H:%M:%S"))
        
        # Recent executions
        if hasattr(agent, 'execution_history'):
            st.subheader("📋 Recent Executions")
            
            recent_executions = agent.execution_history[-10:]  # Last 10 executions
            
            if recent_executions:
                execution_data = []
                for execution in recent_executions:
                    execution_data.append({
                        "Timestamp": execution.get("timestamp", datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
                        "Status": execution.get("status", "unknown"),
                        "Duration": f"{execution.get('duration', 0):.3f}s",
                        "Input": execution.get("input", "")[:50] + "..." if len(execution.get("input", "")) > 50 else execution.get("input", ""),
                        "Output": execution.get("output", "")[:50] + "..." if len(execution.get("output", "")) > 50 else execution.get("output", "")
                    })
                
                df = pd.DataFrame(execution_data)
                st.dataframe(df, width='stretch', hide_index=True)
            else:
                st.info("No execution history available.")
        
        # Agent controls
        st.subheader("⚙️ Agent Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Restart Agent", key=f"restart_{selected_agent}"):
                restart_agent(agent)
        
        with col2:
            if st.button("📊 Reset Stats", key=f"reset_stats_{selected_agent}"):
                reset_agent_stats(agent)
        
        with col3:
            if st.button("🗑️ Clear History", key=f"clear_history_{selected_agent}"):
                clear_agent_history(agent)

def render_execution_flow(graph_builder, current_graph):
    """Render execution flow visualization"""
    
    st.subheader("🔄 Execution Flow")
    
    # Graph type selection
    graph_types = ["simple_chat", "multi_agent", "advanced"]
    selected_graph_type = st.selectbox(
        "Select Graph Type:",
        options=graph_types,
        key="graph_type_selection"
    )
    
    # Build and visualize graph
    if selected_graph_type == "simple_chat":
        graph = graph_builder.build_simple_chat_graph()
        visualize_graph(graph, "Simple Chat Graph")
    elif selected_graph_type == "multi_agent":
        graph = graph_builder.build_multi_agent_graph()
        visualize_graph(graph, "Multi-Agent Graph")
    elif selected_graph_type == "advanced":
        graph = graph_builder.build_advanced_graph()
        visualize_graph(graph, "Advanced Graph")
    
    # Execution simulation
    st.subheader("🧪 Execution Simulation")
    
    test_input = st.text_input(
        "Test Input:",
        placeholder="Enter input to simulate execution...",
        key="execution_test_input"
    )
    
    session_id = st.text_input(
        "Session ID:",
        value="test_session",
        key="execution_test_session"
    )
    
    if st.button("🚀 Simulate Execution", key="simulate_execution"):
        if test_input:
            simulate_execution(graph_builder, selected_graph_type, test_input, session_id)

def visualize_graph(graph, title: str):
    """Visualize LangGraph execution graph"""
    
    st.subheader(f"📊 {title}")
    
    try:
        # Get graph structure
        graph_dict = graph.get_graph()
        
        # Create visualization
        if hasattr(graph_dict, 'draw_mermaid'):
            st.graphviz_chart(graph_dict.draw_mermaid())
        else:
            # Fallback to text representation
            st.write("**Graph Structure:**")
            st.code(str(graph_dict))
        
        # Node information
        if hasattr(graph_dict, 'nodes'):
            st.subheader("📋 Graph Nodes")
            
            node_data = []
            for node_name, node_info in graph_dict.nodes.items():
                node_data.append({
                    "Node": node_name,
                    "Type": type(node_info).__name__,
                    "Description": getattr(node_info, 'description', 'No description')
                })
            
            df = pd.DataFrame(node_data)
            st.dataframe(df, width='stretch', hide_index=True)
        
        # Edge information
        if hasattr(graph_dict, 'edges'):
            st.subheader("🔗 Graph Edges")
            
            edge_data = []
            for edge in graph_dict.edges:
                edge_data.append({
                    "From": edge[0],
                    "To": edge[1],
                    "Condition": getattr(edge, 'condition', 'Always')
                })
            
            df = pd.DataFrame(edge_data)
            st.dataframe(df, width='stretch', hide_index=True)
    
    except Exception as e:
        st.error(f"Error visualizing graph: {str(e)}")
        st.info("Graph visualization requires additional dependencies.")

def simulate_execution(graph_builder, graph_type: str, test_input: str, session_id: str):
    """Simulate graph execution"""
    
    try:
        # Build graph
        if graph_type == "simple_chat":
            graph = graph_builder.build_simple_chat_graph()
        elif graph_type == "multi_agent":
            graph = graph_builder.build_multi_agent_graph()
        elif graph_type == "advanced":
            graph = graph_builder.build_advanced_graph()
        
        # Create state
        state = SafeClawState(
            user_input=test_input,
            session_id=session_id,
            messages=[],
            start_time=datetime.now()
        )
        
        # Execute with progress tracking
        with st.spinner("Simulating execution..."):
            config = {"configurable": {"thread_id": session_id}}
            
            # Track execution
            start_time = datetime.now()
            result = graph.invoke(state, config)
            end_time = datetime.now()
            
            execution_time = (end_time - start_time).total_seconds()
        
        # Display results
        st.success("✅ Execution completed successfully!")
        
        st.subheader("📊 Execution Results")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Response:** {result.get('response', 'No response')}")
            st.write(f"**Current Agent:** {result.get('current_agent', 'Unknown')}")
            st.write(f"**Execution Path:** {' → '.join(result.get('execution_path', []))}")
        
        with col2:
            st.metric("Execution Time", f"{execution_time:.3f}s")
            st.metric("Messages Processed", len(result.get('messages', [])))
            st.metric("Memory Retrieved", len(result.get('active_memories', [])))
        
        # Detailed execution log
        if 'execution_log' in result:
            st.subheader("📋 Execution Log")
            
            for log_entry in result['execution_log']:
                with st.expander(f"🕐 {log_entry['timestamp'].strftime('%H:%M:%S')} - {log_entry['agent']}"):
                    st.write(f"**Agent:** {log_entry['agent']}")
                    st.write(f"**Action:** {log_entry['action']}")
                    st.write(f"**Duration:** {log_entry['duration']:.3f}s")
                    
                    if 'input' in log_entry:
                        st.write(f"**Input:** {log_entry['input']}")
                    
                    if 'output' in log_entry:
                        st.write(f"**Output:** {log_entry['output']}")
    
    except Exception as e:
        st.error(f"Error simulating execution: {str(e)}")

def render_performance_metrics(agents: Dict[str, BaseAgent]):
    """Render performance metrics"""
    
    st.subheader("📈 Performance Metrics")
    
    # Collect metrics from all agents
    all_metrics = []
    
    for name, agent in agents.items():
        metrics = {
            "Agent": name,
            "Execution Count": getattr(agent, 'execution_count', 0),
            "Success Count": getattr(agent, 'success_count', 0),
            "Error Count": getattr(agent, 'error_count', 0),
            "Avg Execution Time": getattr(agent, 'average_execution_time', 0),
            "Success Rate": getattr(agent, 'success_rate', 0),
            "Last Execution": getattr(agent, 'last_execution', None)
        }
        all_metrics.append(metrics)
    
    if all_metrics:
        # Create DataFrame
        df = pd.DataFrame(all_metrics)
        st.dataframe(df, width='stretch', hide_index=True)
        
        # Performance charts
        st.subheader("📊 Performance Charts")
        
        # Execution count chart
        import plotly.express as px
        import plotly.graph_objects as go
        
        fig1 = go.Figure(data=[
            go.Bar(
                x=df["Agent"],
                y=df["Execution Count"],
                marker_color='lightblue'
            )
        ])
        
        fig1.update_layout(
            title="Execution Count by Agent",
            xaxis_title="Agent",
            yaxis_title="Count"
        )
        
        st.plotly_chart(fig1, width='stretch')
        
        # Success rate chart
        fig2 = go.Figure(data=[
            go.Bar(
                x=df["Agent"],
                y=df["Success Rate"],
                marker_color='lightgreen'
            )
        ])
        
        fig2.update_layout(
            title="Success Rate by Agent",
            xaxis_title="Agent",
            yaxis_title="Success Rate"
        )
        
        st.plotly_chart(fig2, width='stretch')
        
        # Execution time chart
        fig3 = go.Figure(data=[
            go.Bar(
                x=df["Agent"],
                y=df["Avg Execution Time"],
                marker_color='lightcoral'
            )
        ])
        
        fig3.update_layout(
            title="Average Execution Time by Agent",
            xaxis_title="Agent",
            yaxis_title="Time (seconds)"
        )
        
        st.plotly_chart(fig3, width='stretch')
        
        # Performance summary
        st.subheader("📋 Performance Summary")
        
        total_executions = df["Execution Count"].sum()
        total_successes = df["Success Count"].sum()
        total_errors = df["Error Count"].sum()
        overall_success_rate = total_successes / total_executions if total_executions > 0 else 0
        avg_execution_time = df["Avg Execution Time"].mean()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Executions", total_executions)
        with col2:
            st.metric("Total Successes", total_successes)
        with col3:
            st.metric("Total Errors", total_errors)
        with col4:
            st.metric("Overall Success Rate", f"{overall_success_rate:.1%}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Avg Execution Time", f"{avg_execution_time:.3f}s")
        
        with col2:
            if df["Last Execution"].notna().any():
                last_execution = df["Last Execution"].max()
                st.metric("Last Execution", last_execution.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        st.info("No performance data available.")

def render_agent_testing(graph_builder, agents: Dict[str, BaseAgent]):
    """Render agent testing interface"""
    
    st.subheader("🧪 Agent Testing")
    
    # Agent selection
    selected_agent = st.selectbox(
        "Select Agent to Test:",
        options=list(agents.keys()),
        key="agent_test_selection"
    )
    
    if selected_agent:
        agent = agents[selected_agent]
        
        # Test input
        test_input = st.text_area(
            "Test Input:",
            placeholder="Enter input to test agent...",
            height=100,
            key=f"agent_test_input_{selected_agent}"
        )
        
        # Test parameters
        st.subheader("⚙️ Test Parameters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            session_id = st.text_input(
                "Session ID:",
                value=f"test_{selected_agent}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                key=f"test_session_id_{selected_agent}"
            )
            
            timeout = st.number_input(
                "Timeout (seconds):",
                min_value=1,
                max_value=300,
                value=30,
                key=f"test_timeout_{selected_agent}"
            )
        
        with col2:
            enable_debug = st.checkbox(
                "Enable Debug Mode",
                value=True,
                key=f"test_debug_{selected_agent}"
            )
            
            enable_memory = st.checkbox(
                "Enable Memory Retrieval",
                value=True,
                key=f"test_memory_{selected_agent}"
            )
        
        # Run test
        if st.button("🚀 Run Agent Test", key=f"run_agent_test_{selected_agent}"):
            if test_input:
                run_agent_test(agent, test_input, session_id, timeout, enable_debug, enable_memory, graph_builder)
            else:
                st.error("Please enter test input.")

def run_agent_test(agent: BaseAgent, test_input: str, session_id: str, timeout: int, 
                   enable_debug: bool, enable_memory: bool, graph_builder):
    """Run individual agent test"""
    
    try:
        # Create state
        state = SafeClawState(
            user_input=test_input,
            session_id=session_id,
            messages=[],
            start_time=datetime.now()
        )
        
        # Execute agent
        with st.spinner(f"Testing {agent.__class__.__name__}..."):
            start_time = datetime.now()
            
            # Process with agent
            result = agent.process(state)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
        
        # Display results
        st.success("✅ Agent test completed successfully!")
        
        st.subheader("📊 Test Results")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Agent:** {agent.__class__.__name__}")
            st.write(f"**Execution Time:** {execution_time:.3f}s")
            st.write(f"**Session ID:** {session_id}")
            
            if 'response' in result:
                st.write(f"**Response:** {result['response']}")
            
            if 'current_agent' in result:
                st.write(f"**Current Agent:** {result['current_agent']}")
            
            if 'execution_path' in result:
                st.write(f"**Execution Path:** {' → '.join(result['execution_path'])}")
        
        with col2:
            st.metric("Execution Time", f"{execution_time:.3f}s")
            
            if 'messages' in result:
                st.metric("Messages", len(result['messages']))
            
            if 'active_memories' in result:
                st.metric("Memories Retrieved", len(result['active_memories']))
        
        # Debug information
        if enable_debug:
            st.subheader("🐛 Debug Information")
            
            st.write("**Full Result:**")
            st.json(result)
            
            st.write("**State Information:**")
            st.json({
                "user_input": state["user_input"],
                "session_id": state["session_id"],
                "message_count": len(state.get("messages", [])),
                "start_time": state["start_time"].isoformat()
            })
    
    except Exception as e:
        st.error(f"❌ Agent test failed: {str(e)}")
        
        if enable_debug:
            st.subheader("🐛 Error Details")
            st.code(str(e))

def restart_agent(agent: BaseAgent):
    """Restart agent"""
    try:
        if hasattr(agent, 'restart'):
            agent.restart()
            st.success("✅ Agent restarted successfully!")
        else:
            st.warning("⚠️ Agent does not support restart functionality.")
    except Exception as e:
        st.error(f"❌ Failed to restart agent: {str(e)}")

def reset_agent_stats(agent: BaseAgent):
    """Reset agent statistics"""
    try:
        if hasattr(agent, 'reset_stats'):
            agent.reset_stats()
            st.success("✅ Agent statistics reset successfully!")
        else:
            st.warning("⚠️ Agent does not support statistics reset.")
    except Exception as e:
        st.error(f"❌ Failed to reset agent statistics: {str(e)}")

def clear_agent_history(agent: BaseAgent):
    """Clear agent execution history"""
    try:
        if hasattr(agent, 'clear_history'):
            agent.clear_history()
            st.success("✅ Agent history cleared successfully!")
        else:
            st.warning("⚠️ Agent does not support history clearing.")
    except Exception as e:
        st.error(f"❌ Failed to clear agent history: {str(e)}")
