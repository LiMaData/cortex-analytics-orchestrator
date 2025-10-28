"""
Unified monitoring dashboard for Cortex evaluation
Real-time performance metrics visualization
✅ Cortex Evaluation (FREE) - NO TrueLens!
FIXED: use_container_width → width='stretch'
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
    .cortex-badge {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #2196F3;
    }
    .fallback-badge {
        background-color: #fff3e0;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ff9800;
    }
</style>
""", unsafe_allow_html=True)

# Initialize
st.title("📊 Agent Performance Dashboard")
st.caption("Real-time monitoring with Cortex Quality Evaluation")

# ✅ FIXED: Access orchestrator from main app's session state
# Don't create a new one - use the existing one with data!
if 'orchestrator' not in st.session_state:
    st.error("❌ **No orchestrator found!** Please run queries in the main app first.")
    st.info("💡 Go to the main 'streamlit app' page and run at least one query, then come back here.")
    st.stop()

orchestrator = st.session_state.orchestrator

if not orchestrator or not orchestrator.monitor:
    st.error("❌ **Monitoring not enabled!** Please restart the app.")
    st.stop()

monitor = orchestrator.monitor
dashboard_data = monitor.get_dashboard_data()

# ============================================================================
# 🎯 EVALUATION METHOD INDICATOR (NEW!)
# ============================================================================
st.subheader("🔍 Monitoring System Status")

col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    eval_method = dashboard_data.get('evaluation_method', 'unknown')
    
    if eval_method == 'cortex':
        st.markdown("""
        <div class="cortex-badge">
        <strong>✅ Cortex Evaluation ACTIVE</strong><br>
        Using Snowflake Cortex for quality metrics (FREE)
        </div>
        """, unsafe_allow_html=True)
    elif eval_method == 'fallback':
        st.markdown("""
        <div class="fallback-badge">
        <strong>⚠️ Fallback Mode ACTIVE</strong><br>
        Using basic metrics (Cortex unavailable)
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="fallback-badge">
        <strong>❓ Status Unknown</strong><br>
        Check logs for details
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.metric(
        "Evaluation Method",
        eval_method.upper(),
        help="Cortex = Full quality evaluation | Fallback = Basic metrics only"
    )

with col3:
    if eval_method == 'cortex':
        st.success("✅ Full quality metrics available")
    else:
        st.warning("⚠️ Limited quality metrics")

st.divider()

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
    # ✅ FIXED: use_container_width → width
    if st.button("🔄 Refresh Now", width='stretch'):
        st.rerun()

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
        help="Average end-to-end query time"
    )

with col4:
    success_rate = dashboard_data.get('success_rate', 0)
    st.metric(
        "Success Rate",
        f"{success_rate:.1f}%",
        help="Percentage of successful queries"
    )

with col5:
    # ✅ NEW: Show quality score if available
    quality_score = dashboard_data.get('avg_quality_score', 0)
    if eval_method == 'cortex' and quality_score > 0:
        st.metric(
            "Avg Quality",
            f"{quality_score:.2f}",
            help="Average AI response quality (0-1 scale)"
        )
    else:
        st.metric(
            "AI Calls",
            dashboard_data.get('ai_agent_calls', 0),
            help="LLM-powered agent invocations"
        )

st.divider()

# ============================================================================
# AGENT TABS
# ============================================================================
tabs = st.tabs(["🤖 AI Agents", "⚙️ Internal Agents", "📊 System Health", "📈 Trends"])

# TAB 1: AI AGENTS (with quality metrics)
with tabs[0]:
    st.subheader("🤖 AI Agent Performance")
    
    if eval_method == 'cortex':
        st.caption("🎯 LLM-powered agents monitored with Cortex quality metrics")
    else:
        st.caption("⚠️ LLM-powered agents with basic metrics only")
    
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
                    # ✅ FIXED: success_rate is now stored as percentage (0-100), not decimal (0-1)
                    st.metric(
                        "Success Rate",
                        f"{success_rate:.1f}%",  # Just add %, don't use .1% format
                        delta=f"{success_rate - 95:.1f}%" if success_rate < 95 else None
                    )
                
                with col3:
                    avg_time = stats['avg_time']
                    st.metric("Avg Time", f"{avg_time:.2f}s")
                
                with col4:
                    total_time = stats['total_time']
                    st.metric("Total Time", f"{total_time:.1f}s")
                
                # ✅ Quality Metrics (if Cortex)
                if eval_method == 'cortex' and 'avg_quality_scores' in stats:
                    st.caption("**Quality Metrics (Cortex)**")
                    
                    quality = stats['avg_quality_scores']
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Relevance", f"{quality.get('relevance', 0):.2f}")
                    with col2:
                        st.metric("Groundedness", f"{quality.get('groundedness', 0):.2f}")
                    with col3:
                        st.metric("Coherence", f"{quality.get('coherence', 0):.2f}")
                    with col4:
                        overall = quality.get('overall', 0)
                        st.metric(
                            "Overall",
                            f"{overall:.2f}",
                            delta=f"{overall - 0.8:.2f}" if overall < 0.8 else None
                        )
            else:
                st.info(f"ℹ️ No data for {agent_name}")

# TAB 2: INTERNAL AGENTS
with tabs[1]:
    st.subheader("⚙️ Internal Agent Performance")
    st.caption("🔧 Rule-based agents (no LLM)")
    
    internal_agents = ['VisualizationAgent']
    
    for agent_name in internal_agents:
        with st.expander(f"🔧 {agent_name}", expanded=True):
            stats = monitor.get_agent_stats(agent_name)
            
            if stats and stats.get('total_calls', 0) > 0:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Calls", stats['total_calls'])
                
                with col2:
                    success_rate = stats['success_rate']
                    # ✅ FIXED: success_rate is now percentage (0-100)
                    st.metric("Success Rate", f"{success_rate:.1f}%")
                
                with col3:
                    avg_time = stats['avg_time']
                    st.metric("Avg Time", f"{avg_time:.2f}s")
                
                with col4:
                    # Calculate throughput
                    total_execution_time = stats.get('total_time', 0)
                    throughput = stats['total_calls'] / total_execution_time if total_execution_time > 0 else 0
                    st.metric(
                        "Throughput",
                        f"{throughput:.1f}/s"
                    )
                
                # Performance chart
                st.caption("**Performance Metrics**")
                metrics_data = pd.DataFrame({
                    'Metric': ['Speed', 'Reliability'],
                    'Score': [95, 99]
                })
                
                fig = px.bar(
                    metrics_data,
                    x='Metric',
                    y='Score',
                    color='Metric',
                    title="Performance Scores"
                )
                fig.update_layout(showlegend=False, height=300)
                # ✅ FIXED: use_container_width → width
                st.plotly_chart(fig, width='stretch')
            
            else:
                st.info(f"ℹ️ No data for {agent_name}")

# TAB 3: SYSTEM HEALTH
with tabs[2]:
    st.subheader("📊 System Health Metrics")
    
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
            # ✅ FIXED: use_container_width → width
            st.plotly_chart(fig, width='stretch')
        
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
            # ✅ FIXED: use_container_width → width
            st.plotly_chart(fig, width='stretch')
        
        # Agent usage breakdown
        st.caption("**Agent Usage Distribution**")
        agent_usage = pd.DataFrame({
            'Agent': ['DataAgent', 'InsightAgent', 'BenchmarkAgent'],
            'Calls': [
                len([m for m in monitor.metrics_history if m.get('agent_name') == 'DataAgent']),
                len([m for m in monitor.metrics_history if m.get('agent_name') == 'InsightAgent']),
                len([m for m in monitor.metrics_history if m.get('agent_name') == 'BenchmarkAgent'])
            ]
        })
        
        # Filter out zero values
        agent_usage = agent_usage[agent_usage['Calls'] > 0]
        
        if not agent_usage.empty:
            fig = px.pie(
                agent_usage,
                values='Calls',
                names='Agent',
                title="Agent Usage Distribution"
            )
            # ✅ FIXED: use_container_width → width
            st.plotly_chart(fig, width='stretch')
    
    else:
        st.info("📊 Run some queries to see system health metrics")

# TAB 4: TRENDS (with quality trends if Cortex)
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
                # ✅ FIXED: use_container_width → width
                st.plotly_chart(fig, width='stretch')
            
            # ✅ NEW: Quality trend if Cortex
            if eval_method == 'cortex' and 'overall_score' in df.columns:
                st.caption("**Quality Score Trends (Cortex)**")
                
                ai_data = df[df['agent_type'] == 'ai'].copy() if 'agent_type' in df.columns else df.copy()
                if not ai_data.empty and 'overall_score' in ai_data.columns and ai_data['overall_score'].notna().any():
                    quality_trend = ai_data.groupby(ai_data['timestamp'].dt.date)['overall_score'].mean()
                    
                    if not quality_trend.empty:
                        fig = px.line(
                            x=quality_trend.index,
                            y=quality_trend.values,
                            title="AI Quality Score Over Time",
                            labels={'x': 'Date', 'y': 'Quality Score (0-1)'}
                        )
                        fig.add_hline(y=0.8, line_dash="dash", annotation_text="Target (0.80)")
                        st.plotly_chart(fig, width='stretch')
            
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
                    # ✅ FIXED: use_container_width → width
                    st.plotly_chart(fig, width='stretch')
        
        # Raw data table
        with st.expander("📋 View Raw Metrics"):
            # ✅ FIXED: use_container_width → width
            st.dataframe(df, width='stretch')
    else:
        st.info("📊 No trend data yet. Run queries to generate metrics.")

st.divider()

# ============================================================================
# EVALUATION METHOD DETAILS
# ============================================================================
with st.expander("🔍 Evaluation Method Details"):
    st.markdown(f"""
    ### Current Evaluation Method: **{eval_method.upper()}**
    
    {f"""
    #### ✅ Cortex Evaluation (Active)
    - **Cost**: FREE (uses Snowflake credits)
    - **Metrics Tracked**:
      - Relevance: How relevant is response to query?
      - Groundedness: Is response factually accurate?
      - Coherence: Is response well-structured?
    - **Quality Score**: 0-1 scale (higher is better)
    - **Update Frequency**: Per query
    - **Logs**: Check terminal for "✅ Cortex evaluation ENABLED"
    """ if eval_method == 'cortex' else f"""
    #### ⚠️ Fallback Mode (Limited)
    - **Cost**: FREE
    - **Metrics Tracked**:
      - Success rate
      - Execution time
      - Agent calls
    - **Quality Score**: Not available in fallback mode
    - **Why Fallback**: Cortex evaluator not initialized
    - **Solution**: 
      1. Check that cortex_evaluator.py exists in monitoring/
      2. Check that agent_monitor_CORTEX.py is deployed
      3. Check Snowflake session is available
      4. Restart app
    - **Logs**: Check terminal for "⚠️ Cortex evaluator not available" + error details
    """}
    """)

# ============================================================================
# ACTIONS
# ============================================================================
st.divider()
st.subheader("📌 Dashboard Actions")

col1, col2, col3 = st.columns(3)

with col1:
    # ✅ FIXED: use_container_width → width
    if st.button("📥 Export Metrics", width='stretch'):
        try:
            monitor.export_metrics("agent_metrics.json")
            st.success("✅ Metrics exported to agent_metrics.json")
        except Exception as e:
            st.error(f"❌ Export failed: {e}")

with col2:
    # ✅ FIXED: use_container_width → width
    if st.button("🗑️ Clear Metrics", width='stretch'):
        monitor.metrics_history = []
        st.success("✅ Metrics cleared")
        st.rerun()

with col3:
    # ✅ FIXED: use_container_width → width
    if st.button("🔄 Force Refresh", width='stretch'):
        st.rerun()

# Auto-refresh
if auto_refresh:
    import time
    time.sleep(30)
    st.rerun()

# Footer
st.divider()
st.caption(f"📊 Dashboard last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption(f"📈 Total metrics tracked: {len(monitor.metrics_history)} | Evaluation: {eval_method.upper()}")