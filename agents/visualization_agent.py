"""Visualization Agent - Creates charts from data (IMPROVED - Better Detection Logic)"""

import logging
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class VisualizationAgent:
    """Generates charts from tabular data using Plotly with smart auto-detection"""
    
    def __init__(self):
        logger.info("✅ VisualizationAgent initialized")
    
    def create_visualization(self, data: List[Dict[str, Any]], question: str) -> go.Figure:
        """Create appropriate visualization based on data and question"""
        
        if not data:
            logger.warning("⚠️ No data provided for visualization")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        logger.info(f"📊 Creating visualization for {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"📊 Columns: {list(df.columns)}")
        
        # Convert numeric columns FIRST (critical!)
        df = self._convert_numeric_columns(df)
        
        # Log column types after conversion
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        logger.info(f"📊 Numeric columns: {numeric_cols}")
        logger.info(f"📊 Categorical columns: {categorical_cols}")
        
        # ✅ PRIORITY 1: Check question context FIRST
        # If question asks for comparison by category, don't try time-series
        if question:
            question_lower = question.lower()
            
            # Check for categorical comparison keywords
            categorical_keywords = ['by market', 'by country', 'by channel', 'by region', 
                                   'by segment', 'by businessunit', 'per market', 'per country',
                                   'compare', 'comparison', 'between', 'across']
            
            if any(kw in question_lower for kw in categorical_keywords):
                logger.info("📊 Question indicates categorical comparison → Using BAR chart")
                
                # Check for categorical business dimensions in columns
                business_dims = ['BUSINESSUNIT', 'MARKET', 'COUNTRY_CODE', 'COUNTRY',
                               'CHANNEL', 'CHANNEL_GROUPING', 'REGION', 'SEGMENT']
                
                x_col = None
                for col in df.columns:
                    if col.upper() in business_dims:
                        x_col = col
                        logger.info(f"   Using {col} as X-axis (categorical dimension)")
                        break
                
                if x_col and numeric_cols:
                    return self._create_bar_chart(df, x_col=x_col, y_cols=numeric_cols, title=question)
        
        # ✅ PRIORITY 2: Detect time-based data (but only if not categorical comparison)
        time_columns = self._detect_time_columns(df)
        
        if time_columns:
            logger.info(f"📊 Detected time columns: {time_columns}")
            # Create time series chart
            return self._create_time_series_chart(df, time_columns[0], question)
        
        # ✅ PRIORITY 3: Standard logic based on column types
        if not numeric_cols:
            logger.warning("⚠️ No numeric columns found for chart")
            return None
        
        if len(numeric_cols) >= 2:
            # Multiple numeric columns
            x_col = categorical_cols[0] if categorical_cols else df.columns[0]
            logger.info(f"📊 Multiple numeric cols → BAR chart with X={x_col}, Y={numeric_cols}")
            return self._create_bar_chart(df, x_col=x_col, y_cols=numeric_cols, title=question)
        
        elif len(numeric_cols) == 1:
            # Single numeric column
            if categorical_cols:
                x_col = categorical_cols[0]
                y_col = numeric_cols[0]
                logger.info(f"📊 Single numeric col + categorical → BAR chart X={x_col}, Y={y_col}")
                return self._create_bar_chart(df, x_col=x_col, y_cols=[y_col], title=question)
            else:
                x_col = df.columns[0]
                y_col = numeric_cols[0]
                logger.info(f"📊 Single numeric col without categorical → LINE chart")
                return self._create_line_chart(df, x_col=x_col, y_col=y_col, title=question)
        
        logger.warning("⚠️ Could not determine appropriate chart type")
        return None

    def _convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert string numbers to numeric where possible
        CRITICAL: This must work properly for visualization to succeed
        """
        df = df.copy()  # Don't modify original
        
        for col in df.columns:
            if df[col].dtype == 'object' or df[col].dtype == 'string':
                try:
                    # Try to convert to numeric
                    converted = pd.to_numeric(df[col], errors='coerce')
                    
                    # Only apply if most values converted successfully
                    if converted.notna().sum() > len(df) * 0.5:  # At least 50% valid
                        df[col] = converted
                        logger.info(f"✅ Converted {col} to numeric (dtype: {df[col].dtype})")
                    else:
                        logger.debug(f"   Kept {col} as {df[col].dtype} (too few numeric values)")
                        
                except (ValueError, TypeError) as e:
                    logger.debug(f"   Could not convert {col} to numeric: {e}")
        
        return df

    def _detect_time_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Detect columns that contain time/date data
        ✅ IMPROVED: Less aggressive, more accurate
        """
        
        time_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            
            # ✅ STRICT: Only consider columns with very clear time names
            clear_time_keywords = ['date', 'datetime', 'timestamp', 'time', 'year', 'month', 'quarter']
            
            # Check if column name is clearly a time column
            if col_lower in clear_time_keywords or col_lower.endswith('_date') or col_lower.startswith('date_'):
                time_columns.append(col)
                logger.debug(f"✅ Detected time column by name: {col}")
                continue
            
            # Check data type
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                time_columns.append(col)
                logger.debug(f"✅ Detected datetime dtype column: {col}")
                continue
            
            # ✅ CAREFUL: Only try parsing if column name suggests it's a date
            if any(kw in col_lower for kw in ['date', 'time']):
                # Try parsing as date
                if df[col].dtype == 'object':
                    try:
                        sample = df[col].dropna().head(3)  # Check first 3 values
                        if len(sample) > 0:
                            test_val = sample.iloc[0]
                            # Quick validation - dates usually have dashes or slashes
                            if isinstance(test_val, str) and ('-' in test_val or '/' in test_val):
                                pd.to_datetime(sample, format='mixed')
                                time_columns.append(col)
                                logger.debug(f"✅ Detected parseable date column: {col}")
                    except Exception:
                        pass  # Not a date column
        
        return time_columns

    def _create_time_series_chart(self, df: pd.DataFrame, time_col: str, question: str) -> go.Figure:
        """Create time series line chart"""
        
        try:
            # Make a copy to avoid modifying original
            df = df.copy()
            
            # Convert time column to datetime
            try:
                logger.info(f"Converting {time_col} from dtype={df[time_col].dtype}")
                
                if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
                    # Try ISO format first (YYYY-MM-DD)
                    try:
                        df[time_col] = pd.to_datetime(df[time_col], format='%Y-%m-%d')
                        logger.info(f"✅ Parsed {time_col} as ISO format")
                    except:
                        # Try mixed format
                        df[time_col] = pd.to_datetime(df[time_col], format='mixed')
                        logger.info(f"✅ Parsed {time_col} as mixed format")
                
                # Validate dates
                min_date = df[time_col].min()
                max_date = df[time_col].max()
                logger.info(f"Date range: {min_date} to {max_date}")
                
            except Exception as parse_error:
                logger.error(f"❌ Failed to parse dates: {parse_error}")
                # Fall back to bar chart
                return self._create_bar_chart(df, x_col=time_col, y_cols=None, title=question)
            
            # Sort by time
            df = df.sort_values(time_col)
            
            # Get numeric columns to plot (re-check after copy)
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if not numeric_cols:
                logger.warning("⚠️ No numeric columns found for time series")
                return None
            
            # Create line chart with first numeric column
            y_col = numeric_cols[0]
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[y_col],
                mode='lines+markers',
                name=y_col.replace('_', ' ').title(),
                line=dict(width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title=question or "Time Series",
                xaxis_title=time_col.replace('_', ' ').title(),
                yaxis_title=y_col.replace('_', ' ').title(),
                height=600,
                hovermode='x unified',
                font=dict(size=12)
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"❌ Time series chart creation failed: {e}")
            # Fall back to bar chart
            return self._create_bar_chart(df, x_col=df.columns[0], y_cols=None, title=question)
    
    def _create_bar_chart(self, df: pd.DataFrame, x_col: str = None, y_cols: List[str] = None, title: str = None) -> go.Figure:
        """Create bar chart"""
        
        # Use defaults if not provided
        if x_col is None:
            string_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
            x_col = string_cols[0] if string_cols else df.columns[0]
        
        if y_cols is None:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if not numeric_cols:
                logger.warning("⚠️ No numeric columns found for bar chart")
                return None
            y_cols = numeric_cols
        
        # Use first numeric column
        y_col = y_cols[0] if y_cols else df.columns[1]
        
        # Sort by y value descending
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
        
        # Format numbers on bars
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
            font=dict(size=12),
            xaxis={'categoryorder': 'total descending'}
        )
        
        return fig
    
    def _create_line_chart(self, df: pd.DataFrame, x_col: str = None, y_col: str = None, title: str = None) -> go.Figure:
        """Create line chart for trends"""
        
        # Use defaults if not provided
        if x_col is None:
            x_col = df.columns[0]
        
        if y_col is None:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            y_col = numeric_cols[0] if numeric_cols else df.columns[1]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode='lines+markers',
            name=y_col.replace('_', ' ').title(),
            line=dict(width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=title or "Trend Over Time",
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            height=600,
            hovermode='x unified'
        )
        
        return fig
    
    def process(self, data: List[Dict[str, Any]], question: str = None) -> go.Figure:
        """Legacy method - calls create_visualization()"""
        return self.create_visualization(data, question=question)


logger.info("✅ VisualizationAgent class defined (IMPROVED - Better detection)")