# ✨ Lumos Doc Gen - Intelligent Documentation Generator

**Challenge 4: Intelligent Documentation Generator & Knowledge Base**

---

## 👥 Team Information

- **Team Members**: Tanisha Mathur & Sanchita Sunil
- **Team Number**: 24
- **Challenge**: Challenge 4 - Intelligent Documentation Generator & Knowledge Base

---

## 🎯 Challenge Requirements Met

### ✅ Base Requirements
1. **Parse 2+ Programming Languages**: Python, JavaScript, Java, SQL (4 languages)
2. **Extract Code Entities**: Functions, classes, methods, parameters, return types
3. **Generate 20+ Documentation Entities**: Handles unlimited entities
4. **Single Files & Directories**: Both supported
5. **Auto-Generate 5+ Usage Examples**: Generates for all functions
6. **Semantic Search**: Natural language search
7. **Export 2+ Formats**: Markdown, CSV, HTML, PDF (4 formats)

### ✅ Value-Added Feature
- **Natural Language Query Search**: Search using plain English instead of just keywords
  - Example: "find functions that calculate totals" instead of just "calculate"

---

## 📝 Solution Summary

Lumos Doc Gen is a web-based documentation generator built with Streamlit that automatically extracts and documents code from Python, JavaScript, Java, and SQL files. It uses semantic search to find functions using natural language queries and exports documentation in multiple formats.

**Key Features:**
- Multi-language code parsing (Python, JavaScript, Java, SQL)
- Semantic search with natural language understanding
- Auto-generated usage examples for all functions
- Interactive HTML reports with syntax highlighting
- Architecture diagrams (UML-style)
- Modern, accessible UI

---

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Graphviz (for diagrams)
# Windows: Download from https://graphviz.org/download/
# Mac: brew install graphviz
# Linux: sudo apt-get install graphviz
```

### Run the Application

```bash
streamlit run app.py
```

Open browser at `http://localhost:8501`

---

## 📂 Project Structure

```
Lumos/
├── app.py                    # Main application (Streamlit UI + parsers)
├── java_parser.py           # Java code parser
├── sql_parser.py            # SQL code parser
├── architecture_map.py      # Diagram generator
├── requirements.txt         # Python dependencies
├── .streamlit/config.toml   # UI theme configuration
├── python_test.py           # Python test file
├── javascript_test.js       # JavaScript test file
├── java_test.java          # Java test file
├── sql_test.sql            # SQL test file
└── README.md               # This file
```

---

## 💻 Key Code Snippets

### 1. Python Function Parser (AST-based (Abstract Syntax Tree))

```python
# Extract Python functions using Abstract Syntax Tree
def extract_function_metadata(source_code, language='python'):
    """Parse Python code and extract function details."""
    
    # Parse the source code into an AST (Abstract Syntax Tree)
    tree = ast.parse(source_code)
    
    # Walk through all nodes in the tree
    for node in ast.walk(tree):
        # Check if the node is a function definition
        if isinstance(node, ast.FunctionDef):
            # Get the function name
            func_name = node.name
            
            # Extract parameters from the function
            params = []
            for arg in node.args.args:
                param_name = arg.arg
                # Add type annotation if it exists (e.g., name: str)
                if arg.annotation:
                    param_name += f": {ast.unparse(arg.annotation)}"
                params.append(param_name)
            
            # Get the docstring (documentation inside the function)
            docstring = ast.get_docstring(node) or "No documentation available"
            
            # Extract the actual source code of the function
            start_line = node.lineno - 1  # Line where function starts
            end_line = node.end_lineno    # Line where function ends
            source_body = '\n'.join(lines[start_line:end_line])
            
            # Generate a usage example automatically
            usage_example = generate_usage_template(func_name, params, 'python')
```

**What this does:**
- Reads Python code and breaks it down into a tree structure
- Finds all function definitions
- Extracts function name, parameters, documentation, and source code
- Creates usage examples automatically

---

### 2. JavaScript Function Parser (Regex-based)

```python
# Extract JavaScript functions using regular expressions
elif language == 'javascript':
    # Pattern to match: function functionName(param1, param2) {
    func_pattern = r'function\s+(\w+)\s*\((.*?)\)\s*\{'
    
    # Find all matches in the source code
    matches = list(re.finditer(func_pattern, source_code))
    
    for match in matches:
        # Extract function name (group 1 from regex)
        func_name = match.group(1)
        
        # Extract parameters (group 2 from regex)
        params_str = match.group(2)
        # Split by comma and clean up spaces
        params = [p.strip() for p in params_str.split(',') if p.strip()]
        
        # Find JSDoc comment above the function (/** ... */)
        jsdoc_pattern = r'/\*\*(.*?)\*/'
        jsdoc_matches = list(re.finditer(jsdoc_pattern, before_func, re.DOTALL))
        
        # Use the last JSDoc comment found before the function
        if jsdoc_matches:
            docstring = jsdoc_matches[-1].group(1).strip()
```

**What this does:**
- Uses pattern matching to find JavaScript functions
- Extracts function names and parameters
- Looks for JSDoc comments (/** ... */) above functions
- Handles traditional function syntax

---

### 3. Semantic Search (Natural Language)

```python
# Load AI model for understanding natural language
@st.cache_resource
def load_model():
    """Load sentence transformer model for semantic search."""
    # This model converts text into numbers (embeddings)
    # Similar meanings = similar numbers
    return SentenceTransformer('all-MiniLM-L6-v2')

# Perform semantic search
def semantic_search(query, entities, model):
    """Search functions using natural language."""
    
    # Convert user's query into numbers (embedding)
    query_embedding = model.encode(query, convert_to_tensor=True)
    
    # Convert all function descriptions into numbers
    entity_texts = [
        f"{e['Name']} {e.get('Docs', '')} {' '.join(e.get('Params', []))}"
        for e in entities
    ]
    entity_embeddings = model.encode(entity_texts, convert_to_tensor=True)
    
    # Calculate similarity between query and each function
    # Higher score = better match
    similarities = util.cos_sim(query_embedding, entity_embeddings)[0]
    
    # Find the best matching function
    top_idx = similarities.argmax()
    top_score = similarities[top_idx].item()
    
    # Return the best match if similarity is high enough
    if top_score > 0.3:  # 30% similarity threshold
        return entities[top_idx], top_score
```

**What this does:**
- Converts text into numerical representations (embeddings)
- Compares user query with all function descriptions
- Finds the most similar function using cosine similarity
- Returns best match if similarity score is above threshold

---

### 4. Auto-Generate Usage Examples

```python
def generate_usage_template(func_name, params, language='python'):
    """Generate example code showing how to use a function."""
    
    if language == 'python':
        # Create parameter list with example values
        if params:
            # Use generic names like arg1, arg2 for parameters
            param_str = ', '.join([f'arg{i+1}' for i in range(len(params))])
            return f"result = {func_name}({param_str})"
        else:
            # No parameters needed
            return f"result = {func_name}()"
    
    elif language == 'javascript':
        if params:
            param_str = ', '.join([f'arg{i+1}' for i in range(len(params))])
            return f"const result = {func_name}({param_str});"
        else:
            return f"const result = {func_name}();"
```

**What this does:**
- Creates example code showing how to call each function
- Adapts to different programming languages
- Generates parameter placeholders (arg1, arg2, etc.)

---

### 5. Export to Multiple Formats

```python
# Export as Markdown
def generate_markdown(entities):
    """Create formatted Markdown documentation."""
    md = "# Code Documentation\n\n"
    
    for entity in entities:
        # Add function name as heading
        md += f"## {entity['Name']}\n\n"
        
        # Add parameters
        if entity.get('Params'):
            md += f"**Parameters:** {', '.join(entity['Params'])}\n\n"
        
        # Add documentation
        md += f"{entity.get('Docs', 'No documentation')}\n\n"
        
        # Add usage example
        md += f"**Usage:**\n```python\n{entity.get('Usage', '')}\n```\n\n"
    
    return md

# Export as CSV
csv_df = pd.DataFrame(entities)  # Convert to DataFrame
csv_content = csv_df.to_csv(index=False)  # Convert to CSV format

# Export as Interactive HTML (with syntax highlighting)
# See demo_html_report.py for full implementation
```

**What this does:**
- Converts extracted data into different file formats
- Markdown: Human-readable documentation
- CSV: Spreadsheet format for data analysis
- HTML: Interactive web page with syntax highlighting

---

## 🔍 How It Works

1. **Upload Files**: User uploads Python, JavaScript, Java, or SQL files
2. **Parse Code**: App extracts functions, classes, parameters, and documentation
3. **Generate Examples**: Auto-creates usage examples for each function
4. **Enable Search**: Model allows natural language queries
5. **Export**: User downloads documentation in preferred format

---

## 📊 Testing

Test files are included to demonstrate functionality:

```bash
# Test with provided sample files
# Upload python_test.py, javascript_test.js, java_test.java, or sql_test.sql
# in the Streamlit interface
```

Each test file contains 5+ functions with documentation to meet the 20+ entities requirement.

---

## 🎨 Additional Features

1. **SQL Support**: Parse database schemas, procedures, and functions
2. **Architecture Diagrams**: Visual UML-style diagrams of code structure
3. **Interactive HTML**: Beautiful reports with syntax highlighting
4. **Modern UI**: Accessible, responsive interface with pastel theme
5. **PDF Export**: Professional documentation (requires `pip install reportlab`)

**Benefits:**
- **Time Saving**: Automatic documentation generation
- **Better Understanding**: Visual diagrams and examples
- **Easy Sharing**: Multiple export formats(PDF/MD/CSV/HTML)
- **Professional Output**: Publication-ready documentation

---

## 🛠️ Technologies Used

- **Streamlit**: Web interface
- **AST (Abstract Syntax Tree)**: Python parsing
- **Regex**: JavaScript/Java parsing
- **Sentence Transformers**: AI semantic search
- **Graphviz**: Diagram generation
- **Pandas**: Data manipulation

---

