"""Visualization Agent - Creates charts from data (ENHANCED - Full Date Fix + Plotly Config)"""

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
            return None
        
        df = pd.DataFrame(data)
        df = self._convert_numeric_columns(df)
        
        # Detect time-based data
        time_columns = self._detect_time_columns(df)
        
        if time_columns:
            # Create time series chart
            return self._create_time_series_chart(df, time_columns[0], question)
        
        # Rest of existing logic...
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        
        if len(numeric_cols) >= 2:
            x_col = categorical_cols[0] if categorical_cols else df.columns[0]
            return self._create_bar_chart(df, x_col=x_col, y_cols=numeric_cols)
        elif len(numeric_cols) == 1:
            if categorical_cols:
                x_col = categorical_cols[0]
                y_col = numeric_cols[0]
                return self._create_bar_chart(df, x_col=x_col, y_cols=[y_col])
            else:
                x_col = df.columns[0]
                y_col = numeric_cols[0]
                return self._create_line_chart(df, x_col=x_col, y_col=y_col)
        
        return None

    def _detect_time_columns(self, df: pd.DataFrame) -> List[str]:
        """Detect columns that contain time/date data"""
        
        time_columns = []
        
        for col in df.columns:
            col_lower = col.lower()
            
            # Check column name FIRST
            if any(keyword in col_lower for keyword in ['date', 'time', 'year', 'month', 'week', 'day', 'quarter']):
                time_columns.append(col)
                logger.debug(f"Detected time column by name: {col}")
                continue
            
            # Check data type
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                time_columns.append(col)
                logger.debug(f"Detected datetime dtype column: {col}")
                continue
            
            # Try parsing as date
            if df[col].dtype == 'object':
                try:
                    sample = df[col].dropna().head(1)
                    if len(sample) > 0:
                        test_val = sample.iloc[0]
                        # Quick validation - dates usually have dashes or slashes
                        if isinstance(test_val, str) and ('-' in test_val or '/' in test_val or len(test_val) == 10):
                            pd.to_datetime(sample, format='mixed')
                            time_columns.append(col)
                            logger.debug(f"Detected parseable date column: {col}")
                except Exception as e:
                    logger.debug(f"Could not parse {col} as date: {e}")
            
            # Check if numeric but might be Unix timestamp
            elif pd.api.types.is_numeric_dtype(df[col]):
                try:
                    sample = df[col].dropna().head(1)
                    if len(sample) > 0:
                        val = sample.iloc[0]
                        # Unix timestamps are usually > 500000000 (year 1985+)
                        # and < 5000000000 (year 2128)
                        if 500000000 < val < 5000000000:
                            logger.debug(f"Detected potential Unix timestamp column: {col}")
                            time_columns.append(col)
                except:
                    pass
        
        return time_columns

    def _create_time_series_chart(self, df: pd.DataFrame, time_col: str, question: str) -> go.Figure:
        """Create time series line chart (ENHANCED: Unix timestamp + date parsing)"""
        
        try:
            # Make a copy to avoid modifying original
            df = df.copy()
            
            # CRITICAL: Handle date conversion carefully
            try:
                logger.info(f"Converting {time_col} from dtype={df[time_col].dtype}")
                
                # First check if already datetime
                if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
                    
                    # STRATEGY 1: Try ISO format first (YYYY-MM-DD)
                    try:
                        df[time_col] = pd.to_datetime(df[time_col], format='%Y-%m-%d')
                        logger.info(f"✅ Parsed {time_col} as ISO format (YYYY-MM-DD)")
                    except:
                        # STRATEGY 2: Check if Unix timestamps (numeric)
                        try:
                            if pd.api.types.is_numeric_dtype(df[time_col]):
                                logger.info(f"⚠️ Detected numeric column, attempting Unix timestamp conversion")
                                # Convert Unix timestamp (seconds) to datetime
                                df[time_col] = pd.to_datetime(df[time_col], unit='s')
                                logger.info(f"✅ Converted Unix timestamps to datetime")
                            else:
                                raise ValueError("Not numeric")
                        except:
                            # STRATEGY 3: Try mixed format
                            try:
                                df[time_col] = pd.to_datetime(df[time_col], format='mixed', dayfirst=False)
                                logger.info(f"✅ Parsed {time_col} as mixed format")
                            except:
                                # STRATEGY 4: Last resort - let pandas infer
                                df[time_col] = pd.to_datetime(df[time_col])
                                logger.info(f"✅ Parsed {time_col} with inferred format")
                
                # Validate dates - check for epoch issue
                min_date = df[time_col].min()
                max_date = df[time_col].max()
                
                logger.info(f"Date range: {min_date} to {max_date}")
                
                # Check if we got epoch dates (1969-1970 range = bad parsing)
                epoch = pd.Timestamp('1970-01-01')
                if min_date < epoch and max_date < pd.Timestamp('1975-01-01'):
                    logger.error(f"⚠️ EPOCH ISSUE DETECTED: Dates are in 1969-1970 range")
                    logger.error(f"Min: {min_date}, Max: {max_date}")
                    logger.error(f"Column {time_col} appears to still be Unix timestamp or incorrectly parsed")
                    
                    # Try one more time with different units
                    try:
                        logger.info("Attempting alternative Unix timestamp conversion...")
                        # Maybe timestamps are in milliseconds?
                        df[time_col] = pd.to_datetime(df[time_col], unit='ms')
                        min_date = df[time_col].min()
                        max_date = df[time_col].max()
                        if min_date > pd.Timestamp('2000-01-01'):
                            logger.info(f"✅ Success with millisecond conversion! New range: {min_date} to {max_date}")
                        else:
                            raise ValueError("Still in wrong range")
                    except Exception as retry_error:
                        logger.error(f"❌ Alternative conversion failed: {retry_error}")
                        return self._create_fallback_chart(f"Date parsing failed. Original range: {min_date} to {max_date}")
                
            except Exception as parse_error:
                logger.error(f"❌ Failed to parse dates: {parse_error}")
                return self._create_fallback_chart(f"Date parsing error: {str(parse_error)}")
            
            # Sort by time
            df = df.sort_values(time_col)
            
            # Get numeric columns to plot
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if not numeric_cols:
                logger.warning("⚠️ No numeric columns found for chart")
                return None
            
            fig = go.Figure()
            
            # Add line for each metric (limit to 3)
            for col in numeric_cols[:3]:
                fig.add_trace(go.Scatter(
                    x=df[time_col],
                    y=df[col],
                    mode='lines+markers',
                    name=col,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
            
            # Determine time granularity for title
            try:
                time_range = df[time_col].max() - df[time_col].min()
                if time_range.days > 365:
                    granularity = "Yearly"
                elif time_range.days > 60:
                    granularity = "Monthly"
                elif time_range.days > 14:
                    granularity = "Weekly"
                else:
                    granularity = "Daily"
            except:
                granularity = "Time Series"
            
            # FIXED: Use proper Plotly config parameter instead of deprecated keyword args
            fig.update_layout(
                title=f"{granularity} Trend: {question}",
                xaxis_title=time_col.replace('_', ' ').title(),
                yaxis_title="Value",
                hovermode='x unified',
                template='plotly_white',
                showlegend=True,
                height=500,
                xaxis=dict(
                    tickformat="%Y-%m-%d",
                    type='date'
                )
            )
            
            # Use proper config instead of deprecated keyword arguments
            config = {
                'responsive': True,
                'displayModeBar': True,
                'displaylogo': False
            }
            
            logger.info(f"✅ Successfully created time series chart")
            return fig
            
        except Exception as e:
            logger.error(f"❌ Error creating time series chart: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._create_fallback_chart(f"Error: {str(e)}")
    
    def _create_fallback_chart(self, error_msg: str = None) -> go.Figure:
        """Create a simple placeholder chart if date parsing fails"""
        logger.warning(f"⚠️ Creating fallback chart: {error_msg}")
        
        fig = go.Figure()
        msg = error_msg or "⚠️ Unable to parse dates. Please check the date format in your data."
        fig.add_annotation(
            text=msg,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="red")
        )
        return fig
    
    def _convert_numeric_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert string numbers to numeric where possible"""
        
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    # Try to convert to numeric
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    # If conversion fails, keep as is
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
    
    def _create_bar_chart(self, df: pd.DataFrame, x_col: str = None, y_cols: List[str] = None, title: str = None) -> go.Figure:
        """Create bar chart"""
        
        # Use defaults if not provided
        if x_col is None:
            string_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
            x_col = string_cols[0] if string_cols else df.columns[0]
        
        if y_cols is None:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            y_cols = numeric_cols if numeric_cols else [df.columns[1] if len(df.columns) > 1 else df.columns[0]]
        
        # Use first numeric column if y_cols is empty
        if not y_cols:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if not numeric_cols:
                logger.warning("⚠️ No numeric columns found for bar chart")
                return None
            y_cols = [numeric_cols[0]]
        
        # Sort by first y column descending
        y_col = y_cols[0]
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
    
    def _create_pie_chart(self, df: pd.DataFrame, labels_col: str = None, values_col: str = None, title: str = None) -> go.Figure:
        """Create pie chart for proportions"""
        
        # Use defaults if not provided
        if labels_col is None:
            categorical_cols = df.select_dtypes(exclude=['number']).columns.tolist()
            labels_col = categorical_cols[0] if categorical_cols else df.columns[0]
        
        if values_col is None:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if not numeric_cols:
                logger.warning("⚠️ Need numeric column for pie chart")
                return self._create_bar_chart(df, x_col=labels_col, title=title)
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
    
    def process(self, data: List[Dict[str, Any]], question: str = None) -> go.Figure:
        """Legacy method - calls create_visualization()"""
        logger.warning("⚠️ process() is deprecated, use create_visualization() instead")
        return self.create_visualization(data, question=question)


logger.info("✅ VisualizationAgent class defined (ENHANCED - Unix timestamp + Plotly config fix)")