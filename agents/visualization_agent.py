import logging
import plotly.express as px
import pandas as pd

logger = logging.getLogger(__name__)

class VisualizationAgent:
    """Generates charts from tabular data using Plotly"""

    def __init__(self):
        logger.info("✅ VisualizationAgent initialized")

    def process(self, data: list[dict], chart_type: str = "bar", x: str = None, y: str = None):
        """Generate a chart from data"""
        if not data:
            logger.warning("⚠️ No data provided to VisualizationAgent")
            return None

        df = pd.DataFrame(data)

        if not x:
            x = df.columns[0]
        if not y and len(df.columns) > 1:
            y = df.columns[1]

        logger.info(f"📊 Creating {chart_type} chart: x={x}, y={y}")

        if chart_type == "bar":
            fig = px.bar(df, x=x, y=y, title="Bar Chart")
        elif chart_type == "line":
            fig = px.line(df, x=x, y=y, title="Line Chart")
        elif chart_type == "pie":
            fig = px.pie(df, names=x, values=y, title="Pie Chart")
        else:
            logger.warning(f"⚠️ Unknown chart type: {chart_type}")
            return None

        return fig