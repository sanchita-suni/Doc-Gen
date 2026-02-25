import streamlit as st
import os
import ast
import re
import pandas as pd
from java_parser import extract_java_docs
from sql_parser import extract_sql_docs
from architecture_map import generate_simple_diagram, generate_architecture_diagram, GRAPHVIZ_AVAILABLE
from io import BytesIO
from datetime import datetime

# Try to import reportlab for PDF generation
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Try to import sentence_transformers, but make it optional
try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Configure the page with custom theme
st.set_page_config(
    page_title="✨ Lumos Doc Gen",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced interactive theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@300;400;600;700&family=Varela+Round&family=Indie+Flower&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Nunito', sans-serif;
    }
    
    /* Main background with subtle pattern */
    .stApp {
        background-color: #FDFCFE;
        background-image:
            radial-gradient(circle at 20% 50%, rgba(232, 180, 240, 0.03) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(168, 213, 255, 0.03) 0%, transparent 50%);
    }
    
    /* Headings */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif;
        color: #6B5B7B;
        letter-spacing: -0.5px;
    }
    
    /* Post-it Note with glow */
    .postit-note {
        background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%);
        padding: 2rem;
        border-radius: 8px;
        box-shadow:
            0 8px 32px rgba(255, 249, 196, 0.4),
            0 2px 8px rgba(0, 0, 0, 0.1);
        transform: rotate(-2deg);
        max-width: 500px;
        margin: 3rem auto;
        font-family: 'Indie Flower', cursive;
        font-size: 1.2rem;
        line-height: 1.8;
        color: #5D4037;
        position: relative;
        transition: all 0.3s ease;
    }
    
    .postit-note:hover {
        transform: rotate(0deg) translateY(-5px);
        box-shadow:
            0 12px 48px rgba(255, 249, 196, 0.5),
            0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    .postit-note::before {
        content: '';
        position: absolute;
        top: -10px;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 20px;
        background: rgba(255, 255, 255, 0.4);
        border-radius: 2px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .logo-container {
        text-align: center;
        margin: 2rem auto;
        animation: fadeInDown 0.8s ease-out;
    }
    
    .logo-text {
        font-size: 4.5rem;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        background: linear-gradient(135deg, #E8B4F0 0%, #A8D5FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -2px;
        text-shadow: 0 0 40px rgba(232, 180, 240, 0.3);
    }
    
    /* Interactive Cards */
    .action-card {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        border: 2px solid transparent;
        box-shadow:
            0 4px 20px rgba(232, 180, 240, 0.1),
            0 0 0 1px rgba(232, 180, 240, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }
    
    .action-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, rgba(232, 180, 240, 0.05) 0%, rgba(168, 213, 255, 0.05) 100%);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .action-card:hover {
        transform: translateY(-8px);
        border-color: #E8B4F0;
        box-shadow:
            0 12px 40px rgba(232, 180, 240, 0.25),
            0 0 0 1px rgba(232, 180, 240, 0.2),
            0 0 60px rgba(232, 180, 240, 0.15);
    }
    
    .action-card:hover::before {
        opacity: 1;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFF5F8 0%, #F5F0FF 100%);
        border-right: 2px solid #FFE5F1;
    }
    
    [data-testid="stSidebar"] h1 {
        color: #E8B4F0;
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
    }
    
    /* Card Styling */
    .custom-card {
        background: white;
        padding: 1.5rem;
        border-radius: 20px;
        box-shadow: 0 4px 20px rgba(232, 180, 240, 0.15);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    
    .custom-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(232, 180, 240, 0.25);
        border-color: #FFE5F1;
    }
    
    /* Search Bar Styling with glow */
    .search-container {
        max-width: 700px;
        margin: 2rem auto;
        text-align: center;
    }
    
    .stTextInput > div > div > input {
        border-radius: 50px !important;
        border: 2px solid #E8B4F0 !important;
        padding: 1.2rem 2rem !important;
        font-size: 1.1rem !important;
        text-align: center !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow:
            0 4px 20px rgba(232, 180, 240, 0.15),
            0 0 0 0 rgba(232, 180, 240, 0) !important;
        background: white !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #A8D5FF !important;
        box-shadow:
            0 8px 32px rgba(168, 213, 255, 0.25),
            0 0 40px rgba(168, 213, 255, 0.15),
            0 0 0 4px rgba(168, 213, 255, 0.1) !important;
        transform: translateY(-2px) !important;
    }
    
    /* Enhanced Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, #FFB3D9 0%, #C9A3FF 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 0.9rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow:
            0 4px 20px rgba(232, 180, 240, 0.3),
            0 0 0 0 rgba(232, 180, 240, 0);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:hover {
        transform: translateY(-4px);
        box-shadow:
            0 8px 32px rgba(232, 180, 240, 0.4),
            0 0 60px rgba(232, 180, 240, 0.2);
        background: linear-gradient(135deg, #FFC4E5 0%, #D9B3FF 100%);
    }
    
    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton > button:active {
        transform: translateY(-2px);
    }
    
    /* Download Button Styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #FFD4A3 0%, #FFE5F1 100%);
        color: #6B5B7B;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 212, 163, 0.3);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(255, 212, 163, 0.4);
    }
    
    /* File Uploader Styling */
    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 20px;
        padding: 1.5rem;
        border: 2px dashed #E8B4F0;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #A8D5FF;
        background: #FEFBFF;
    }
    
    /* DataFrame Styling */
    .stDataFrame {
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(232, 180, 240, 0.15);
    }
    
    /* Input Fields */
    .stTextInput > div > div > input {
        border-radius: 15px;
        border: 2px solid #FFE5F1;
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #E8B4F0;
        box-shadow: 0 0 0 3px rgba(232, 180, 240, 0.1);
    }
    
    /* Success/Info/Warning Messages */
    .stSuccess {
        background: linear-gradient(135deg, #D4FFE5 0%, #E5F8FF 100%);
        border-radius: 15px;
        border-left: 4px solid #A8FFD5;
        padding: 1rem;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #E5F8FF 0%, #F5F0FF 100%);
        border-radius: 15px;
        border-left: 4px solid #A8D5FF;
        padding: 1rem;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #FFF5E5 0%, #FFE5F1 100%);
        border-radius: 15px;
        border-left: 4px solid #FFD4A3;
        padding: 1rem;
    }
    
    /* Enhanced Metric Cards with glow */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        background: linear-gradient(135deg, #E8B4F0 0%, #A8D5FF 100%);
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    
    [data-testid="stMetric"] {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow:
            0 4px 20px rgba(232, 180, 240, 0.1),
            0 0 0 1px rgba(232, 180, 240, 0.1);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow:
            0 8px 32px rgba(232, 180, 240, 0.2),
            0 0 60px rgba(232, 180, 240, 0.1);
    }
    
    /* Enhanced DataFrame styling */
    .stDataFrame {
        border-radius: 16px !important;
        overflow: hidden !important;
        box-shadow:
            0 4px 20px rgba(232, 180, 240, 0.15),
            0 0 0 1px rgba(232, 180, 240, 0.1) !important;
    }
    
    /* Divider */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #FFE5F1, transparent);
        margin: 2rem 0;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.8;
        }
    }
    
    @keyframes glow {
        0%, 100% {
            box-shadow: 0 0 20px rgba(232, 180, 240, 0.3);
        }
        50% {
            box-shadow: 0 0 40px rgba(232, 180, 240, 0.5);
        }
    }
    
    /* Icon Styling */
    .icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        animation: pulse 2s infinite;
    }
    
    /* Section Headers */
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        color: #6B5B7B;
        font-weight: 600;
    }
    
    /* Subheader with icon */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Feature Cards */
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(232, 180, 240, 0.15);
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(232, 180, 240, 0.25);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    /* Accessibility - High Contrast Mode Support */
    @media (prefers-contrast: high) {
        .stApp {
            background: white;
        }
        .custom-card {
            border: 2px solid #6B5B7B;
        }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        .hero-subtitle {
            font-size: 1.1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Load the sentence transformer model
@st.cache_resource
def load_model():
    """Load the sentence transformer model for semantic search."""
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    return SentenceTransformer('all-MiniLM-L6-v2')


def generate_usage_template(func_name, params, language='python'):
    """
    Generate a usage example template for a function.
    
    Args:
        func_name (str): Name of the function
        params (list): List of parameter names
        language (str): Programming language ('python', 'javascript', 'java', 'sql')
    
    Returns:
        str: Usage example template
    """
    if not params:
        params = []
    
    # Create parameter placeholders
    param_placeholders = []
    for param in params:
        # Remove default values and type hints
        clean_param = param.split('=')[0].split(':')[0].strip()
        if clean_param and clean_param not in ['self', 'cls']:
            param_placeholders.append(clean_param)
    
    params_str = ', '.join(param_placeholders) if param_placeholders else ''
    
    # Generate language-specific templates
    if language == 'python':
        return f"""# Example usage:
result = {func_name}({params_str})
print(result)"""
    
    elif language == 'javascript':
        return f"""// Example usage:
const result = {func_name}({params_str});
console.log(result);"""
    
    elif language == 'java':
        return f"""// Example usage:
Object result = {func_name}({params_str});
System.out.println(result);"""
    
    elif language == 'sql':
        if params_str:
            return f"""-- Example usage:
SELECT {func_name}({params_str});"""
        else:
            return f"""-- Example usage:
CALL {func_name}();"""
    
    else:
        return f"// Example: {func_name}({params_str})"


def extract_function_metadata(source_code, language='python', limit=5):
    """
    Extract detailed metadata for functions including source code and usage examples.
    
    Args:
        source_code (str): Source code to parse
        language (str): Programming language
        limit (int): Maximum number of functions to extract (default: 5)
    
    Returns:
        list: List of function metadata dictionaries
    """
    functions = []
    
    try:
        if language == 'python':
            # Parse Python using AST
            tree = ast.parse(source_code)
            lines = source_code.split('\n')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract function name
                    func_name = node.name
                    
                    # Extract parameters
                    params = []
                    for arg in node.args.args:
                        param_name = arg.arg
                        # Include type annotation if present
                        if arg.annotation:
                            param_name += f": {ast.unparse(arg.annotation)}"
                        params.append(param_name)
                    
                    # Extract docstring
                    docstring = ast.get_docstring(node) or "No documentation available"
                    
                    # Extract function body source code
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                    source_body = '\n'.join(lines[start_line:end_line])
                    
                    # Generate usage example
                    usage_example = generate_usage_template(func_name, params, 'python')
                    
                    functions.append({
                        'name': func_name,
                        'params': params,
                        'docstring': docstring,
                        'source_code': source_body,
                        'usage_example': usage_example,
                        'language': 'python',
                        'type': 'function'
                    })
                    
                    if len(functions) >= limit:
                        break
        
        elif language == 'javascript':
            lines = source_code.split('\n')
            
            # Regular function pattern
            func_pattern = r'function\s+(\w+)\s*\((.*?)\)\s*\{'
            matches = list(re.finditer(func_pattern, source_code))
            
            for match in matches[:limit]:
                func_name = match.group(1)
                params_str = match.group(2)
                params = [p.strip() for p in params_str.split(',') if p.strip()]
                
                # Find function body
                start_pos = match.start()
                start_line = source_code[:start_pos].count('\n')
                
                # Find matching closing brace
                brace_count = 1
                pos = match.end()
                while pos < len(source_code) and brace_count > 0:
                    if source_code[pos] == '{':
                        brace_count += 1
                    elif source_code[pos] == '}':
                        brace_count -= 1
                    pos += 1
                
                end_line = source_code[:pos].count('\n')
                source_body = '\n'.join(lines[start_line:end_line + 1])
                
                # Try to find JSDoc comment
                before_func = source_code[:start_pos]
                jsdoc_pattern = r'/\*\*(.*?)\*/'
                jsdoc_matches = list(re.finditer(jsdoc_pattern, before_func, re.DOTALL))
                docstring = "No documentation available"
                if jsdoc_matches:
                    last_jsdoc = jsdoc_matches[-1].group(1).strip()
                    docstring = '\n'.join(line.strip().lstrip('*').strip() for line in last_jsdoc.split('\n'))
                
                usage_example = generate_usage_template(func_name, params, 'javascript')
                
                functions.append({
                    'name': func_name,
                    'params': params,
                    'docstring': docstring,
                    'source_code': source_body,
                    'usage_example': usage_example,
                    'language': 'javascript',
                    'type': 'function'
                })
            
            # Arrow functions
            arrow_pattern = r'const\s+(\w+)\s*=\s*\((.*?)\)\s*=>'
            arrow_matches = list(re.finditer(arrow_pattern, source_code))
            
            for match in arrow_matches[:max(0, limit - len(functions))]:
                func_name = match.group(1)
                params_str = match.group(2)
                params = [p.strip() for p in params_str.split(',') if p.strip()]
                
                start_pos = match.start()
                start_line = source_code[:start_pos].count('\n')
                
                # Find end of arrow function (semicolon or newline)
                end_pos = source_code.find(';', match.end())
                if end_pos == -1:
                    end_pos = source_code.find('\n\n', match.end())
                if end_pos == -1:
                    end_pos = len(source_code)
                
                end_line = source_code[:end_pos].count('\n')
                source_body = '\n'.join(lines[start_line:end_line + 1])
                
                usage_example = generate_usage_template(func_name, params, 'javascript')
                
                functions.append({
                    'name': func_name,
                    'params': params,
                    'docstring': "Arrow function - No documentation available",
                    'source_code': source_body,
                    'usage_example': usage_example,
                    'language': 'javascript',
                    'type': 'function'
                })
        
        elif language == 'java':
            lines = source_code.split('\n')
            
            # Java method pattern
            method_pattern = r'(public|private|protected)?\s*(static)?\s*(\w+)\s+(\w+)\s*\((.*?)\)\s*\{'
            matches = list(re.finditer(method_pattern, source_code))
            
            for match in matches[:limit]:
                func_name = match.group(4)
                params_str = match.group(5)
                
                # Parse parameters
                params = []
                if params_str.strip():
                    for param in params_str.split(','):
                        param = param.strip()
                        if param:
                            # Extract parameter name (last word)
                            parts = param.split()
                            if parts:
                                params.append(parts[-1])
                
                start_pos = match.start()
                start_line = source_code[:start_pos].count('\n')
                
                # Find matching closing brace
                brace_count = 1
                pos = match.end()
                while pos < len(source_code) and brace_count > 0:
                    if source_code[pos] == '{':
                        brace_count += 1
                    elif source_code[pos] == '}':
                        brace_count -= 1
                    pos += 1
                
                end_line = source_code[:pos].count('\n')
                source_body = '\n'.join(lines[start_line:end_line + 1])
                
                # Try to find Javadoc comment
                before_method = source_code[:start_pos]
                javadoc_pattern = r'/\*\*(.*?)\*/'
                javadoc_matches = list(re.finditer(javadoc_pattern, before_method, re.DOTALL))
                docstring = "No documentation available"
                if javadoc_matches:
                    last_javadoc = javadoc_matches[-1].group(1).strip()
                    docstring = '\n'.join(line.strip().lstrip('*').strip() for line in last_javadoc.split('\n'))
                
                usage_example = generate_usage_template(func_name, params, 'java')
                
                functions.append({
                    'name': func_name,
                    'params': params,
                    'docstring': docstring,
                    'source_code': source_body,
                    'usage_example': usage_example,
                    'language': 'java',
                    'type': 'method'
                })
        
        elif language == 'sql':
            lines = source_code.split('\n')
            
            # SQL function/procedure pattern
            func_pattern = r'CREATE\s+(FUNCTION|PROCEDURE)\s+(\w+)\s*\((.*?)\)'
            matches = list(re.finditer(func_pattern, source_code, re.IGNORECASE | re.DOTALL))
            
            for match in matches[:limit]:
                func_type = match.group(1).upper()
                func_name = match.group(2)
                params_str = match.group(3)
                
                # Parse parameters
                params = []
                if params_str.strip():
                    for param in params_str.split(','):
                        param = param.strip()
                        if param:
                            # Extract parameter name (first word)
                            parts = param.split()
                            if parts:
                                params.append(parts[0])
                
                start_pos = match.start()
                start_line = source_code[:start_pos].count('\n')
                
                # Find END statement
                end_pattern = r'END\s*;'
                end_match = re.search(end_pattern, source_code[match.end():], re.IGNORECASE)
                if end_match:
                    end_pos = match.end() + end_match.end()
                    end_line = source_code[:end_pos].count('\n')
                else:
                    end_line = min(start_line + 20, len(lines) - 1)
                
                source_body = '\n'.join(lines[start_line:end_line + 1])
                
                usage_example = generate_usage_template(func_name, params, 'sql')
                
                functions.append({
                    'name': func_name,
                    'params': params,
                    'docstring': f"SQL {func_type}",
                    'source_code': source_body,
                    'usage_example': usage_example,
                    'language': 'sql',
                    'type': func_type.lower()
                })
    
    except Exception as e:
        print(f"Error extracting function metadata: {str(e)}")
    
    return functions


def generate_html_report(processed_data, output_file='function_report.html'):
    """
    Generate an interactive HTML report with split-screen layout.
    
    Args:
        processed_data (list): Output from process_files() function
        output_file (str): Output HTML file name
    
    Returns:
        str: Path to the generated HTML file
    """
    import html
    import json
    from datetime import datetime
    
    # Prepare data for JavaScript
    functions_data = []
    for file_data in processed_data:
        for func in file_data['functions']:
            functions_data.append({
                'file': file_data['file_name'],
                'file_path': file_data['file_path'],
                'language': file_data['language'],
                'name': func['name'],
                'params': func['params'],
                'docstring': func['docstring'],
                'usage_example': func['usage_example'],
                'source_code': func['source_code'],
                'type': func['type']
            })
    
    # Generate HTML
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Function Documentation Report</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            height: 100vh;
            overflow: hidden;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .container {{
            display: flex;
            height: 100vh;
            background: white;
        }}
        
        /* Left Panel - Navigation */
        .left-panel {{
            width: 350px;
            background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
            border-right: 2px solid #dee2e6;
            overflow-y: auto;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        
        .header h1 {{
            font-size: 24px;
            margin-bottom: 5px;
        }}
        
        .header p {{
            font-size: 12px;
            opacity: 0.9;
        }}
        
        .search-box {{
            padding: 15px;
            background: white;
            border-bottom: 1px solid #dee2e6;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        
        .file-group {{
            margin: 10px;
        }}
        
        .file-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 15px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: all 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .file-header:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}
        
        .file-header .icon {{
            font-size: 18px;
        }}
        
        .file-header .count {{
            margin-left: auto;
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
        }}
        
        .function-list {{
            background: white;
            margin: 5px 10px 10px 10px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        
        .function-item {{
            padding: 12px 15px;
            cursor: pointer;
            border-bottom: 1px solid #f8f9fa;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .function-item:last-child {{
            border-bottom: none;
        }}
        
        .function-item:hover {{
            background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
            padding-left: 20px;
        }}
        
        .function-item.active {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
        }}
        
        .function-item .type-badge {{
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 10px;
            text-transform: uppercase;
        }}
        
        .function-item.active .type-badge {{
            background: rgba(255,255,255,0.3);
        }}
        
        .function-item .name {{
            flex: 1;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        
        /* Right Panel - Details */
        .right-panel {{
            flex: 1;
            overflow-y: auto;
            background: #ffffff;
        }}
        
        .welcome {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }}
        
        .welcome .icon {{
            font-size: 80px;
            margin-bottom: 20px;
            opacity: 0.3;
        }}
        
        .welcome h2 {{
            font-size: 28px;
            margin-bottom: 10px;
            color: #495057;
        }}
        
        .welcome p {{
            font-size: 16px;
            max-width: 500px;
        }}
        
        .detail-view {{
            display: none;
            padding: 30px;
            animation: fadeIn 0.3s;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .detail-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }}
        
        .detail-header h2 {{
            font-size: 32px;
            margin-bottom: 10px;
            font-family: 'Courier New', monospace;
        }}
        
        .detail-header .meta {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 15px;
        }}
        
        .detail-header .meta-item {{
            background: rgba(255,255,255,0.2);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 13px;
        }}
        
        .section {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: all 0.3s;
        }}
        
        .section:hover {{
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 15px;
            color: #495057;
            display: flex;
            align-items: center;
            gap: 10px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .section-title .icon {{
            font-size: 24px;
        }}
        
        .section-content {{
            color: #6c757d;
            line-height: 1.8;
            font-size: 15px;
        }}
        
        .code-block {{
            background: #1e1e1e;
            border-radius: 8px;
            padding: 20px;
            overflow-x: auto;
            margin-top: 10px;
        }}
        
        .code-block pre {{
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
        }}
        
        .code-block code {{
            color: #d4d4d4;
        }}
        
        .params-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}
        
        .param-badge {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            box-shadow: 0 2px 5px rgba(102, 126, 234, 0.3);
        }}
        
        /* Language Icons */
        .lang-python {{ color: #3776ab; }}
        .lang-javascript {{ color: #f7df1e; }}
        .lang-java {{ color: #007396; }}
        .lang-sql {{ color: #00758f; }}
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }}
        
        /* Stats Bar */
        .stats-bar {{
            background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 15px;
            display: flex;
            justify-content: space-around;
            border-bottom: 2px solid #dee2e6;
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #667eea;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Left Panel -->
        <div class="left-panel">
            <div class="header">
                <h1>✨ Function Explorer</h1>
                <p>Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
            </div>
            
            <div class="stats-bar">
                <div class="stat-item">
                    <div class="stat-value" id="total-files">0</div>
                    <div class="stat-label">Files</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="total-functions">0</div>
                    <div class="stat-label">Functions</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="total-languages">0</div>
                    <div class="stat-label">Languages</div>
                </div>
            </div>
            
            <div class="search-box">
                <input type="text" id="search-input" placeholder="🔍 Search functions...">
            </div>
            
            <div id="navigation-tree"></div>
        </div>
        
        <!-- Right Panel -->
        <div class="right-panel">
            <div class="welcome" id="welcome-view">
                <div class="icon">📚</div>
                <h2>Welcome to Function Explorer</h2>
                <p>Select a function from the left panel to view its documentation, usage examples, and source code.</p>
            </div>
            
            <div class="detail-view" id="detail-view">
                <div class="detail-header">
                    <h2 id="func-name"></h2>
                    <div class="meta">
                        <div class="meta-item">📄 <span id="func-file"></span></div>
                        <div class="meta-item">💻 <span id="func-language"></span></div>
                        <div class="meta-item">🏷️ <span id="func-type"></span></div>
                    </div>
                    <div class="params-list" id="func-params"></div>
                </div>
                
                <div class="section">
                    <div class="section-title">
                        <span class="icon">📖</span>
                        Explanation
                    </div>
                    <div class="section-content" id="func-explanation"></div>
                </div>
                
                <div class="section">
                    <div class="section-title">
                        <span class="icon">💡</span>
                        Usage Example
                    </div>
                    <div class="section-content">
                        <div class="code-block">
                            <pre><code id="func-usage" class="language-python"></code></pre>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">
                        <span class="icon">📝</span>
                        Source Code
                    </div>
                    <div class="section-content">
                        <div class="code-block">
                            <pre><code id="func-source" class="language-python"></code></pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Function data
        const functionsData = {json.dumps(functions_data, indent=8)};
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            renderNavigationTree();
            updateStats();
            setupSearch();
        }});
        
        function renderNavigationTree() {{
            const tree = document.getElementById('navigation-tree');
            const fileGroups = {{}};
            
            // Group functions by file
            functionsData.forEach(func => {{
                if (!fileGroups[func.file]) {{
                    fileGroups[func.file] = {{
                        language: func.language,
                        functions: []
                    }};
                }}
                fileGroups[func.file].functions.push(func);
            }});
            
            // Render each file group
            Object.keys(fileGroups).sort().forEach(fileName => {{
                const group = fileGroups[fileName];
                const langIcon = getLangIcon(group.language);
                
                const fileDiv = document.createElement('div');
                fileDiv.className = 'file-group';
                fileDiv.innerHTML = `
                    <div class="file-header">
                        <span class="icon">${{langIcon}}</span>
                        <span>${{fileName}}</span>
                        <span class="count">${{group.functions.length}}</span>
                    </div>
                    <div class="function-list" id="list-${{fileName.replace(/[^a-zA-Z0-9]/g, '_')}}">
                    </div>
                `;
                
                tree.appendChild(fileDiv);
                
                const funcList = fileDiv.querySelector('.function-list');
                group.functions.forEach((func, index) => {{
                    const funcItem = document.createElement('div');
                    funcItem.className = 'function-item';
                    funcItem.innerHTML = `
                        <span class="type-badge">${{func.type}}</span>
                        <span class="name">${{func.name}}</span>
                    `;
                    funcItem.onclick = () => showFunctionDetails(func, funcItem);
                    funcList.appendChild(funcItem);
                }});
            }});
        }}
        
        function showFunctionDetails(func, element) {{
            // Update active state
            document.querySelectorAll('.function-item').forEach(item => {{
                item.classList.remove('active');
            }});
            element.classList.add('active');
            
            // Hide welcome, show details
            document.getElementById('welcome-view').style.display = 'none';
            document.getElementById('detail-view').style.display = 'block';
            
            // Update content
            document.getElementById('func-name').textContent = func.name;
            document.getElementById('func-file').textContent = func.file;
            document.getElementById('func-language').textContent = func.language.toUpperCase();
            document.getElementById('func-type').textContent = func.type.toUpperCase();
            
            // Parameters
            const paramsDiv = document.getElementById('func-params');
            paramsDiv.innerHTML = '';
            if (func.params && func.params.length > 0) {{
                func.params.forEach(param => {{
                    const badge = document.createElement('div');
                    badge.className = 'param-badge';
                    badge.textContent = param;
                    paramsDiv.appendChild(badge);
                }});
            }} else {{
                paramsDiv.innerHTML = '<div class="param-badge">No parameters</div>';
            }}
            
            // Explanation
            document.getElementById('func-explanation').textContent = func.docstring;
            
            // Usage example
            const usageCode = document.getElementById('func-usage');
            usageCode.textContent = func.usage_example;
            usageCode.className = `language-${{func.language}}`;
            
            // Source code
            const sourceCode = document.getElementById('func-source');
            sourceCode.textContent = func.source_code;
            sourceCode.className = `language-${{func.language}}`;
            
            // Apply syntax highlighting
            hljs.highlightAll();
            
            // Scroll to top
            document.querySelector('.right-panel').scrollTop = 0;
        }}
        
        function updateStats() {{
            const files = new Set(functionsData.map(f => f.file));
            const languages = new Set(functionsData.map(f => f.language));
            
            document.getElementById('total-files').textContent = files.size;
            document.getElementById('total-functions').textContent = functionsData.length;
            document.getElementById('total-languages').textContent = languages.size;
        }}
        
        function setupSearch() {{
            const searchInput = document.getElementById('search-input');
            searchInput.addEventListener('input', function(e) {{
                const query = e.target.value.toLowerCase();
                document.querySelectorAll('.function-item').forEach(item => {{
                    const name = item.querySelector('.name').textContent.toLowerCase();
                    if (name.includes(query)) {{
                        item.style.display = 'flex';
                    }} else {{
                        item.style.display = 'none';
                    }}
                }});
            }});
        }}
        
        function getLangIcon(language) {{
            const icons = {{
                'python': '🐍',
                'javascript': '📜',
                'java': '☕',
                'sql': '🗄️'
            }};
            return icons[language] || '📄';
        }}
    </script>
</body>
</html>'''
    
    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML report generated: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error generating HTML report: {str(e)}")
        return None


def process_files(file_paths_or_data, language=None):
    """
    Process multiple files and extract structured metadata for all functions.
    
    Args:
        file_paths_or_data: Either a list of file paths (str) or a dict from ingest_codebase
        language (str, optional): Language if processing single file
    
    Returns:
        list: List of file metadata objects containing function details
    """
    processed_data = []
    
    # Handle dict input from ingest_codebase
    if isinstance(file_paths_or_data, dict):
        for lang, lang_data in file_paths_or_data.items():
            if lang == 'summary':
                continue
            
            files = lang_data.get('files', [])
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        source_code = f.read()
                    
                    # Extract function metadata (at least 5 per file)
                    functions = extract_function_metadata(source_code, lang, limit=5)
                    
                    if functions:
                        processed_data.append({
                            'file_path': file_path,
                            'file_name': os.path.basename(file_path),
                            'language': lang,
                            'function_count': len(functions),
                            'functions': functions
                        })
                
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
    
    # Handle list of file paths
    elif isinstance(file_paths_or_data, list):
        for file_path in file_paths_or_data:
            try:
                # Determine language from extension
                ext = os.path.splitext(file_path)[1].lower()
                lang_map = {'.py': 'python', '.js': 'javascript', '.java': 'java', '.sql': 'sql'}
                file_lang = language or lang_map.get(ext, 'unknown')
                
                if file_lang == 'unknown':
                    continue
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    source_code = f.read()
                
                # Extract function metadata (at least 5 per file)
                functions = extract_function_metadata(source_code, file_lang, limit=5)
                
                if functions:
                    processed_data.append({
                        'file_path': file_path,
                        'file_name': os.path.basename(file_path),
                        'language': file_lang,
                        'function_count': len(functions),
                        'functions': functions
                    })
            
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
    
    return processed_data


def extract_python_docs(source_code):
    """Extract documentation from Python source code using AST parsing with enhanced fallbacks."""
    entities = []
    
    try:
        tree = ast.parse(source_code)
        lines = source_code.split('\n')
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.name
                args_list = [arg.arg for arg in node.args.args]
                docstring = ast.get_docstring(node)
                
                # If no docstring, try to extract inline comments or generate basic docs
                if docstring is None:
                    # Try to find comments before the function
                    if hasattr(node, 'lineno') and node.lineno > 1:
                        comment_lines = []
                        for i in range(max(0, node.lineno - 4), node.lineno - 1):
                            if i < len(lines):
                                line = lines[i].strip()
                                if line.startswith('#'):
                                    comment_lines.append(line[1:].strip())
                        
                        if comment_lines:
                            docstring = ' '.join(comment_lines)
                        else:
                            # Generate basic documentation from function signature
                            docstring = f"Function: {func_name}"
                            if args_list:
                                docstring += f"\nParameters: {', '.join(args_list)}"
                            else:
                                docstring += "\nNo parameters"
                            
                            # Try to infer purpose from function name
                            name_parts = func_name.replace('_', ' ').replace('get', 'retrieves').replace('set', 'sets').replace('calculate', 'calculates').replace('create', 'creates').replace('update', 'updates').replace('delete', 'deletes')
                            docstring += f"\nInferred purpose: {name_parts}"
                    else:
                        # Fallback: basic signature info
                        docstring = f"Function with {len(args_list)} parameter(s)"
                        if args_list:
                            docstring += f": {', '.join(args_list)}"
                
                entity = {
                    "Name": func_name,
                    "Type": "Function",
                    "Params": args_list,
                    "Docs": docstring
                }
                
                entities.append(entity)
                
    except IndentationError as e:
        st.error(f"IndentationError: {str(e)}")
        return []
    except SyntaxError as e:
        st.error(f"SyntaxError: {str(e)}")
        return []
    except Exception as e:
        st.error(f"Error parsing Python code: {str(e)}")
        return []
    
    return entities


def extract_js_docs(source_code):
    """Extract documentation from JavaScript source code with JSDoc and comment support."""
    entities = []
    lines = source_code.split('\n')
    
    try:
        # Pattern to find JSDoc comments
        jsdoc_pattern = r'/\*\*(.*?)\*/'
        
        # Traditional function pattern
        traditional_pattern = r'function\s+(\w+)\s*\((.*?)\)'
        traditional_matches = re.finditer(traditional_pattern, source_code)
        
        for match in traditional_matches:
            func_name = match.group(1)
            params_str = match.group(2)
            params_list = [p.strip() for p in params_str.split(',') if p.strip()]
            
            # Try to find JSDoc or comments before the function
            func_start = match.start()
            before_func = source_code[:func_start]
            
            # Look for JSDoc comment
            jsdoc_matches = list(re.finditer(jsdoc_pattern, before_func, re.DOTALL))
            if jsdoc_matches:
                # Get the last JSDoc comment before the function
                last_jsdoc = jsdoc_matches[-1].group(1).strip()
                # Clean up JSDoc formatting
                docs = '\n'.join(line.strip().lstrip('*').strip() for line in last_jsdoc.split('\n'))
            else:
                # Look for inline comments
                func_line = source_code[:func_start].count('\n')
                comment_lines = []
                for i in range(max(0, func_line - 3), func_line):
                    if i < len(lines):
                        line = lines[i].strip()
                        if line.startswith('//'):
                            comment_lines.append(line[2:].strip())
                
                if comment_lines:
                    docs = ' '.join(comment_lines)
                else:
                    # Generate basic docs
                    docs = f"Function: {func_name}"
                    if params_list:
                        docs += f"\nParameters: {', '.join(params_list)}"
                    # Convert camelCase to readable text
                    name_hint = re.sub(r'([A-Z])', r' \1', func_name).strip().lower()
                    docs += f"\nInferred purpose: {name_hint}"
            
            entity = {
                "Name": func_name,
                "Type": "Function",
                "Params": params_list,
                "Docs": docs
            }
            entities.append(entity)
        
        # Arrow function pattern
        arrow_pattern = r'const\s+(\w+)\s*=\s*\((.*?)\)\s*=>'
        arrow_matches = re.finditer(arrow_pattern, source_code)
        
        for match in arrow_matches:
            func_name = match.group(1)
            params_str = match.group(2)
            params_list = [p.strip() for p in params_str.split(',') if p.strip()]
            
            # Try to find comments before the arrow function
            func_start = match.start()
            before_func = source_code[:func_start]
            
            # Look for JSDoc comment
            jsdoc_matches = list(re.finditer(jsdoc_pattern, before_func, re.DOTALL))
            if jsdoc_matches:
                last_jsdoc = jsdoc_matches[-1].group(1).strip()
                docs = '\n'.join(line.strip().lstrip('*').strip() for line in last_jsdoc.split('\n'))
            else:
                # Look for inline comments
                func_line = source_code[:func_start].count('\n')
                comment_lines = []
                for i in range(max(0, func_line - 3), func_line):
                    if i < len(lines):
                        line = lines[i].strip()
                        if line.startswith('//'):
                            comment_lines.append(line[2:].strip())
                
                if comment_lines:
                    docs = ' '.join(comment_lines)
                else:
                    # Generate basic docs
                    docs = f"Arrow function: {func_name}"
                    if params_list:
                        docs += f"\nParameters: {', '.join(params_list)}"
            
            entity = {
                "Name": func_name,
                "Type": "Function",
                "Params": params_list,
                "Docs": docs
            }
            entities.append(entity)
            
    except Exception as e:
        st.error(f"Error parsing JavaScript code: {str(e)}")
        return []
    
    return entities


def ingest_codebase(path):
    """
    Ingest an entire codebase from a directory path.
    Recursively traverses directories, collects all code files, and extracts documentation.
    
    Args:
        path (str): Path to directory or single file
        
    Returns:
        dict: Structured data grouped by language with extracted entities
        {
            'python': {'files': [...], 'entities': [...]},
            'javascript': {'files': [...], 'entities': [...]},
            'java': {'files': [...], 'entities': [...]},
            'sql': {'files': [...], 'entities': [...]},
            'summary': {'total_files': int, 'total_entities': int}
        }
    """
    # Initialize result structure
    result = {
        'python': {'files': [], 'entities': []},
        'javascript': {'files': [], 'entities': []},
        'java': {'files': [], 'entities': []},
        'sql': {'files': [], 'entities': []},
        'summary': {'total_files': 0, 'total_entities': 0}
    }
    
    # Directories and files to ignore
    ignore_dirs = {
        'node_modules', '__pycache__', '.git', '.svn', 'venv', 'env',
        'dist', 'build', '.idea', '.vscode', 'target', 'bin', 'obj'
    }
    ignore_files = {'.DS_Store', 'Thumbs.db', '.gitignore', '.gitkeep'}
    
    # Supported file extensions
    extensions = {
        '.py': 'python',
        '.js': 'javascript',
        '.java': 'java',
        '.sql': 'sql'
    }
    
    def should_ignore(name):
        """Check if file/directory should be ignored."""
        return name in ignore_dirs or name in ignore_files or name.startswith('.')
    
    def process_file(file_path, language):
        """Process a single file and extract entities."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract entities based on language
            entities = []
            if language == 'python':
                entities = extract_python_docs(content)
            elif language == 'javascript':
                entities = extract_js_docs(content)
            elif language == 'java':
                entities = extract_java_docs(content)
            elif language == 'sql':
                entities = extract_sql_docs(content)
            
            # Add file info to each entity
            for entity in entities:
                entity['source_file'] = file_path
            
            return entities
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return []
    
    def traverse_directory(dir_path):
        """Recursively traverse directory and collect code files."""
        try:
            for entry in os.listdir(dir_path):
                # Skip ignored items
                if should_ignore(entry):
                    continue
                
                full_path = os.path.join(dir_path, entry)
                
                # If directory, recurse
                if os.path.isdir(full_path):
                    traverse_directory(full_path)
                
                # If file, check extension and process
                elif os.path.isfile(full_path):
                    _, ext = os.path.splitext(entry)
                    if ext in extensions:
                        language = extensions[ext]
                        
                        # Add file to list
                        result[language]['files'].append(full_path)
                        result['summary']['total_files'] += 1
                        
                        # Extract entities
                        entities = process_file(full_path, language)
                        result[language]['entities'].extend(entities)
                        result['summary']['total_entities'] += len(entities)
        
        except PermissionError:
            print(f"Permission denied: {dir_path}")
        except Exception as e:
            print(f"Error traversing {dir_path}: {str(e)}")
    
    # Check if path is file or directory
    if os.path.isfile(path):
        # Single file
        _, ext = os.path.splitext(path)
        if ext in extensions:
            language = extensions[ext]
            result[language]['files'].append(path)
            result['summary']['total_files'] = 1
            
            entities = process_file(path, language)
            result[language]['entities'].extend(entities)
            result['summary']['total_entities'] = len(entities)
    
    elif os.path.isdir(path):
        # Directory - traverse recursively
        traverse_directory(path)
    
    else:
        raise ValueError(f"Invalid path: {path}")
    
    return result


def perform_search(query, entities):
    """Perform semantic search on entities using sentence transformers."""
    if not entities or not query:
        return None
    
    if not SENTENCE_TRANSFORMERS_AVAILABLE:
        st.error("Search functionality requires sentence-transformers. Install with: `pip install sentence-transformers`")
        return None
    
    try:
        model = load_model()
        
        if model is None:
            st.error("Failed to load the model. Please install sentence-transformers.")
            return None
        
        entity_texts = []
        for entity in entities:
            combined_text = f"{entity['Name']} {entity['Docs']}"
            entity_texts.append(combined_text)
        
        query_embedding = model.encode(query, convert_to_tensor=True)
        entity_embeddings = model.encode(entity_texts, convert_to_tensor=True)
        
        similarities = util.cos_sim(query_embedding, entity_embeddings)[0]
        
        top_idx = similarities.argmax().item()
        top_score = similarities[top_idx].item()
        
        top_entity = entities[top_idx].copy()
        top_entity['similarity_score'] = top_score
        
        return top_entity
        
    except Exception as e:
        st.error(f"Error during search: {str(e)}")
        return None


def generate_markdown(entities):
    """Generate markdown documentation from entities."""
    markdown_content = "# Function Documentation\n\n"
    
    for entity in entities:
        markdown_content += f"## {entity['Name']}\n\n"
        markdown_content += f"**Type:** {entity['Type']}\n\n"
        
        if entity['Params']:
            markdown_content += f"**Parameters:** {', '.join(entity['Params'])}\n\n"
        else:
            markdown_content += "**Parameters:** None\n\n"
        
        markdown_content += f"**Documentation:**\n\n{entity['Docs']}\n\n"
        markdown_content += "---\n\n"
    
    return markdown_content


def generate_csv(entities):
    """Generate CSV from entities."""
    df = pd.DataFrame(entities)
    df['Params'] = df['Params'].apply(lambda x: ', '.join(x) if x else 'None')
    csv_content = df.to_csv(index=False)
    
    return csv_content


def calculate_time_saved(entities):
    """
    Calculate estimated time saved by using Lumos instead of manually reading code.
    
    More realistic assumptions:
    - Reading and understanding a function: 8-12 minutes (including context, dependencies)
    - Reading and understanding a class: 15-20 minutes (multiple methods, relationships)
    - Reading a table schema: 5-8 minutes (understanding columns, relationships)
    - Reading a view: 6-10 minutes (understanding the query logic)
    - Reading a procedure/function: 10-15 minutes (complex logic, parameters)
    - Lumos processes everything in seconds
    
    Returns:
        tuple: (minutes_saved, hours_saved, formatted_string)
    """
    time_per_entity = {
        'Function': 10,  # minutes - realistic time to understand function logic
        'Method': 10,    # minutes - similar to function
        'Class': 18,     # minutes - multiple methods and relationships
        'Table': 7,      # minutes - understanding schema and relationships
        'View': 8,       # minutes - understanding query logic
        'Procedure': 12, # minutes - complex stored procedure logic
        'Unknown': 8     # minutes - conservative estimate
    }
    
    total_minutes = 0
    for entity in entities:
        entity_type = entity.get('Type', 'Unknown')
        total_minutes += time_per_entity.get(entity_type, 8)
    
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    
    if hours > 0:
        return total_minutes, hours, f"{hours}h {minutes}m"
    else:
        return total_minutes, 0, f"{minutes} minutes"


def generate_pdf(entities):
    """Generate a well-structured PDF document from entities."""
    if not REPORTLAB_AVAILABLE:
        return None
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []
    
    # Define custom styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6B5B7B'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Heading style
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#E8B4F0'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Subheading style
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#8B7B9B'),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    # Body style
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#4A4A4A'),
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    # Code style
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=9,
        textColor=colors.HexColor('#2C2C2C'),
        backColor=colors.HexColor('#F5F5F5'),
        spaceAfter=12,
        fontName='Courier'
    )
    
    # Add title
    story.append(Paragraph("📚 Code Documentation", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Add generation info
    generation_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    story.append(Paragraph(f"<i>Generated on {generation_date}</i>", body_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Add summary section
    story.append(Paragraph("📊 Documentation Summary", heading_style))
    
    # Create summary table
    types_count = {}
    for entity in entities:
        entity_type = entity['Type']
        types_count[entity_type] = types_count.get(entity_type, 0) + 1
    
    documented = sum(1 for e in entities if e['Docs'] != "No documentation found")
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Entities', str(len(entities))],
        ['Documented Entities', f"{documented} ({documented*100//len(entities)}%)"],
        ['Unique Types', str(len(types_count))]
    ]
    
    for entity_type, count in sorted(types_count.items()):
        summary_data.append([f'{entity_type}s', str(count)])
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8D5FF')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#6B5B7B')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FEFBFF')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E8B4F0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F0FF')])
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 0.4*inch))
    story.append(PageBreak())
    
    # Group entities by type
    entities_by_type = {}
    for entity in entities:
        entity_type = entity['Type']
        if entity_type not in entities_by_type:
            entities_by_type[entity_type] = []
        entities_by_type[entity_type].append(entity)
    
    # Add detailed documentation for each type
    for entity_type, type_entities in sorted(entities_by_type.items()):
        # Type header
        story.append(Paragraph(f"📑 {entity_type}s ({len(type_entities)})", heading_style))
        story.append(Spacer(1, 0.2*inch))
        
        for i, entity in enumerate(type_entities, 1):
            # Entity name
            entity_name = entity.get('Name', 'Unknown')
            story.append(Paragraph(f"{i}. <b>{entity_name}</b>", subheading_style))
            
            # Entity details table
            details_data = [['Property', 'Value']]
            
            # Type
            details_data.append(['Type', entity.get('Type', 'N/A')])
            
            # Parameters
            params = entity.get('Params', [])
            if params:
                params_str = ', '.join(params)
                if len(params_str) > 60:
                    params_str = params_str[:60] + '...'
                details_data.append(['Parameters', params_str])
            else:
                details_data.append(['Parameters', 'None'])
            
            details_table = Table(details_data, colWidths=[1.5*inch, 4.5*inch])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFE5F1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#6B5B7B')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E8B4F0')),
            ]))
            
            story.append(details_table)
            story.append(Spacer(1, 0.1*inch))
            
            # Documentation
            docs = entity.get('Docs', 'No documentation found')
            story.append(Paragraph("<b>Documentation:</b>", body_style))
            
            # Clean and format documentation text
            docs_clean = docs.replace('<', '<').replace('>', '>')
            # Split long documentation into paragraphs
            doc_paragraphs = docs_clean.split('\n')
            for para in doc_paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), body_style))
            
            story.append(Spacer(1, 0.2*inch))
            
            # Add separator between entities
            if i < len(type_entities):
                story.append(Paragraph("─" * 80, body_style))
                story.append(Spacer(1, 0.1*inch))
        
        # Page break between types
        if entity_type != list(entities_by_type.keys())[-1]:
            story.append(PageBreak())
    
    # Add footer
    story.append(PageBreak())
    story.append(Spacer(1, 2*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#8B7B9B'),
        alignment=TA_CENTER
    )
    story.append(Paragraph("─" * 80, footer_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Generated by Lumos Doc Gen ✨", footer_style))
    story.append(Paragraph(f"<i>Total: {len(entities)} entities documented</i>", footer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# Initialize session state
if 'entities' not in st.session_state:
    st.session_state.entities = []
if 'view' not in st.session_state:
    st.session_state.view = 'home'
if 'codebase_data' not in st.session_state:
    st.session_state.codebase_data = None
if 'upload_mode' not in st.session_state:
    st.session_state.upload_mode = 'files'  # 'files' or 'folder'

# Upload mode selector
col1, col2 = st.columns([1, 4])
with col1:
    upload_mode = st.radio(
        "Upload Mode",
        options=['Files', 'Folder'],
        horizontal=True,
        label_visibility="collapsed" if st.session_state.view == 'results' else "visible"
    )
    st.session_state.upload_mode = upload_mode.lower()

with col2:
    if st.session_state.upload_mode == 'files':
        # File uploader (always visible but styled differently based on view)
        uploaded_files = st.file_uploader(
            "Upload your code files",
            type=['py', 'js', 'java', 'sql'],
            accept_multiple_files=True,
            label_visibility="collapsed" if st.session_state.view == 'results' else "visible"
        )
    else:
        # Folder path input
        folder_path = st.text_input(
            "Enter folder path to analyze",
            placeholder="e.g., C:/Users/YourName/Projects/MyProject or ./src",
            label_visibility="collapsed" if st.session_state.view == 'results' else "visible"
        )
        
        if folder_path and st.button("Analyze Folder", type="primary"):
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                with st.spinner('✨ Analyzing codebase...'):
                    st.session_state.codebase_data = ingest_codebase(folder_path)
                    st.session_state.view = 'results'
                    st.rerun()
            else:
                st.error("Invalid folder path. Please enter a valid directory path.")
        
        uploaded_files = None

# VIEW 1: HOME PAGE
if st.session_state.view == 'home' and not uploaded_files:
    # Logo
    st.markdown("""
    <div class="logo-container">
        <div class="logo-text">✨ Lumos</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Post-it Note
    st.markdown("""
    <div class="postit-note">
        <p><b>Hey there! 👋</b></p>
        <p>Upload your Python, JavaScript, Java, or SQL files and I'll magically extract all the documentation for you!</p>
        <p>✨ Get beautiful docs<br>
        🔍 Search with AI<br>
        📥 Export as PDF, MD, or CSV</p>
        <p style="text-align: right; margin-top: 1rem;"><i>~ Your friendly doc generator</i></p>
    </div>
    """, unsafe_allow_html=True)

# Process files when uploaded
if uploaded_files and (not st.session_state.entities or st.session_state.view == 'home'):
    with st.spinner('✨ Processing your files...'):
        st.session_state.entities = []
        
        for uploaded_file in uploaded_files:
            file_content = uploaded_file.read().decode('utf-8')
            
            if uploaded_file.name.endswith('.py'):
                extracted_entities = extract_python_docs(file_content)
                st.session_state.entities.extend(extracted_entities)
            elif uploaded_file.name.endswith('.js'):
                extracted_entities = extract_js_docs(file_content)
                st.session_state.entities.extend(extracted_entities)
            elif uploaded_file.name.endswith('.java'):
                extracted_entities = extract_java_docs(file_content)
                st.session_state.entities.extend(extracted_entities)
            elif uploaded_file.name.endswith('.sql'):
                extracted_entities = extract_sql_docs(file_content)
                st.session_state.entities.extend(extracted_entities)
        
        if st.session_state.entities:
            st.session_state.view = 'results'
            st.success(f"🎉 Successfully extracted **{len(st.session_state.entities)}** entities!")
            st.rerun()

# VIEW 2: RESULTS PAGE
if st.session_state.view == 'results' and (st.session_state.entities or st.session_state.codebase_data):
    # Determine which data to display
    if st.session_state.codebase_data:
        # Folder mode - use codebase data
        all_entities = []
        for lang_data in st.session_state.codebase_data.values():
            if isinstance(lang_data, dict) and 'entities' in lang_data:
                all_entities.extend(lang_data['entities'])
        display_entities = all_entities
    else:
        # File mode - use entities
        display_entities = st.session_state.entities
    
    # Time Saved Metric at the very top
    total_minutes, hours, time_str = calculate_time_saved(display_entities)
    
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0;">
        <div style="
            background: linear-gradient(135deg, #FFE5F1 0%, #E8D5FF 100%);
            padding: 2rem;
            border-radius: 20px;
            box-shadow:
                0 8px 32px rgba(232, 180, 240, 0.3),
                0 0 60px rgba(232, 180, 240, 0.15);
            display: inline-block;
            min-width: 300px;
        ">
            <div style="font-size: 0.9rem; color: #6B5B7B; font-weight: 600; margin-bottom: 0.5rem;">
                ⏱️ TIME SAVED READING CODE
            </div>
            <div style="
                font-size: 3rem;
                font-weight: 700;
                background: linear-gradient(135deg, #E8B4F0 0%, #A8D5FF 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            ">
                """ + time_str + """
            </div>
            <div style="font-size: 0.85rem; color: #8B7B9B;">
                vs. manually reading """ + str(len(display_entities)) + """ entities
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### Quick Actions")
    
    # Architecture Diagram Buttons at the top
    if GRAPHVIZ_AVAILABLE:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Entity Diagram", use_container_width=True, type="primary"):
                with st.spinner("Creating diagram..."):
                    try:
                        diagram_path = generate_simple_diagram(
                            display_entities,
                            'entity_diagram',
                            'png'
                        )
                        
                        if diagram_path and os.path.exists(diagram_path):
                            st.success("Diagram generated!")
                            st.image(diagram_path, caption="Entity Relationship Diagram", use_column_width=True)
                            
                            with open(diagram_path, 'rb') as f:
                                st.download_button(
                                    label="Download Diagram",
                                    data=f.read(),
                                    file_name="entity_diagram.png",
                                    mime="image/png",
                                    use_container_width=True
                                )
                        else:
                            st.error("Failed to generate diagram")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            if st.button("Generate Project Architecture", use_container_width=True, type="primary"):
                with st.spinner("Analyzing project..."):
                    try:
                        diagram_path = generate_architecture_diagram(
                            '.',
                            'project_architecture',
                            'png'
                        )
                        
                        if diagram_path and os.path.exists(diagram_path):
                            st.success("Architecture generated!")
                            st.image(diagram_path, caption="Project Architecture", use_column_width=True)
                            
                            with open(diagram_path, 'rb') as f:
                                st.download_button(
                                    label="Download Architecture",
                                    data=f.read(),
                                    file_name="project_architecture.png",
                                    mime="image/png",
                                    use_container_width=True
                                )
                        else:
                            st.error("Failed to generate architecture")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Search Bar (center aligned)
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        search_query = st.text_input(
            "Search your documentation",
            placeholder="Search by function name or description...",
            label_visibility="collapsed",
            key="main_search"
        )
        
        if search_query:
            with st.spinner("Searching..."):
                result = perform_search(search_query, display_entities)
                
                if result:
                    st.markdown(f"#### Top Match: `{result['Name']}`")
                    
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.metric("Similarity", f"{result['similarity_score']:.0%}")
                        st.markdown(f"**Type:** {result['Type']}")
                        st.markdown(f"**Params:** {', '.join(result['Params']) if result['Params'] else 'None'}")
                    
                    with col2:
                        st.markdown("**Documentation:**")
                        st.info(result['Docs'])
                    
                    st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Metrics
    st.markdown("### Documentation Overview")
    col1, col2, col3 = st.columns(3)
    
    types_count = {}
    for entity in display_entities:
        entity_type = entity['Type']
        types_count[entity_type] = types_count.get(entity_type, 0) + 1
    
    with col1:
        st.metric("Total Entities", len(display_entities))
    
    with col2:
        st.metric("Unique Types", len(types_count))
    
    with col3:
        documented = sum(1 for e in display_entities if e['Docs'] != "No documentation found")
        st.metric("Documented", f"{documented}/{len(display_entities)}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Display documentation based on mode
    if st.session_state.codebase_data:
        # FOLDER MODE: Show segregated by language and file
        st.markdown("### 📁 Documentation by Language & File")
        
        # Language order and icons
        lang_info = {
            'python': {'icon': '🐍', 'name': 'Python', 'color': '#E8D5FF'},
            'javascript': {'icon': '📜', 'name': 'JavaScript', 'color': '#FFE5F1'},
            'java': {'icon': '☕', 'name': 'Java', 'color': '#FFD4A3'},
            'sql': {'icon': '🗄️', 'name': 'SQL', 'color': '#D4FFE5'}
        }
        
        for lang, info in lang_info.items():
            lang_data = st.session_state.codebase_data.get(lang, {})
            entities = lang_data.get('entities', [])
            
            if entities:
                # Language header
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, {info['color']} 0%, #FEFBFF 100%);
                    padding: 1rem 1.5rem;
                    border-radius: 15px;
                    margin: 1.5rem 0 1rem 0;
                    border-left: 5px solid {info['color']};
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                ">
                    <h3 style="margin: 0; color: #6B5B7B;">
                        {info['icon']} {info['name']}
                        <span style="font-size: 0.9rem; font-weight: normal; color: #8B7B9B;">
                            ({len(entities)} entities from {len(set(e.get('source_file', '') for e in entities))} files)
                        </span>
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Group entities by source file
                files_dict = {}
                for entity in entities:
                    source_file = entity.get('source_file', 'Unknown')
                    if source_file not in files_dict:
                        files_dict[source_file] = []
                    files_dict[source_file].append(entity)
                
                # Display each file's entities
                for file_path, file_entities in sorted(files_dict.items()):
                    file_name = os.path.basename(file_path)
                    
                    with st.expander(f"📄 **{file_name}** ({len(file_entities)} entities)", expanded=False):
                        st.markdown(f"<small style='color: #8B7B9B;'>Path: `{file_path}`</small>", unsafe_allow_html=True)
                        
                        # Create DataFrame for this file
                        file_df = pd.DataFrame(file_entities)
                        
                        # Remove source_file column if it exists
                        if 'source_file' in file_df.columns:
                            file_df = file_df.drop(columns=['source_file'])
                        
                        st.dataframe(file_df, use_container_width=True, height=min(300, len(file_entities) * 35 + 50))
                        
                        # Show detailed view for each entity
                        st.markdown("#### Entity Details")
                        for idx, entity in enumerate(file_entities, 1):
                            with st.container():
                                st.markdown(f"""
                                <div style="
                                    background: #FEFBFF;
                                    padding: 1rem;
                                    border-radius: 10px;
                                    margin: 0.5rem 0;
                                    border-left: 3px solid {info['color']};
                                ">
                                    <h5 style="margin: 0 0 0.5rem 0; color: #6B5B7B;">
                                        {idx}. {entity.get('Name', 'Unknown')}
                                        <span style="
                                            background: {info['color']};
                                            padding: 0.2rem 0.5rem;
                                            border-radius: 5px;
                                            font-size: 0.75rem;
                                            margin-left: 0.5rem;
                                        ">{entity.get('Type', 'Unknown')}</span>
                                    </h5>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                col1, col2 = st.columns([1, 3])
                                with col1:
                                    params = entity.get('Params', [])
                                    st.markdown(f"**Parameters:** {len(params)}")
                                    if params:
                                        st.markdown(f"<small>{', '.join(params[:5])}{', ...' if len(params) > 5 else ''}</small>", unsafe_allow_html=True)
                                
                                with col2:
                                    st.markdown("**Documentation:**")
                                    docs = entity.get('Docs', 'No documentation found')
                                    st.info(docs)
                                
                                st.markdown("<hr style='margin: 0.5rem 0; border: none; border-top: 1px solid #E8E8E8;'>", unsafe_allow_html=True)
    else:
        # FILE MODE: Show simple DataFrame
        df = pd.DataFrame(display_entities)
        st.dataframe(df, use_container_width=True, height=400)

    # Export Section
    st.markdown("---")
    st.markdown("### Export Documentation")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        markdown_content = generate_markdown(display_entities)
        st.download_button(
            label="📝 Markdown",
            data=markdown_content,
            file_name="documentation.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with col2:
        csv_df = pd.DataFrame(display_entities)
        if 'source_file' in csv_df.columns:
            csv_df = csv_df.drop(columns=['source_file'])
        csv_content = csv_df.to_csv(index=False)
        st.download_button(
            label="📊 CSV",
            data=csv_content,
            file_name="documentation.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        if REPORTLAB_AVAILABLE:
            pdf_buffer = generate_pdf(display_entities)
            st.download_button(
                label="📄 PDF",
                data=pdf_buffer,
                file_name="documentation.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.button(
                label="PDF (Install reportlab)",
                disabled=True,
                use_container_width=True,
                help="Install reportlab: pip install reportlab"
            )
    
    with col4:
        if st.button("🌐 Interactive HTML", type="primary", use_container_width=True, help="Generate and open interactive HTML report"):
            with st.spinner("Generating HTML report..."):
                # Prepare data for HTML report
                processed_data = []
                
                if st.session_state.codebase_data:
                    # Folder mode: process all languages
                    for lang, lang_data in st.session_state.codebase_data.items():
                        entities = lang_data.get('entities', [])
                        
                        # Group by file
                        files_dict = {}
                        for entity in entities:
                            source_file = entity.get('source_file', 'Unknown')
                            if source_file not in files_dict:
                                files_dict[source_file] = []
                            files_dict[source_file].append(entity)
                        
                        # Convert to HTML report format
                        for file_path, file_entities in files_dict.items():
                            file_name = os.path.basename(file_path)
                            functions_list = []
                            
                            for entity in file_entities:
                                functions_list.append({
                                    'name': entity.get('Name', 'Unknown'),
                                    'params': entity.get('Params', []),
                                    'docstring': entity.get('Docs', 'No documentation found'),
                                    'usage_example': entity.get('Usage', f"{entity.get('Name', 'Unknown')}()"),
                                    'source_code': entity.get('Source', '# Source code not available'),
                                    'type': entity.get('Type', 'function')
                                })
                            
                            processed_data.append({
                                'file_name': file_name,
                                'file_path': file_path,
                                'language': lang,
                                'functions': functions_list
                            })
                else:
                    # File mode: single file
                    if st.session_state.entities:
                        # Get language from first entity or default to python
                        first_entity = st.session_state.entities[0]
                        lang = 'python'  # Default
                        
                        functions_list = []
                        for entity in st.session_state.entities:
                            functions_list.append({
                                'name': entity.get('Name', 'Unknown'),
                                'params': entity.get('Params', []),
                                'docstring': entity.get('Docs', 'No documentation found'),
                                'usage_example': entity.get('Usage', f"{entity.get('Name', 'Unknown')}()"),
                                'source_code': entity.get('Source', '# Source code not available'),
                                'type': entity.get('Type', 'function')
                            })
                        
                        processed_data.append({
                            'file_name': 'uploaded_file',
                            'file_path': 'uploaded_file',
                            'language': lang,
                            'functions': functions_list
                        })
                
                # Generate HTML report
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                html_filename = f"interactive_report_{timestamp}.html"
                
                try:
                    output_file = generate_html_report(processed_data, html_filename)
                    if output_file:
                        st.success(f"✅ HTML report generated: {html_filename}")
                        
                        # Provide download button
                        with open(output_file, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        
                        st.download_button(
                            label="⬇️ Download HTML Report",
                            data=html_content,
                            file_name=html_filename,
                            mime="text/html",
                            use_container_width=True
                        )
                        
                        # Try to open in browser
                        try:
                            import webbrowser
                            abs_path = os.path.abspath(output_file)
                            webbrowser.open(f'file://{abs_path}')
                            st.info("🌐 Opening report in your default browser...")
                        except Exception as e:
                            st.warning(f"Could not auto-open browser. Please open {html_filename} manually.")
                    else:
                        st.error("Failed to generate HTML report")
                except Exception as e:
                    st.error(f"Error generating HTML report: {str(e)}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #8B7B9B; padding: 2rem;">
        <p>Made with 💜 by Bob | Powered by Streamlit ✨</p>
    </div>
    """, unsafe_allow_html=True)

# Made with Bob
