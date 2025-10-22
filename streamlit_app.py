"""
Streamlit UI for Multi-Agent Analytics Orchestrator
Improved with working examples and elegant progress visualization
"""

import streamlit as st
import pandas as pd
from orchestrators.conversational import ConversationalOrchestrator
import logging
import time

# Configure
st.set_page_config(
    page_title="Multi-Agent Analytics Orchestrator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UX
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .step-indicator {
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        background-color: #f0f2f6;
    }
    .step-active {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
    }
    .step-complete {
        background-color: #e8f5e9;
        border-left: 4px solid #4CAF50;
    }
    .step-error {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Setup logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise in UI
logger = logging.getLogger(__name__)

# Initialize session state
if 'orchestrator' not in st.session_state:
    with st.spinner("🔧 Initializing orchestrator..."):
        try:
            st.session_state.orchestrator = ConversationalOrchestrator(enable_monitoring=True)
            st.session_state.query_history = []
            st.session_state.initialized = True
        except Exception as e:
            st.error(f"❌ Failed to initialize: {e}")
            st.session_state.initialized = False
            st.stop()

if 'last_response' not in st.session_state:
    st.session_state.last_response = None

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Agent toggles
    st.subheader("🤖 Active Agents")
    with_benchmarks = st.checkbox("📊 Benchmarks", value=True, help="Compare to industry standards")
    with_insights = st.checkbox("💡 AI Insights", value=True, help="Generate insights with LLM")
    with_viz = st.checkbox("📈 Visualization", value=True, help="Auto-generate charts")
    
    # Processing visualization toggle
    st.divider()
    show_processing = st.checkbox("🔄 Show Processing Steps", value=True, help="Display real-time progress")
    
    st.divider()
    
    # Query history
    st.subheader("📜 Recent Queries")
    if st.session_state.query_history:
        for i, hist_query in enumerate(reversed(st.session_state.query_history[-5:])):
            if st.button(f"↻ {hist_query[:35]}...", key=f"hist_{i}", use_container_width=True):
                st.session_state.trigger_query = hist_query
                st.rerun()
    else:
        st.caption("_No history yet_")
    
    # Performance stats
    if st.session_state.get('initialized'):
        st.divider()
        st.subheader("📊 Session Stats")
        status = st.session_state.orchestrator.get_status()
        
        if 'monitoring_stats' in status:
            stats = status['monitoring_stats']
            st.metric("Queries Run", stats.get('total_queries', 0))
            st.metric("Avg Time", f"{stats.get('avg_query_time', 0):.1f}s")
            st.metric("Success Rate", f"{stats.get('success_rate', 0):.0f}%")

# Main header
st.markdown('<p class="main-header">🚀 Cortex Analytics Orchestrator</p>', unsafe_allow_html=True)
st.caption("Multi-Agent Analytics with AI-Powered Insights & Benchmark Comparison")

# Query input section
col1, col2 = st.columns([5, 1])

with col1:
    query = st.text_input(
        "Enter your analytics question:",
        placeholder="e.g., Show me open rates by market",
        key="query_input",
        label_visibility="collapsed"
    )

with col2:
    run_query = st.button("🔍 Analyze", type="primary", use_container_width=True)

# Example queries with immediate execution
st.caption("💡 **Try these examples:**")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📧 Total Sends", use_container_width=True):
        st.session_state.trigger_query = "What are the total email sends?"
        st.rerun()

with col2:
    if st.button("📊 Open Rates", use_container_width=True):
        st.session_state.trigger_query = "Show me open rates by market"
        st.rerun()

with col3:
    if st.button("🎯 VCUS Rate", use_container_width=True):
        st.session_state.trigger_query = "What is the conversion rate for VCUS?"
        st.rerun()

with col4:
    if st.button("📈 Click Rates", use_container_width=True):
        st.session_state.trigger_query = "Compare click rates across all markets"
        st.rerun()

st.divider()

# Check if query should be triggered
query_to_process = None
if run_query and query:
    query_to_process = query
elif 'trigger_query' in st.session_state:
    query_to_process = st.session_state.trigger_query
    del st.session_state.trigger_query

# Process query with elegant progress visualization
if query_to_process:
    # Add to history
    if query_to_process not in st.session_state.query_history:
        st.session_state.query_history.append(query_to_process)
    
    # Show query being processed
    st.info(f"🔍 **Processing:** {query_to_process}")
    
    # Processing visualization
    if show_processing:
        st.subheader("⏳ Processing Pipeline")
        
        # Create placeholders for each step
        step1 = st.empty()
        step2 = st.empty()
        step3 = st.empty()
        step4 = st.empty()
        progress_bar = st.progress(0)
        time_estimate = st.empty()
    
    try:
        start_time = time.time()
        
        # Step indicators
        steps_config = [
            {"name": "🔍 Data Query", "key": "data", "weight": 30},
            {"name": "📊 Benchmarks", "key": "benchmarks", "weight": 20},
            {"name": "💡 Insights", "key": "insights", "weight": 30},
            {"name": "📈 Visualization", "key": "viz", "weight": 20}
        ]
        
        # STEP 1: Data Query
        if show_processing:
            step1.markdown('<div class="step-indicator step-active">🔍 <b>Data Query</b> - Translating to SQL...</div>', unsafe_allow_html=True)
            progress_bar.progress(0.1)
            time_estimate.caption("⏱️ Estimated time: 15-40 seconds")
        
        # Execute query with monitoring
        response = st.session_state.orchestrator.process_query(
            query_to_process,
            with_viz=with_viz,
            with_benchmarks=with_benchmarks,
            with_insights=with_insights
        )
        
        if show_processing:
            step1.markdown('<div class="step-indicator step-complete">✅ <b>Data Query</b> - Complete</div>', unsafe_allow_html=True)
            progress_bar.progress(0.3)
        
        # STEP 2: Benchmarks
        if with_benchmarks and show_processing:
            step2.markdown('<div class="step-indicator step-active">📊 <b>Benchmarks</b> - Fetching industry data...</div>', unsafe_allow_html=True)
            progress_bar.progress(0.5)
        
        if show_processing:
            if 'benchmarks' in response:
                step2.markdown('<div class="step-indicator step-complete">✅ <b>Benchmarks</b> - Retrieved</div>', unsafe_allow_html=True)
            elif with_benchmarks:
                step2.markdown('<div class="step-indicator step-error">⚠️ <b>Benchmarks</b> - Skipped</div>', unsafe_allow_html=True)
            progress_bar.progress(0.5)
        
        # STEP 3: Insights
        if with_insights and show_processing:
            step3.markdown('<div class="step-indicator step-active">💡 <b>AI Insights</b> - Generating analysis...</div>', unsafe_allow_html=True)
            progress_bar.progress(0.7)
        
        if show_processing:
            if 'insights' in response:
                step3.markdown('<div class="step-indicator step-complete">✅ <b>AI Insights</b> - Generated</div>', unsafe_allow_html=True)
            elif with_insights:
                step3.markdown('<div class="step-indicator step-error">⚠️ <b>AI Insights</b> - Skipped</div>', unsafe_allow_html=True)
            progress_bar.progress(0.8)
        
        # STEP 4: Visualization
        if with_viz and show_processing:
            step4.markdown('<div class="step-indicator step-active">📈 <b>Visualization</b> - Creating chart...</div>', unsafe_allow_html=True)
            progress_bar.progress(0.9)
        
        if show_processing:
            if 'visualization' in response:
                step4.markdown('<div class="step-indicator step-complete">✅ <b>Visualization</b> - Created</div>', unsafe_allow_html=True)
            elif with_viz:
                step4.markdown('<div class="step-indicator step-error">⚠️ <b>Visualization</b> - Skipped</div>', unsafe_allow_html=True)
            progress_bar.progress(1.0)
        
        elapsed = time.time() - start_time
        
        if show_processing:
            time_estimate.caption(f"✅ **Completed in {elapsed:.2f}s**")
            time.sleep(0.5)  # Brief pause to show completion
        
        # Success message
        st.success(f"✅ **Query completed successfully!** {len(response.get('data', []))} rows returned in {elapsed:.1f}s")
        
        # Store response
        st.session_state.last_response = response
        
        # Clear processing visualization
        if show_processing:
            time.sleep(0.3)
            step1.empty()
            step2.empty()
            step3.empty()
            step4.empty()
            progress_bar.empty()
            time_estimate.empty()
        
        # Display results
        if response.get('success'):
            # Create tabs
            tab_names = ["📊 Results"]
            if response.get('sql'):
                tab_names.append("💾 SQL")
            if 'visualization' in response:
                tab_names.append("📈 Chart")
            if 'benchmarks' in response:
                tab_names.append("📊 Benchmarks")
            if 'insights' in response:
                tab_names.append("💡 Insights")
            
            tabs = st.tabs(tab_names)
            tab_idx = 0
            
            # TAB: RESULTS
            with tabs[tab_idx]:
                tab_idx += 1
                st.subheader("📊 Query Results")
                
                data = response.get('data', [])
                if data:
                    df = pd.DataFrame(data)
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("📊 Total Rows", len(df))
                    with col2:
                        st.metric("📋 Columns", len(df.columns))
                    with col3:
                        numeric_cols = df.select_dtypes(include=['number']).columns
                        if len(numeric_cols) > 0:
                            first_val = df[numeric_cols[0]].iloc[0] if len(df) > 0 else 0
                            st.metric(numeric_cols[0], f"{first_val:,.2f}")
                    with col4:
                        st.metric("⏱️ Query Time", f"{elapsed:.2f}s")
                    
                    st.divider()
                    
                    # Data table with better formatting
                    st.dataframe(
                        df,
                        use_container_width=True,
                        height=min(400, len(df) * 35 + 38)
                    )
                    
                    # Download
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "⬇️ Download CSV",
                            csv,
                            "results.csv",
                            "text/csv",
                            use_container_width=True
                        )
                else:
                    st.info("No data returned")
            
            # TAB: SQL
            if response.get('sql'):
                with tabs[tab_idx]:
                    tab_idx += 1
                    st.subheader("💾 Generated SQL")
                    
                    sql = response.get('sql', '')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("SQL Length", f"{len(sql)} chars")
                    with col2:
                        complexity = "Simple" if len(sql) < 200 else "Moderate" if len(sql) < 500 else "Complex"
                        st.metric("Complexity", complexity)
                    
                    st.code(sql, language="sql", line_numbers=True)
            
            # TAB: VISUALIZATION
            if 'visualization' in response:
                with tabs[tab_idx]:
                    tab_idx += 1
                    st.subheader("📈 Data Visualization")
                    
                    st.plotly_chart(
                        response['visualization'],
                        use_container_width=True,
                        height=600
                    )
                    
                    st.caption("💡 _Interactive chart - hover for details, click legend to filter_")
            
            # TAB: BENCHMARKS
            if 'benchmarks' in response:
                with tabs[tab_idx]:
                    tab_idx += 1
                    st.subheader("📊 Industry Benchmarks")
                    
                    benchmarks = response['benchmarks']
                    bm_data = benchmarks.get('benchmarks', {})
                    
                    # Visual benchmark comparison
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric(
                            "Industry Average",
                            f"{bm_data.get('industry_average', 0):.1f}%",
                            help="Average performance across industry"
                        )
                    with col2:
                        st.metric(
                            "Top Quartile",
                            f"{bm_data.get('top_quartile', 0):.1f}%",
                            delta=f"+{bm_data.get('top_quartile', 0) - bm_data.get('industry_average', 0):.1f}%",
                            help="Best 25% of performers"
                        )
                    with col3:
                        st.metric(
                            "Bottom Quartile",
                            f"{bm_data.get('bottom_quartile', 0):.1f}%",
                            delta=f"{bm_data.get('bottom_quartile', 0) - bm_data.get('industry_average', 0):.1f}%",
                            delta_color="inverse",
                            help="Lowest 25% of performers"
                        )
                    with col4:
                        st.metric(
                            "Excellence Bar",
                            f"{bm_data.get('excellent_threshold', 0):.1f}%",
                            help="Target for excellent performance"
                        )
                    
                    st.divider()
                    
                    # Source attribution
                    st.caption(f"**📚 Source:** {benchmarks.get('source_description', 'N/A')}")
                    if 'updated_date' in bm_data:
                        st.caption(f"**📅 Last Updated:** {bm_data['updated_date']} ({bm_data.get('age_days', 0)} days ago)")
            
            # TAB: INSIGHTS
            if 'insights' in response:
                with tabs[tab_idx]:
                    tab_idx += 1
                    st.subheader("💡 AI-Generated Insights")
                    
                    insights = response['insights']
                    
                    # Display insights with nice formatting
                    st.markdown(insights)
                    
                    st.divider()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Regenerate Insights", use_container_width=True):
                            with st.spinner("Regenerating..."):
                                new_response = st.session_state.orchestrator.process_query(
                                    query_to_process,
                                    with_viz=False,
                                    with_benchmarks=with_benchmarks,
                                    with_insights=True
                                )
                                if new_response.get('success'):
                                    st.session_state.last_response['insights'] = new_response.get('insights')
                                    st.rerun()
                    
                    with col2:
                        insights_text = insights.replace('\n', '\n\n')
                        st.download_button(
                            "💾 Download Insights",
                            insights_text,
                            "insights.txt",
                            "text/plain",
                            use_container_width=True
                        )
        
        else:
            st.error(f"❌ **Query failed:** {response.get('error', 'Unknown error')}")
            
            if response.get('sql'):
                with st.expander("🔍 View Generated SQL"):
                    st.code(response['sql'], language="sql")
    
    except Exception as e:
        if show_processing:
            st.error(f"❌ **System Error:** {e}")
        else:
            st.error(f"❌ Error: {e}")
        
        logger.exception("Query execution failed")

# Footer
st.divider()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.caption("🤖 Powered by Snowflake Cortex")
with col2:
    st.caption("📊 Multi-Agent Orchestration")
with col3:
    st.caption(f"📜 {len(st.session_state.query_history)} queries")
with col4:
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.query_history = []
        st.rerun()