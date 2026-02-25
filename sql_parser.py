import re

def extract_sql_docs(source_code):
    """
    Extract documentation from SQL source code using regex patterns.
    
    Args:
        source_code (str): SQL source code as a string
        
    Returns:
        list: List of dictionaries containing SQL object information
    """
    entities = []
    
    try:
        # Remove multi-line comments for cleaner parsing
        # But keep them for documentation extraction
        
        # Pattern 1: CREATE TABLE statements
        # Matches: CREATE TABLE table_name (columns...)
        table_pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\((.*?)\);'
        table_matches = re.findall(table_pattern, source_code, re.IGNORECASE | re.DOTALL)
        
        for match in table_matches:
            table_name = match[0]
            columns_def = match[1]
            
            # Extract column names
            column_pattern = r'(\w+)\s+(?:VARCHAR|INT|INTEGER|DECIMAL|DATE|DATETIME|TEXT|BOOLEAN|FLOAT|DOUBLE|CHAR|BIGINT|SMALLINT|TIMESTAMP)'
            columns = re.findall(column_pattern, columns_def, re.IGNORECASE)
            
            # Look for comment immediately before CREATE TABLE
            # Find the position of this CREATE TABLE statement
            table_pos = source_code.find(f'CREATE TABLE {table_name}')
            if table_pos == -1:
                table_pos = source_code.upper().find(f'CREATE TABLE {table_name.upper()}')
            
            doc = "No documentation found"
            if table_pos > 0:
                # Look backwards for comment
                before_text = source_code[:table_pos].rstrip()
                
                # Check for single-line comment
                if before_text.endswith('\n') or before_text.endswith('\r\n'):
                    lines = before_text.split('\n')
                    if lines and lines[-1].strip().startswith('--'):
                        doc = lines[-1].strip()[2:].strip()
                
                # Check for multi-line comment
                multiline_match = re.search(r'/\*\s*(.*?)\s*\*/\s*$', before_text, re.DOTALL)
                if multiline_match:
                    doc = multiline_match.group(1).strip()
            
            entity = {
                "Name": table_name,
                "Type": "Table",
                "Params": columns,
                "Docs": doc
            }
            entities.append(entity)
        
        # Pattern 2: CREATE PROCEDURE statements
        # Matches: CREATE PROCEDURE proc_name (params)
        procedure_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+(\w+)\s*\((.*?)\)'
        procedure_matches = re.findall(procedure_pattern, source_code, re.IGNORECASE | re.DOTALL)
        
        for match in procedure_matches:
            proc_name = match[0]
            params_str = match[1]
            
            # Extract parameter names
            param_pattern = r'(?:IN|OUT|INOUT)?\s*(\w+)\s+(?:VARCHAR|INT|INTEGER|DECIMAL|DATE|DATETIME|TEXT|BOOLEAN|FLOAT|DOUBLE)'
            params = re.findall(param_pattern, params_str, re.IGNORECASE)
            
            # Look for comment immediately before CREATE PROCEDURE
            proc_search = f'CREATE PROCEDURE {proc_name}'
            proc_pos = source_code.upper().find(proc_search.upper())
            
            doc = "No documentation found"
            if proc_pos > 0:
                before_text = source_code[:proc_pos].rstrip()
                
                # Check for single-line comment
                lines = before_text.split('\n')
                if lines and lines[-1].strip().startswith('--'):
                    doc = lines[-1].strip()[2:].strip()
                
                # Check for multi-line comment
                multiline_match = re.search(r'/\*\s*(.*?)\s*\*/\s*$', before_text, re.DOTALL)
                if multiline_match:
                    doc = multiline_match.group(1).strip()
            
            entity = {
                "Name": proc_name,
                "Type": "Procedure",
                "Params": params,
                "Docs": doc
            }
            entities.append(entity)
        
        # Pattern 3: CREATE FUNCTION statements
        # Matches: CREATE FUNCTION func_name (params) RETURNS type
        function_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(\w+)\s*\((.*?)\)\s+RETURNS?\s+(\w+)'
        function_matches = re.findall(function_pattern, source_code, re.IGNORECASE | re.DOTALL)
        
        for match in function_matches:
            func_name = match[0]
            params_str = match[1]
            return_type = match[2]
            
            # Extract parameter names
            param_pattern = r'(\w+)\s+(?:VARCHAR|INT|INTEGER|DECIMAL|DATE|DATETIME|TEXT|BOOLEAN|FLOAT|DOUBLE)'
            params = re.findall(param_pattern, params_str, re.IGNORECASE)
            
            # Look for comment immediately before CREATE FUNCTION
            func_search = f'CREATE FUNCTION {func_name}'
            func_pos = source_code.upper().find(func_search.upper())
            
            doc = f"Returns: {return_type}"
            if func_pos > 0:
                before_text = source_code[:func_pos].rstrip()
                
                comment_text = None
                # Check for single-line comment
                lines = before_text.split('\n')
                if lines and lines[-1].strip().startswith('--'):
                    comment_text = lines[-1].strip()[2:].strip()
                
                # Check for multi-line comment
                multiline_match = re.search(r'/\*\s*(.*?)\s*\*/\s*$', before_text, re.DOTALL)
                if multiline_match:
                    comment_text = multiline_match.group(1).strip()
                
                if comment_text:
                    doc = f"{comment_text}\nReturns: {return_type}"
            
            entity = {
                "Name": func_name,
                "Type": "Function",
                "Params": params,
                "Docs": doc
            }
            entities.append(entity)
        
        # Pattern 4: CREATE VIEW statements
        # Matches: CREATE VIEW view_name AS SELECT...
        view_pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+(\w+)\s+AS\s+SELECT'
        view_matches = re.findall(view_pattern, source_code, re.IGNORECASE)
        
        for view_name in view_matches:
            # Look for comment immediately before CREATE VIEW
            view_search = f'CREATE VIEW {view_name}'
            view_pos = source_code.upper().find(view_search.upper())
            if view_pos == -1:
                view_search = f'CREATE OR REPLACE VIEW {view_name}'
                view_pos = source_code.upper().find(view_search.upper())
            
            doc = "No documentation found"
            if view_pos > 0:
                before_text = source_code[:view_pos].rstrip()
                
                # Check for single-line comment
                lines = before_text.split('\n')
                if lines and lines[-1].strip().startswith('--'):
                    doc = lines[-1].strip()[2:].strip()
                
                # Check for multi-line comment
                multiline_match = re.search(r'/\*\s*(.*?)\s*\*/\s*$', before_text, re.DOTALL)
                if multiline_match:
                    doc = multiline_match.group(1).strip()
            
            entity = {
                "Name": view_name,
                "Type": "View",
                "Params": [],
                "Docs": doc
            }
            entities.append(entity)
            
    except Exception as e:
        print(f"Error parsing SQL code: {str(e)}")
        return []
    
    return entities

# Made with Bob
