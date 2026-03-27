"""Skill manager component for SafeClaw"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from safe_claw.core.skills.registry import SkillRegistry
from safe_claw.core.skills.base_skill import BaseSkill

def render_skill_manager(skill_registry: SkillRegistry):
    """Render skill management interface"""
    
    st.subheader("🔧 Skill Manager")
    
    # Get registry info
    registry_info = skill_registry.get_registry_info()
    
    # Overview statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Skills", registry_info["total_skills"])
    with col2:
        st.metric("Categories", len(registry_info["categories"]))
    with col3:
        total_executions = sum(info["usage_count"] for info in registry_info["skills"].values())
        st.metric("Total Executions", total_executions)
    with col4:
        if registry_info["skills"]:
            most_used = max(registry_info["skills"].values(), key=lambda x: x["usage_count"])
            st.metric("Most Used", most_used["name"])
    
    # Tab interface
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Browse Skills", "🔍 Search Skills", "📊 Statistics", "⚙️ Skill Testing"])
    
    with tab1:
        render_skill_browser(skill_registry, registry_info)
    
    with tab2:
        render_skill_search(skill_registry)
    
    with tab3:
        render_skill_statistics(skill_registry, registry_info)
    
    with tab4:
        render_skill_testing(skill_registry)

def render_skill_browser(skill_registry: SkillRegistry, registry_info: Dict):
    """Render skill browser interface"""
    
    st.subheader("📋 Skill Browser")
    
    # Category filter
    categories = ["All"] + list(registry_info["categories"].keys())
    selected_category = st.selectbox(
        "Filter by Category:",
        categories,
        key="skill_category_filter"
    )
    
    # Get skills to display
    if selected_category == "All":
        skills = skill_registry.get_all_skills()
    else:
        skills = skill_registry.get_skills_by_category(selected_category)
    
    if skills:
        # Sort by usage count
        sorted_skills = sorted(skills.items(), key=lambda x: x[1].usage_count, reverse=True)
        
        # Skill selection
        skill_options = {name: f"{skill.name} - {skill.description}" for name, skill in sorted_skills}
        selected_skill_name = st.selectbox(
            "Select Skill:",
            options=list(skill_options.keys()),
            format_func=lambda x: skill_options[x],
            key="skill_selection"
        )
        
        if selected_skill_name:
            skill = skills[selected_skill_name]
            render_skill_details(skill, skill_registry)
    else:
        st.info(f"No skills found in category: {selected_category}")

def render_skill_details(skill: BaseSkill, skill_registry: SkillRegistry):
    """Render detailed skill information"""
    
    st.subheader(f"🔧 {skill.name}")
    
    # Skill information
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Description:**")
        st.write(skill.description)
        
        st.write("**Category:**")
        st.write(skill.category)
        
        st.write("**Usage Count:**")
        st.write(skill.usage_count)
        
        st.write("**Created At:**")
        st.write(skill.created_at.strftime("%Y-%m-%d %H:%M:%S"))
    
    with col2:
        # Skill operations
        st.write("**Operations:**")
        
        if st.button("🧪 Test Skill", key=f"test_{skill.name}"):
            st.session_state[f"test_skill_{skill.name}"] = True
        
        if st.button("📊 View Usage", key=f"usage_{skill.name}"):
            st.session_state[f"usage_{skill.name}"] = True
        
        if st.button("📤 Export Skill", key=f"export_{skill.name}"):
            export_skill_info(skill)
    
    # Parameters
    st.subheader("📝 Parameters")
    parameters = skill.get_parameters()
    
    if parameters:
        # Display parameter schema
        st.json(parameters)
        
        # Parameter input form
        st.write("**Test Parameters:**")
        parameter_values = {}
        
        if "properties" in parameters:
            for param_name, param_info in parameters["properties"].items():
                param_type = param_info.get("type", "string")
                param_default = param_info.get("default")
                param_description = param_info.get("description", "")
                
                # Create input based on type
                if param_type == "string":
                    if param_name.lower() in ["password", "token", "key"]:
                        value = st.text_input(
                            f"{param_name} ({param_description})",
                            value=param_default or "",
                            type="password",
                            key=f"param_{param_name}"
                        )
                    else:
                        value = st.text_input(
                            f"{param_name} ({param_description})",
                            value=param_default or "",
                            key=f"param_{param_name}"
                        )
                elif param_type == "integer":
                    value = st.number_input(
                        f"{param_name} ({param_description})",
                        value=int(param_default) if param_default else 0,
                        key=f"param_{param_name}"
                    )
                elif param_type == "number":
                    value = st.number_input(
                        f"{param_name} ({param_description})",
                        value=float(param_default) if param_default else 0.0,
                        key=f"param_{param_name}"
                    )
                elif param_type == "boolean":
                    value = st.checkbox(
                        f"{param_name} ({param_description})",
                        value=bool(param_default) if param_default is not None else False,
                        key=f"param_{param_name}"
                    )
                else:
                    value = st.text_input(
                        f"{param_name} ({param_description})",
                        value=str(param_default) if param_default else "",
                        key=f"param_{param_name}"
                    )
                
                parameter_values[param_name] = value
        
        # Execute skill button
        if st.button("🚀 Execute Skill", key=f"execute_{skill.name}"):
            execute_skill(skill, parameter_values, skill_registry)
    
    else:
        st.info("No parameters required for this skill.")

def execute_skill(skill: BaseSkill, parameters: Dict[str, Any], skill_registry: SkillRegistry):
    """Execute skill with parameters"""
    st.subheader(f"🚀 Executing {skill.name}")
    
    # Validate parameters
    is_valid, error_msg = skill.validate_parameters(parameters)
    
    if not is_valid:
        st.error(f"Parameter validation failed: {error_msg}")
        return
    
    # Show execution progress
    with st.spinner(f"Executing {skill.name}..."):
        try:
            # Execute skill
            start_time = datetime.now()
            result = skill.execute(**parameters)
            end_time = datetime.now()
            
            # Update usage count
            skill.increment_usage()
            
            # Display results
            st.success("✅ Skill executed successfully!")
            
            # Execution info
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Execution Time:**")
                st.write(f"{(end_time - start_time).total_seconds():.3f} seconds")
                
                st.write("**Usage Count:**")
                st.write(skill.usage_count)
            
            with col2:
                st.write("**Skill Name:**")
                st.write(skill.name)
                
                st.write("**Category:**")
                st.write(skill.category)
            
            # Results
            st.subheader("📊 Results")
            
            if isinstance(result, dict):
                if result.get("success"):
                    st.success("Operation successful!")
                    
                    # Display result data
                    if "result" in result:
                        if isinstance(result["result"], (str, int, float, bool)):
                            st.write("**Result:**")
                            st.write(result["result"])
                        elif isinstance(result["result"], dict):
                            st.write("**Result Data:**")
                            st.json(result["result"])
                        elif isinstance(result["result"], list):
                            st.write("**Result List:**")
                            for i, item in enumerate(result["result"]):
                                st.write(f"{i+1}. {item}")
                    
                    # Display other fields
                    for key, value in result.items():
                        if key not in ["success", "result", "error"]:
                            st.write(f"**{key.replace('_', ' ').title()}:**")
                            if isinstance(value, (dict, list)):
                                st.json(value)
                            else:
                                st.write(value)
                else:
                    st.error("Operation failed!")
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
            else:
                st.write("**Result:**")
                st.write(result)
            
        except Exception as e:
            st.error(f"Error executing skill: {str(e)}")

def render_skill_search(skill_registry: SkillRegistry):
    """Render skill search interface"""
    
    st.subheader("🔍 Skill Search")
    
    # Search input
    search_query = st.text_input(
        "Search Skills:",
        placeholder="Enter keywords to search skills...",
        key="skill_search_query"
    )
    
    if search_query:
        # Search skills
        search_results = skill_registry.search_skills(search_query)
        
        if search_results:
            st.success(f"Found {len(search_results)} skills matching '{search_query}'")
            
            # Display results
            for i, result in enumerate(search_results):
                skill_info = result["skill"]
                relevance_score = result["relevance_score"]
                
                with st.expander(f"🔧 {skill_info['name']} (Relevance: {relevance_score})", expanded=i == 0):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Description:** {skill_info['description']}")
                        st.write(f"**Category:** {skill_info['category']}")
                        st.write(f"**Usage Count:** {skill_info['usage_count']}")
                        
                        # Parameters preview
                        if skill_info.get("parameters"):
                            st.write(f"**Parameters:** {len(skill_info['parameters'].get('properties', {}))} required")
                    
                    with col2:
                        st.write(f"**Relevance:** {relevance_score}")
                        
                        # Quick actions
                        if st.button(f"🧪 Test", key=f"quick_test_{i}"):
                            st.session_state[f"test_skill_{skill_info['name']}"] = True
        else:
            st.warning(f"No skills found matching '{search_query}'")
    
    # Advanced search
    st.subheader("🔍 Advanced Search")
    
    col1, col2 = st.columns(2)
    
    with col1:
        category_filter = st.selectbox(
            "Filter by Category:",
            ["All"] + list(skill_registry.get_registry_info()["categories"].keys()),
            key="advanced_category_filter"
        )
    
    with col2:
        usage_filter = st.selectbox(
            "Filter by Usage:",
            ["All", "Used", "Unused"],
            key="advanced_usage_filter"
        )
    
    if st.button("🔍 Apply Filters", key="apply_advanced_filters"):
        apply_advanced_filters(skill_registry, category_filter, usage_filter)

def apply_advanced_filters(skill_registry: SkillRegistry, category: str, usage: str):
    """Apply advanced filters to skill search"""
    
    skills = skill_registry.get_all_skills()
    filtered_skills = {}
    
    for name, skill in skills.items():
        # Category filter
        if category != "All" and skill.category != category:
            continue
        
        # Usage filter
        if usage == "Used" and skill.usage_count == 0:
            continue
        elif usage == "Unused" and skill.usage_count > 0:
            continue
        
        filtered_skills[name] = skill
    
    if filtered_skills:
        st.success(f"Found {len(filtered_skills)} skills matching filters")
        
        # Display filtered skills
        for name, skill in filtered_skills.items():
            with st.expander(f"🔧 {skill.name}", expanded=False):
                st.write(f"**Description:** {skill.description}")
                st.write(f"**Category:** {skill.category}")
                st.write(f"**Usage Count:** {skill.usage_count}")
                st.write(f"**Created:** {skill.created_at.strftime('%Y-%m-%d')}")
    else:
        st.info("No skills match the applied filters.")

def render_skill_statistics(skill_registry: SkillRegistry, registry_info: Dict):
    """Render skill statistics interface"""
    
    st.subheader("📊 Skill Statistics")
    
    # Overall statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_executions = sum(info["usage_count"] for info in registry_info["skills"].values())
    
    with col1:
        st.metric("Total Skills", registry_info["total_skills"])
    with col2:
        st.metric("Total Executions", total_executions)
    with col3:
        st.metric("Categories", len(registry_info["categories"]))
    with col4:
        if registry_info["skills"]:
            avg_executions = total_executions / len(registry_info["skills"])
            st.metric("Avg Executions", f"{avg_executions:.1f}")
    
    # Usage by category
    st.subheader("📈 Usage by Category")
    
    category_stats = {}
    for category, category_info in registry_info["categories"].items():
        category_executions = 0
        for skill_name in category_info["skills"]:
            category_executions += registry_info["skills"][skill_name]["usage_count"]
        category_stats[category] = category_executions
    
    if category_stats:
        import plotly.express as px
        import plotly.graph_objects as go
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=list(category_stats.keys()),
                y=list(category_stats.values()),
                marker_color='lightblue'
            )
        ])
        
        fig.update_layout(
            title="Skill Usage by Category",
            xaxis_title="Category",
            yaxis_title="Total Executions"
        )
        
        st.plotly_chart(fig, width='stretch')
    
    # Top skills
    st.subheader("🏆 Top Used Skills")
    
    # Sort skills by usage
    sorted_skills = sorted(
        registry_info["skills"].items(),
        key=lambda x: x[1]["usage_count"],
        reverse=True
    )
    
    top_skills = sorted_skills[:10]
    
    if top_skills:
        # Create table
        skill_data = []
        for name, info in top_skills:
            skill_data.append({
                "Skill": name,
                "Category": info["category"],
                "Usage Count": info["usage_count"],
                "Created": info["created_at"][:10]
            })
        
        df = pd.DataFrame(skill_data)
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No skill usage data available.")
    
    # Usage distribution
    st.subheader("📊 Usage Distribution")
    
    usage_counts = [info["usage_count"] for info in registry_info["skills"].values()]
    
    if usage_counts:
        # Create histogram
        import plotly.graph_objects as go
        
        fig = go.Figure(data=[
            go.Histogram(
                x=usage_counts,
                nbinsx=10,
                marker_color='lightgreen'
            )
        ])
        
        fig.update_layout(
            title="Skill Usage Distribution",
            xaxis_title="Usage Count",
            yaxis_title="Number of Skills"
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Max Usage", max(usage_counts))
        with col2:
            st.metric("Min Usage", min(usage_counts))
        with col3:
            st.metric("Avg Usage", f"{sum(usage_counts) / len(usage_counts):.1f}")
        with col4:
            unused_count = sum(1 for count in usage_counts if count == 0)
            st.metric("Unused Skills", unused_count)

def render_skill_testing(skill_registry: SkillRegistry):
    """Render skill testing interface"""
    
    st.subheader("⚙️ Skill Testing")
    
    # Select skill to test
    skills = skill_registry.get_all_skills()
    
    if not skills:
        st.info("No skills available for testing.")
        return
    
    skill_options = {name: f"{skill.name} - {skill.category}" for name, skill in skills.items()}
    selected_skill_name = st.selectbox(
        "Select Skill to Test:",
        options=list(skill_options.keys()),
        format_func=lambda x: skill_options[x],
        key="test_skill_selection"
    )
    
    if selected_skill_name:
        skill = skills[selected_skill_name]
        
        st.subheader(f"🧪 Testing {skill.name}")
        
        # Show skill info
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Description:** {skill.description}")
            st.write(f"**Category:** {skill.category}")
        
        with col2:
            st.write(f"**Usage Count:** {skill.usage_count}")
            st.write(f"**Created:** {skill.created_at.strftime('%Y-%m-%d')}")
        
        # Parameter input
        parameters = skill.get_parameters()
        
        if parameters and "properties" in parameters:
            st.write("**Parameters:**")
            
            parameter_values = {}
            
            for param_name, param_info in parameters["properties"].items():
                param_type = param_info.get("type", "string")
                param_default = param_info.get("default")
                param_required = param_name in parameters.get("required", [])
                
                # Create input with validation
                if param_required:
                    label = f"**{param_name}** ({param_info.get('description', '')}) *Required*"
                else:
                    label = f"{param_name} ({param_info.get('description', '')})"
                
                if param_type == "string":
                    if param_name.lower() in ["password", "token", "key"]:
                        value = st.text_input(
                            label,
                            value=param_default or "",
                            type="password",
                            key=f"test_param_{param_name}"
                        )
                    else:
                        value = st.text_input(
                            label,
                            value=param_default or "",
                            key=f"test_param_{param_name}"
                        )
                elif param_type == "integer":
                    value = st.number_input(
                        label,
                        value=int(param_default) if param_default else 0,
                        key=f"test_param_{param_name}"
                    )
                elif param_type == "number":
                    value = st.number_input(
                        label,
                        value=float(param_default) if param_default else 0.0,
                        key=f"test_param_{param_name}"
                    )
                elif param_type == "boolean":
                    value = st.checkbox(
                        label,
                        value=bool(param_default) if param_default is not None else False,
                        key=f"test_param_{param_name}"
                    )
                else:
                    value = st.text_input(
                        label,
                        value=str(param_default) if param_default else "",
                        key=f"test_param_{param_name}"
                    )
                
                parameter_values[param_name] = value
            
            # Test execution
            if st.button("🚀 Execute Test", key=f"execute_test_{skill.name}"):
                execute_skill(skill, parameter_values, skill_registry)
        else:
            st.info("This skill requires no parameters.")
            
            if st.button("🚀 Execute Test", key=f"execute_test_no_params_{skill.name}"):
                execute_skill(skill, {}, skill_registry)

def export_skill_info(skill: BaseSkill):
    """Export skill information"""
    export_data = {
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "usage_count": skill.usage_count,
        "created_at": skill.created_at.isoformat(),
        "parameters": skill.get_parameters(),
        "exported_at": datetime.now().isoformat()
    }
    
    st.json(export_data)
    
    st.download_button(
        label="📥 Download Skill Info",
        data=st.json.dumps(export_data),
        file_name=f"skill_{skill.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )
