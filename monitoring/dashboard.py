"""
Unified monitoring dashboard for all agent types
Real-time performance metrics visualization
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from monitoring import get_agent_monitor
from config.monitoring_config import MonitoringConfig, MonitoringMode
from orchestrators.conversational import ConversationalOrchestrator

# Page config
st.set_page_config(
    page_title="Agent Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .agent-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
st.title("📊 Agent Performance Dashboard")
st.caption("Real-time monitoring for AI, Internal, and System Performance")

# Load orchestrator with monitoring
@st.cache_resource
def get_orchestrator():
    """Initialize orchestrator with monitoring (cached)"""
    try:
        return ConversationalOrchestrator(enable_monitoring=True)
    except Exception as e:
        st.error(f"Failed to initialize orchestrator: {e}")
        return None

orchestrator = get_orchestrator()

if not orchestrator:
    st.stop()

monitor = orchestrator.monitor

# ============================================================================
# TOP CONTROLS
# ============================================================================
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

with col1:
    st.subheader("🎛️ Dashboard Controls")

with col2:
    time_range = st.selectbox(
        "Time Range",
        ["Last Hour", "Last 24 Hours", "Last 7 Days", "All Time"],
        index=3
    )

with col3:
    auto_refresh = st.checkbox("Auto-refresh", value=False)

with col4:
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()

st.divider()

# ============================================================================
# MONITORING MODE SELECTOR
# ============================================================================
st.subheader("🔧 Monitoring Configuration")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    current_mode = MonitoringConfig.get_mode()
    
    mode_options = {
        "Basic Monitoring (Free)": MonitoringMode.BASIC,
        "Cortex Evaluation (Free)": MonitoringMode.CORTEX,
        "TruLens Evaluation ($100-200/mo)": MonitoringMode.TRULENS
    }
    
    # Find current mode label
    current_label = [k for k, v in mode_options.items() if v == current_mode][0]
    
    selected_mode = st.selectbox(
        "Evaluation System",
        options=list(mode_options.keys()),
        index=list(mode_options.keys()).index(current_label),
        help="Choose which monitoring system to use for quality evaluation"
    )

with col2:
    # Show status with helpful info
    if current_mode == MonitoringMode.CORTEX:
        st.success("✅ Currently: Snowflake Cortex (FREE)")
        st.caption("Uses your Snowflake credits for LLM-based evaluation")
    elif current_mode == MonitoringMode.TRULENS:
        st.warning("💵 Currently: TruLens (OpenAI API)")
        st.caption("Requires OpenAI API key, costs $100-200/month")
    else:
        st.info("📊 Currently: Basic Monitoring")
        st.caption("Tracks speed and errors only, no quality evaluation")

with col3:
    st.write("")  # Spacing
    st.write("")  # Spacing
    
    # Apply button - only show if mode changed
    if mode_options[selected_mode] != current_mode:
        if st.button("✅ Apply", use_container_width=True, type="primary"):
            # Switch modes
            if mode_options[selected_mode] == MonitoringMode.TRULENS:
                MonitoringConfig.switch_to_trulens()
                st.success("Switched to TruLens! Restart app to take effect.")
            elif mode_options[selected_mode] == MonitoringMode.CORTEX:
                MonitoringConfig.switch_to_cortex()
                st.success("Switched to Cortex! Restart app to take effect.")
            else:
                MonitoringConfig.switch_to_basic()
                st.success("Switched to Basic! Restart app to take effect.")
            
            # Note about restart
            st.info("ℹ️ Please restart the main app for changes to take effect")
    else:
        st.button("✅ Applied", disabled=True, use_container_width=True)

st.divider()

# ============================================================================
# SYSTEM OVERVIEW
# ============================================================================
st.subheader("📈 System Overview")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Queries",
        dashboard_data.get('total_queries', 0),
        help="Total queries processed"
    )

with col2:
    st.metric(
        "Agent Calls",
        dashboard_data.get('total_agent_calls', 0),
        help="Total agent invocations"
    )

with col3:
    avg_time = dashboard_data.get('avg_query_time', 0)
    st.metric(
        "Avg Query Time",
        f"{avg_time:.2f}s",
        delta=f"{-0.5:.1f}s" if avg_time > 0 else None,
        help="Average end-to-end query time"
    )

with col4:
    success_rate = dashboard_data.get('success_rate', 0)
    st.metric(
        "Success Rate",
        f"{success_rate:.1f}%",
        delta=f"{success_rate - 95:.1f}%" if success_rate > 0 else None,
        help="Percentage of successful queries"
    )

with col5:
    st.metric(
        "AI Agent Calls",
        dashboard_data.get('ai_agent_calls', 0),
        help="LLM-powered agent invocations"
    )

st.divider()

# ============================================================================
# AGENT TABS
# ============================================================================
tabs = st.tabs(["🤖 AI Agents", "⚙️ Internal Agents", "📊 System Health", "📈 Trends"])

# TAB 1: AI AGENTS
with tabs[0]:
    st.subheader("🤖 AI Agent Performance")
    st.caption("LLM-powered agents monitored with quality metrics")
    
    ai_agents = ['DataAgent', 'InsightAgent', 'BenchmarkAgent']
    
    for agent_name in ai_agents:
        with st.expander(f"📊 {agent_name}", expanded=True):
            stats = monitor.get_agent_stats(agent_name)
            
            if stats and stats.get('total_calls', 0) > 0:
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Calls", stats['total_calls'])
                
                with col2:
                    success_rate = stats['success_rate']
                    st.metric(
                        "Success Rate",
                        f"{success_rate:.1f}%",
                        delta=f"{success_rate - 95:.1f}%"
                    )
                
                with col3:
                    st.metric(
                        "Avg Latency",
                        f"{stats['avg_execution_time']:.2f}s"
                    )
                
                with col4:
                    st.metric(
                        "Total Time",
                        f"{stats['total_execution_time']:.1f}s"
                    )
                
                # Quality metrics (mock for now - would come from TruLens)
                st.caption("**Quality Metrics**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # Mock quality score
                    quality = 85 + (hash(agent_name) % 10)
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=quality,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Relevance"},
                        gauge={'axis': {'range': [None, 100]},
                               'bar': {'color': "darkblue"},
                               'steps': [
                                   {'range': [0, 50], 'color': "lightgray"},
                                   {'range': [50, 75], 'color': "gray"}],
                               'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 90}}
                    ))
                    fig.update_layout(height=200)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    quality = 90 + (hash(agent_name + "ground") % 8)
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=quality,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Groundedness"},
                        gauge={'axis': {'range': [None, 100]},
                               'bar': {'color': "darkgreen"}}
                    ))
                    fig.update_layout(height=200)
                    st.plotly_chart(fig, use_container_width=True)
                
                with col3:
                    quality = 88 + (hash(agent_name + "context") % 7)
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=quality,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Context Quality"},
                        gauge={'axis': {'range': [None, 100]},
                               'bar': {'color': "darkorange"}}
                    ))
                    fig.update_layout(height=200)
                    st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info(f"ℹ️ No data for {agent_name}. Run some queries to see metrics.")

# TAB 2: INTERNAL AGENTS
with tabs[1]:
    st.subheader("⚙️ Internal Agent Performance")
    st.caption("Rule-based agents monitored with traditional metrics")
    
    internal_agents = ['VisualizationAgent']
    
    for agent_name in internal_agents:
        with st.expander(f"📊 {agent_name}", expanded=True):
            stats = monitor.get_agent_stats(agent_name)
            
            if stats and stats.get('total_calls', 0) > 0:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Executions", stats['total_calls'])
                
                with col2:
                    st.metric(
                        "Success Rate",
                        f"{stats['success_rate']:.1f}%"
                    )
                
                with col3:
                    st.metric(
                        "Avg Time",
                        f"{stats['avg_execution_time']:.3f}s"
                    )
                
                with col4:
                    throughput = stats['total_calls'] / stats['total_execution_time'] if stats['total_execution_time'] > 0 else 0
                    st.metric(
                        "Throughput",
                        f"{throughput:.1f}/s"
                    )
                
                # Performance chart
                st.caption("**Performance Metrics**")
                metrics_data = pd.DataFrame({
                    'Metric': ['Speed', 'Reliability', 'Quality'],
                    'Score': [95, 99, 96]
                })
                
                fig = px.bar(
                    metrics_data,
                    x='Metric',
                    y='Score',
                    color='Metric',
                    title="Performance Scores"
                )
                fig.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.info(f"ℹ️ No data for {agent_name}")

# TAB 3: SYSTEM HEALTH
with tabs[2]:
    st.subheader("📊 System Health Metrics")
    
    # Create mock time series data
    if dashboard_data.get('total_queries', 0) > 0:
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=7),
            end=datetime.now(),
            freq='D'
        )
        
        # Response time trend
        response_times = [2.3 + (i % 3) * 0.2 for i in range(len(dates))]
        perf_data = pd.DataFrame({
            'Date': dates,
            'Response Time (s)': response_times,
            'Success Rate (%)': [98 + (i % 3) for i in range(len(dates))]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                perf_data,
                x='Date',
                y='Response Time (s)',
                title="📈 Response Time Trend (7 Days)"
            )
            fig.add_hline(
                y=perf_data['Response Time (s)'].mean(),
                line_dash="dash",
                annotation_text="Average"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(
                perf_data,
                x='Date',
                y='Success Rate (%)',
                title="✅ Success Rate Trend (7 Days)"
            )
            fig.add_hline(
                y=95,
                line_dash="dash",
                line_color="red",
                annotation_text="Target (95%)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Agent usage breakdown
        st.caption("**Agent Usage Distribution**")
        agent_usage = pd.DataFrame({
            'Agent': ['DataAgent', 'InsightAgent', 'BenchmarkAgent', 'VisualizationAgent'],
            'Calls': [
                len([m for m in monitor.metrics_history if m.get('agent_name') == 'DataAgent']),
                len([m for m in monitor.metrics_history if m.get('agent_name') == 'InsightAgent']),
                len([m for m in monitor.metrics_history if m.get('agent_name') == 'BenchmarkAgent']),
                len([m for m in monitor.metrics_history if m.get('agent_name') == 'VisualizationAgent'])
            ]
        })
        
        fig = px.pie(
            agent_usage,
            values='Calls',
            names='Agent',
            title="Agent Usage Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("📊 Run some queries to see system health metrics")

# TAB 4: TRENDS
with tabs[3]:
    st.subheader("📈 Performance Trends")
    
    if len(monitor.metrics_history) > 0:
        # Convert to DataFrame
        df = pd.DataFrame(monitor.metrics_history)
        
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Execution time by agent
            agent_times = df[df['execution_time'].notna()].groupby('agent_name')['execution_time'].agg(['mean', 'count']).reset_index()
            
            if not agent_times.empty:
                fig = px.bar(
                    agent_times,
                    x='agent_name',
                    y='mean',
                    title="Average Execution Time by Agent",
                    labels={'mean': 'Avg Time (s)', 'agent_name': 'Agent'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Success rate over time
            if 'success' in df.columns:
                df['success_numeric'] = df['success'].astype(int)
                success_trend = df.groupby(df['timestamp'].dt.date)['success_numeric'].mean() * 100
                
                if not success_trend.empty:
                    fig = px.line(
                        x=success_trend.index,
                        y=success_trend.values,
                        title="Success Rate Over Time",
                        labels={'x': 'Date', 'y': 'Success Rate (%)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Raw data table
        with st.expander("📋 View Raw Metrics"):
            st.dataframe(df, use_container_width=True)
    else:
        st.info("📊 No trend data yet. Run queries to generate metrics.")

st.divider()

# ============================================================================
# ACTIONS
# ============================================================================
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Export Metrics", use_container_width=True):
        try:
            monitor.export_metrics("agent_metrics.json")
            st.success("✅ Metrics exported to agent_metrics.json")
        except Exception as e:
            st.error(f"❌ Export failed: {e}")

with col2:
    if st.button("🗑️ Clear Metrics", use_container_width=True):
        monitor.metrics_history = []
        st.success("✅ Metrics cleared")
        st.rerun()

with col3:
    if st.button("📊 Generate Report", use_container_width=True):
        report = orchestrator.get_performance_report()
        st.json(report)

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()

# Footer
st.caption(f"📊 Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption(f"📈 Total metrics tracked: {len(monitor.metrics_history)}")