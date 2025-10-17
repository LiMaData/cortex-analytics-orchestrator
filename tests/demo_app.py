# demo_app.py - Multi-Agent Analytics Streamlit App

import streamlit as st
from snowflake.snowpark import Session
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# Page config
st.set_page_config(
    page_title="Multi-Agent Analytics",
    page_icon="🤖",
    layout="wide"
)

# ============================================================
# AGENT CLASSES (Copy from your working Jupyter notebook)
# ============================================================

class CortexAnalyst:
    def __init__(self, session, semantic_model_stage):
        
        self.session = session
        self.semantic_model = self._load_semantic_model(semantic_model_stage)
        self.schema_context = self._build_context()
        
    def _load_semantic_model(self, stage_path):
        self.session.sql("""
            CREATE FILE FORMAT IF NOT EXISTS yaml_format
            TYPE = 'CSV' FIELD_DELIMITER = NONE RECORD_DELIMITER = NONE
        """).collect()
        result = self.session.sql(f"""
            SELECT t.$1 AS content FROM {stage_path} (FILE_FORMAT => yaml_format) t
        """).collect()
        return "\n".join([row['CONTENT'] for row in result])
    
    def _build_context(self):
        header = self.semantic_model[:800]
        verified_start = self.semantic_model.find('verified_queries:')
        verified_end = self.semantic_model.find('tables:', verified_start)
        verified = self.semantic_model[verified_start:verified_end] if verified_start != -1 else ""
        tables_start = self.semantic_model.find('tables:')
        first_table = self.semantic_model[tables_start:tables_start+2000] if tables_start != -1 else ""
        return f"{header}\n\n{verified}\n\n{first_table}"
    
    def _clean_sql(self, text):
        text = re.sub(r'```sql\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()
        match = re.search(r'((?:WITH|SELECT).*?)(?:;|\Z)', text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.rstrip(';').strip()
    
    def ask(self, question):
        prompt = f"""Generate SQL for Snowflake.

{self.schema_context}

Question: {question}

Return ONLY the SQL query:"""
        
        result = self.session.sql(f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large', '{prompt.replace("'", "''")}') AS sql_text
        """).collect()
        
        clean_sql = self._clean_sql(result[0]['SQL_TEXT'])
        
        try:
            data = self.session.sql(clean_sql).collect()
            results = [row.asDict() for row in data]
            return {'success': True, 'sql': clean_sql, 'results': results, 'row_count': len(results)}
        except Exception as e:
            return {'success': False, 'sql': clean_sql, 'results': [], 'error': str(e)}


class VisualizationAgent:
    def create_visualization(self, data, question=None, chart_type=None):
        if not data:
            return None
        df = pd.DataFrame(data)
        
        for col in df.columns:
            if col.upper() not in ['BUSINESSUNIT', 'MARKET', 'COUNTRY_CODE']:
                try:
                    df[col] = pd.to_numeric(df[col])
                except:
                    pass
        
        if chart_type is None:
            first_col = df.columns[0].upper()
            categorical_dims = ['BUSINESSUNIT', 'MARKET', 'COUNTRY_CODE']
            chart_type = 'bar' if first_col in categorical_dims else 'bar'
        
        return self._create_bar_chart(df, question)
    
    def _create_bar_chart(self, df, title=None):
        df.columns = [col.upper() for col in df.columns]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        string_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        if not numeric_cols:
            return None
        
        x_col = string_cols[0] if string_cols else df.columns[0]
        y_col = numeric_cols[0]
        df_sorted = df.sort_values(by=y_col, ascending=False)
        
        fig = px.bar(df_sorted, x=x_col, y=y_col, title=title or f"{y_col} by {x_col}",
                     color=x_col, text=y_col, color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(xaxis_title=x_col.replace('_', ' ').title(),
                         yaxis_title=y_col.replace('_', ' ').title(),
                         showlegend=False, height=500)
        return fig


class MultiAgentExecutor:
    def __init__(self, session, semantic_model_stage):
        self.session = session
        self.analyst = CortexAnalyst(session, semantic_model_stage)
        self.viz_agent = VisualizationAgent()
    
    def execute(self, question, options=None):
        options = options or {}
        
        query_type = self._classify_query(question)
        data_result = self.analyst.ask(question)
        
        if not data_result['success']:
            return {'success': False, 'error': data_result.get('error'), 'sql': data_result.get('sql')}
        
        chart = None
        if options.get('visualize', True) and data_result['row_count'] > 0:
            chart = self.viz_agent.create_visualization(data_result['results'], question)
        
        insights = self._generate_insights(data_result['results'])
        
        return {
            'success': True, 'query': question, 'query_type': query_type,
            'sql': data_result['sql'], 'data': data_result['results'],
            'visualization': chart, 'insights': insights, 'row_count': data_result['row_count']
        }
    
    def _classify_query(self, question):
        q = question.lower()
        if 'trend' in q or 'over time' in q:
            return '📈 TREND'
        elif 'by market' in q or 'by country' in q:
            return '📊 COMPARISON'
        elif 'top' in q or 'bottom' in q:
            return '🏆 RANKING'
        else:
            return '📋 GENERAL'
    
    def _generate_insights(self, data):
        if not data:
            return "No data"
        df = pd.DataFrame(data)
        insights = [f"{len(data)} records"]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            col = numeric_cols[0]
            insights.append(f"{col}: {df[col].sum():,.0f}")
        return " | ".join(insights)


# ============================================================
# STREAMLIT APP UI
# ============================================================

st.title("🤖 Multi-Agent Analytics System")
st.markdown("### Powered by Snowflake Cortex AI")

# Sidebar - Connection
with st.sidebar:
    st.header("🔧 Configuration")
    
    with st.expander("⚙️ Snowflake Connection", expanded=False):
        account = st.text_input("Account", value="wkswaox-lt08934")
        user = st.text_input("User", value="Lima717")
        password = st.text_input("Password", type="password", value="Easy2snowflake!")
        warehouse = st.text_input("Warehouse", value="COMPUTE_WH")
        database = st.text_input("Database", value="CAMPAIGN_ANALYTICS")
        schema = st.text_input("Schema", value="GENERATED_DATA")
    
    if st.button("🔌 Connect", type="primary"):
        try:
            connection_params = {
                "account": account, "user": user, "password": password,
                "role": "ACCOUNTADMIN", "warehouse": warehouse,
                "database": database, "schema": schema
            }
            session = Session.builder.configs(connection_params).create()
            st.session_state.session = session
            st.success("✅ Connected!")
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")
    
    st.markdown("---")
    st.markdown("**System Status:**")
    
    if 'executor' in st.session_state:
        st.success("🟢 Executor Ready")
    else:
        st.warning("🟡 Not Initialized")

# Initialize executor
if 'session' in st.session_state and 'executor' not in st.session_state:
    with st.spinner("⚙️ Initializing Multi-Agent System..."):
        try:
            executor = MultiAgentExecutor(
                st.session_state.session,
                '@semantic_models/marketing_semantic_model.yaml'
            )
            st.session_state.executor = executor
            st.success("✅ Multi-Agent System Ready!")
        except Exception as e:
            st.error(f"❌ Initialization failed: {e}")

# Main interface
if 'executor' in st.session_state:
    
    # Example queries
    st.markdown("### 💡 Try These Examples:")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📧 Open rates by market (past month)", use_container_width=True):
            st.session_state.current_query = "Show me email open rates by market for the past month"
    
    with col2:
        if st.button("🏆 Top 5 markets by sends", use_container_width=True):
            st.session_state.current_query = "Show me top 5 markets by sends"
    
    # Query input
    st.markdown("### 💬 Ask a Question")
    
    query = st.text_input(
        "Enter your question:",
        value=st.session_state.get('current_query', ''),
        placeholder="e.g., What are bookings by market?",
        label_visibility="collapsed"
    )
    
    col_run, col_viz = st.columns([3, 1])
    with col_run:
        run_query = st.button("🚀 Execute Query", type="primary", use_container_width=True)
    with col_viz:
        visualize = st.checkbox("📊 Visualize", value=True)
    
    # Execute query
    if run_query and query:
        with st.spinner("🤖 Multi-Agent System Processing..."):
            result = st.session_state.executor.execute(
                query,
                options={'visualize': visualize}
            )
        
        if result['success']:
            # Success metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Query Type", result['query_type'])
            with col2:
                st.metric("Rows Returned", result['row_count'])
            with col3:
                st.metric("Status", "✅ Success")
            
            # Tabs for results
            tab1, tab2, tab3 = st.tabs(["📊 Visualization", "📋 Data", "💾 SQL"])
            
            with tab1:
                if result['visualization']:
                    st.plotly_chart(result['visualization'], use_container_width=True)
                else:
                    st.info("No visualization generated")
            
            with tab2:
                st.dataframe(pd.DataFrame(result['data']), use_container_width=True, hide_index=True)
                st.caption(f"💡 Insights: {result['insights']}")
            
            with tab3:
                st.code(result['sql'], language='sql')
                if st.button("📋 Copy SQL"):
                    st.toast("SQL copied to clipboard!")
        
        else:
            st.error(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            if 'sql' in result:
                with st.expander("🔍 View Generated SQL"):
                    st.code(result['sql'], language='sql')

else:
    st.info("👈 Please connect to Snowflake using the sidebar")

# Footer
st.markdown("---")
st.caption("🤖 Multi-Agent Orchestrated System | Step 2: Production Architecture")