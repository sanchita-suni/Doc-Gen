"""
Architecture Map Generator
Generates UML-style diagrams showing project structure and dependencies using Graphviz.
"""

import os
import ast
import re
from pathlib import Path

# Try to import graphviz, but make it optional
try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False


def analyze_python_file(file_path):
    """
    Analyze a Python file to extract imports and class/function definitions.
    
    Args:
        file_path (str): Path to the Python file
        
    Returns:
        dict: Contains 'imports', 'classes', 'functions'
    """
    result = {
        'imports': [],
        'classes': [],
        'functions': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
            
        for node in ast.walk(tree):
            # Extract imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result['imports'].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result['imports'].append(node.module)
            
            # Extract classes
            elif isinstance(node, ast.ClassDef):
                result['classes'].append(node.name)
            
            # Extract top-level functions
            elif isinstance(node, ast.FunctionDef):
                result['functions'].append(node.name)
                
    except Exception as e:
        print(f"Error analyzing {file_path}: {str(e)}")
    
    return result


def analyze_javascript_file(file_path):
    """
    Analyze a JavaScript file to extract imports and function definitions.
    
    Args:
        file_path (str): Path to the JavaScript file
        
    Returns:
        dict: Contains 'imports', 'functions'
    """
    result = {
        'imports': [],
        'functions': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract imports (ES6 style)
        import_pattern = r'import\s+.*?\s+from\s+[\'"](.+?)[\'"]'
        imports = re.findall(import_pattern, content)
        result['imports'].extend(imports)
        
        # Extract require statements
        require_pattern = r'require\([\'"](.+?)[\'"]\)'
        requires = re.findall(require_pattern, content)
        result['imports'].extend(requires)
        
        # Extract function declarations
        func_pattern = r'function\s+(\w+)\s*\('
        functions = re.findall(func_pattern, content)
        result['functions'].extend(functions)
        
        # Extract arrow functions
        arrow_pattern = r'const\s+(\w+)\s*=\s*\(.*?\)\s*=>'
        arrow_funcs = re.findall(arrow_pattern, content)
        result['functions'].extend(arrow_funcs)
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {str(e)}")
    
    return result


def analyze_java_file(file_path):
    """
    Analyze a Java file to extract imports and class/method definitions.
    
    Args:
        file_path (str): Path to the Java file
        
    Returns:
        dict: Contains 'imports', 'classes', 'methods'
    """
    result = {
        'imports': [],
        'classes': [],
        'methods': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract imports
        import_pattern = r'import\s+([\w.]+);'
        imports = re.findall(import_pattern, content)
        result['imports'].extend(imports)
        
        # Extract class names
        class_pattern = r'(?:public|private|protected)?\s*class\s+(\w+)'
        classes = re.findall(class_pattern, content)
        result['classes'].extend(classes)
        
        # Extract method names
        method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?[\w\<\>\[\]]+\s+(\w+)\s*\('
        methods = re.findall(method_pattern, content)
        result['methods'].extend(methods)
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {str(e)}")
    
    return result


def analyze_sql_file(file_path):
    """
    Analyze a SQL file to extract table, procedure, function, and view definitions.
    
    Args:
        file_path (str): Path to the SQL file
        
    Returns:
        dict: Contains 'tables', 'procedures', 'functions', 'views'
    """
    result = {
        'tables': [],
        'procedures': [],
        'functions': [],
        'views': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract table names
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)'
        tables = re.findall(table_pattern, content, re.IGNORECASE)
        result['tables'].extend(tables)
        
        # Extract procedure names
        proc_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(\w+)'
        procedures = re.findall(proc_pattern, content, re.IGNORECASE)
        result['procedures'].extend(procedures)
        
        # Extract function names
        func_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)'
        functions = re.findall(func_pattern, content, re.IGNORECASE)
        result['functions'].extend(functions)
        
        # Extract view names
        view_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(\w+)'
        views = re.findall(view_pattern, content, re.IGNORECASE)
        result['views'].extend(views)
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {str(e)}")
    
    return result


def generate_architecture_diagram(project_path='.', output_file='architecture_diagram', output_format='png'):
    """
    Generate a UML-style architecture diagram for the project.
    
    Args:
        project_path (str): Path to the project directory
        output_file (str): Output file name (without extension)
        output_format (str): Output format ('png', 'svg', 'pdf')
        
    Returns:
        str: Path to the generated diagram file, or None if failed
    """
    if not GRAPHVIZ_AVAILABLE:
        print("Error: graphviz package not installed. Install with: pip install graphviz")
        return None
    
    try:
        # Create a new directed graph
        dot = graphviz.Digraph(
            name='Architecture',
            comment='Project Architecture Diagram',
            format=output_format,
            engine='dot'
        )
        
        # Set graph attributes for clean UML look
        dot.attr(rankdir='TB', splines='ortho', nodesep='0.5', ranksep='0.8')
        dot.attr('node', shape='box', style='filled', fillcolor='#F5F0FF', 
                 color='#E8B4F0', fontname='Arial', fontsize='10')
        dot.attr('edge', color='#A8D5FF', fontname='Arial', fontsize='9')
        
        # Analyze project files
        project_files = {}
        supported_extensions = {'.py', '.js', '.java', '.sql'}
        
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories and common non-source directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', 'env']]
            
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1]
                
                if ext in supported_extensions:
                    rel_path = os.path.relpath(file_path, project_path)
                    
                    if ext == '.py':
                        analysis = analyze_python_file(file_path)
                        project_files[rel_path] = {'type': 'Python', 'analysis': analysis}
                    elif ext == '.js':
                        analysis = analyze_javascript_file(file_path)
                        project_files[rel_path] = {'type': 'JavaScript', 'analysis': analysis}
                    elif ext == '.java':
                        analysis = analyze_java_file(file_path)
                        project_files[rel_path] = {'type': 'Java', 'analysis': analysis}
                    elif ext == '.sql':
                        analysis = analyze_sql_file(file_path)
                        project_files[rel_path] = {'type': 'SQL', 'analysis': analysis}
        
        # Add nodes for each file
        for file_path, file_info in project_files.items():
            file_name = os.path.basename(file_path)
            file_type = file_info['type']
            analysis = file_info['analysis']
            
            # Create label with file info
            label_parts = [f"{file_name}", f"{file_type}"]
            
            if file_type == 'Python':
                if analysis['classes']:
                    label_parts.append(f"Classes: {len(analysis['classes'])}")
                if analysis['functions']:
                    label_parts.append(f"Functions: {len(analysis['functions'])}")
            elif file_type == 'JavaScript':
                if analysis['functions']:
                    label_parts.append(f"Functions: {len(analysis['functions'])}")
            elif file_type == 'Java':
                if analysis['classes']:
                    label_parts.append(f"Classes: {len(analysis['classes'])}")
                if analysis['methods']:
                    label_parts.append(f"Methods: {len(analysis['methods'])}")
            elif file_type == 'SQL':
                if analysis['tables']:
                    label_parts.append(f"Tables: {len(analysis['tables'])}")
                if analysis['procedures']:
                    label_parts.append(f"Procedures: {len(analysis['procedures'])}")
            
            label = '\\n'.join(label_parts)
            
            # Set color based on file type
            colors = {
                'Python': '#E8D5FF',
                'JavaScript': '#FFE5F1',
                'Java': '#FFD4A3',
                'SQL': '#D4FFE5'
            }
            
            dot.node(file_path, label, fillcolor=colors.get(file_type, '#F5F0FF'))
        
        # Add edges for dependencies
        for file_path, file_info in project_files.items():
            analysis = file_info['analysis']
            imports = analysis.get('imports', [])
            
            for imp in imports:
                # Try to find matching files in the project
                for target_path in project_files.keys():
                    target_name = os.path.splitext(os.path.basename(target_path))[0]
                    
                    # Check if import matches target file
                    if imp == target_name or imp.endswith(target_name):
                        dot.edge(file_path, target_path, label='imports')
                        break
        
        # Render the diagram
        output_path = dot.render(output_file, cleanup=True)
        print(f"Architecture diagram generated: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating diagram: {str(e)}")
        return None


def generate_simple_diagram(entities, output_file='entity_diagram', output_format='png'):
    """
    Generate a simple diagram showing extracted entities and their relationships.
    
    Args:
        entities (list): List of entity dictionaries from parsers
        output_file (str): Output file name (without extension)
        output_format (str): Output format ('png', 'svg', 'pdf')
        
    Returns:
        str: Path to the generated diagram file, or None if failed
    """
    if not GRAPHVIZ_AVAILABLE:
        print("Error: graphviz package not installed. Install with: pip install graphviz")
        return None
    
    try:
        # Create a new directed graph
        dot = graphviz.Digraph(
            name='Entities',
            comment='Entity Relationship Diagram',
            format=output_format,
            engine='dot'
        )
        
        # Set graph attributes
        dot.attr(rankdir='LR', splines='ortho', nodesep='0.5', ranksep='1.0')
        dot.attr('node', shape='box', style='filled', fillcolor='#F5F0FF',
                 color='#E8B4F0', fontname='Arial', fontsize='10')
        dot.attr('edge', color='#A8D5FF', fontname='Arial', fontsize='9')
        
        # Group entities by type
        entity_types = {}
        for entity in entities:
            entity_type = entity.get('Type', 'Unknown')
            if entity_type not in entity_types:
                entity_types[entity_type] = []
            entity_types[entity_type].append(entity)
        
        # Add nodes for each entity type group
        for entity_type, type_entities in entity_types.items():
            with dot.subgraph(name=f'cluster_{entity_type}') as c:
                c.attr(label=f'{entity_type}s', style='filled', fillcolor='#FEFBFF',
                       color='#E8B4F0', fontsize='12')
                
                for entity in type_entities:
                    name = entity.get('Name', 'Unknown')
                    params = entity.get('Params', [])
                    
                    # Create label
                    label_parts = [f"{name}"]
                    if params:
                        label_parts.append(f"Params: {len(params)}")
                    
                    label = '\\n'.join(label_parts)
                    
                    # Set color based on type
                    colors = {
                        'Function': '#E8D5FF',
                        'Method': '#FFE5F1',
                        'Table': '#D4FFE5',
                        'Procedure': '#FFD4A3',
                        'View': '#A8FFD5'
                    }
                    
                    c.node(name, label, fillcolor=colors.get(entity_type, '#F5F0FF'))
        
        # Render the diagram
        output_path = dot.render(output_file, cleanup=True)
        print(f"Entity diagram generated: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"Error generating diagram: {str(e)}")
        return None


# Test function
if __name__ == "__main__":
    print("Testing architecture diagram generation...")
    
    if GRAPHVIZ_AVAILABLE:
        # Generate architecture diagram for current project
        result = generate_architecture_diagram('.', 'project_architecture', 'png')
        
        if result:
            print(f"Success! Diagram saved to: {result}")
        else:
            print("Failed to generate diagram")
    else:
        print("Graphviz not available. Install with: pip install graphviz")
        print("Also ensure Graphviz system package is installed:")
        print("  - Windows: Download from https://graphviz.org/download/")
        print("  - Mac: brew install graphviz")
        print("  - Linux: sudo apt-get install graphviz")

# Made with Bob