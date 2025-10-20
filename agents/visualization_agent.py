"""Visualization Agent - Creates charts from data"""

import logging
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class VisualizationAgent:
    """Generates charts from tabular data using Plotly with smart auto-detection"""
    
    def __init__(self):
        logger.info("✅ VisualizationAgent initialized")
    
    def create_visualization(
        self, 
        data: List[Dict], 
        question: str = None, 
        chart_type: str = None
    ) -> Optional[go.Figure]:
        """
        Create visualization with smart auto-detection
        
        Args:
            data: List of dictionaries (query results)
            question: Original question (helps infer chart type)
            chart_type: Force specific chart type ('bar', 'line', 'pie')
            
        Returns:
            Plotly figure object or None
        """
        if not data:
            logger.warning("⚠️ No data to visualize")
            return None
        
        df = pd.DataFrame(data)
        logger.info(f"📊 Creating visualization from {len(df)} rows")
        
        # CRITICAL: Auto-convert numeric columns
        df = self._convert_numeric_columns(df)
        
        # Smart categorical detection
        if chart_type is None:
            chart_type = self._infer_chart_type(df, question)
        
        logger.info(f"📊 Creating {chart_type} chart...")
        
        # Create appropriate chart
        if chart_type == 'bar':
            return self._create_bar_chart(df, question)
        elif chart_type == 'line':
            return self._create_line_chart(df, question)
        elif chart_type == 'pie':
            return self._create_pie_chart(df, question)
        else:
            return self._create_bar_chart(df, question)  # Default
    
    def _convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert string columns to numeric where appropriate"""
        
        # List of columns that should stay as strings
        text_columns = ['BUSINESSUNIT', 'MARKET', 'COUNTRY_CODE', 'COUNTRY',
                       'CHANNEL', 'CHANNEL_GROUPING', 'SOURCE', 'CAMPAIGN',
                       'REGION', 'SEGMENT', 'SENDID', 'SEND_KEY']
        
        for col in df.columns:
            if col.upper() not in text_columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors='ignore')
                except:
                    pass
        
        return df
    
    def _infer_chart_type(self, df: pd.DataFrame, question: str = None) -> str:
        """Infer appropriate chart type from data and question"""
        
        # Priority 1: Check question keywords
        if question:
            question_lower = question.lower()
            
            if any(kw in question_lower for kw in ['trend', 'over time', 'time series']):
                return 'line'
            elif any(kw in question_lower for kw in ['by market', 'by country', 'by channel', 'comparison']):
                return 'bar'
            elif any(kw in question_lower for kw in ['distribution', 'proportion', 'share']):
                return 'pie'
        
        # Priority 2: Check for categorical business dimensions
        first_col = df.columns[0].upper()
        categorical_dims = ['BUSINESSUNIT', 'MARKET', 'COUNTRY_CODE', 'COUNTRY',
                           'CHANNEL', 'CHANNEL_GROUPING', 'REGION', 'SEGMENT']
        
        if first_col in categorical_dims:
            logger.info(f"   Detected categorical dimension: {first_col} → BAR chart")
            return 'bar'
        
        # Priority 3: Check for date columns
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                logger.info(f"   Detected time column: {col} → LINE chart")
                return 'line'
        
        # Default: bar chart
        return 'bar'
    
    def _create_bar_chart(self, df: pd.DataFrame, title: str = None) -> go.Figure:
        """Create bar chart"""
        
        # Convert column names to uppercase for consistency
        df.columns = [col.upper() for col in df.columns]
        
        # Identify columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        string_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        if not numeric_cols:
            logger.warning("⚠️ No numeric columns found for bar chart")
            return None
        
        # Select x (categorical) and y (numeric)
        x_col = string_cols[0] if string_cols else df.columns[0]
        y_col = numeric_cols[0]
        
        # Sort by value descending
        df_sorted = df.sort_values(by=y_col, ascending=False)
        
        # Create chart
        fig = px.bar(
            df_sorted,
            x=x_col,
            y=y_col,
            title=title or f"{y_col} by {x_col}",
            color=x_col,
            text=y_col,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        # Format numbers
        max_val = df[y_col].max()
        if max_val > 1000000:
            text_template = '%{text:,.0f}'
        elif max_val < 100:
            text_template = '%{text:.2f}'
        else:
            text_template = '%{text:,.0f}'
        
        fig.update_traces(
            texttemplate=text_template,
            textposition='outside'
        )
        
        fig.update_layout(
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            showlegend=False,
            height=600,
            font=dict(size=12)
        )
        
        return fig
    
    def _create_line_chart(self, df: pd.DataFrame, title: str = None) -> go.Figure:
        """Create line chart for trends"""
        
        x_col = df.columns[0]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        fig = go.Figure()
        
        for y_col in numeric_cols:
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='lines+markers',
                name=y_col.replace('_', ' ').title()
            ))
        
        fig.update_layout(
            title=title or "Trend Over Time",
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title="Value",
            height=600,
            hovermode='x unified'
        )
        
        return fig
    
    def _create_pie_chart(self, df: pd.DataFrame, title: str = None) -> go.Figure:
        """Create pie chart for proportions"""
        
        categorical_cols = df.select_dtypes(exclude=['number']).columns.tolist()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not categorical_cols or not numeric_cols:
            logger.warning("⚠️ Need both categorical and numeric columns for pie chart")
            return self._create_bar_chart(df, title)
        
        labels_col = categorical_cols[0]
        values_col = numeric_cols[0]
        
        fig = px.pie(
            df,
            names=labels_col,
            values=values_col,
            title=title or f"Distribution of {values_col}"
        )
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=600)
        
        return fig
    
    # Keep the old process() method for backward compatibility
    def process(self, data: list[dict], chart_type: str = "bar", x: str = None, y: str = None):
        """Legacy method - calls create_visualization()"""
        logger.warning("⚠️ process() is deprecated, use create_visualization() instead")
        return self.create_visualization(data, chart_type=chart_type)