"""Quick fix for all reported issues"""

import re

def fix_visualization_agent():
    """Fix FutureWarning in visualization_agent.py"""
    
    file_path = 'agents/visualization_agent.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace deprecated errors='ignore'
    old_pattern = r"df\[col\] = pd\.to_numeric\(df\[col\], errors='ignore'\)"
    new_code = """try:
                df[col] = pd.to_numeric(df[col])
            except (ValueError, TypeError):
                pass  # Keep original if conversion fails"""
    
    content = re.sub(old_pattern, new_code, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed visualization_agent.py")

def fix_streamlit_app():
    """Fix deprecation warnings in streamlit_app.py"""
    
    file_path = 'streamlit_app.py'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace use_container_width in dataframe
    content = content.replace(
        'st.dataframe(\n        df,\n        use_container_width=True',
        'st.dataframe(\n        df,\n        width=\'stretch\''
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed streamlit_app.py")

if __name__ == "__main__":
    print("🔧 Fixing issues...")
    fix_visualization_agent()
    fix_streamlit_app()
    print("✅ All fixes applied!")