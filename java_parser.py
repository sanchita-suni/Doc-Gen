import re

def extract_java_docs(source_code):
    """
    Extract documentation from Java source code using regex patterns.
    
    Args:
        source_code (str): Java source code as a string
        
    Returns:
        list: List of dictionaries containing method information
    """
    entities = []
    
    try:
        # Pattern to match JavaDoc comments followed by method declarations
        # Matches: /** ... */ followed by method signature
        javadoc_method_pattern = r'/\*\*\s*(.*?)\s*\*/\s*(?:public|private|protected|static|\s)+[\w\<\>\[\]]+\s+(\w+)\s*\((.*?)\)'
        
        # Find all JavaDoc + method combinations
        javadoc_matches = re.findall(javadoc_method_pattern, source_code, re.DOTALL)
        
        for match in javadoc_matches:
            javadoc = match[0]
            method_name = match[1]
            params_str = match[2]
            
            # Clean up JavaDoc (remove * at line starts)
            javadoc_clean = re.sub(r'^\s*\*\s?', '', javadoc, flags=re.MULTILINE).strip()
            
            # Parse parameters (type name pairs)
            params_list = []
            if params_str.strip():
                # Split by comma and extract parameter names
                param_parts = params_str.split(',')
                for param in param_parts:
                    param = param.strip()
                    if param:
                        # Extract parameter name (last word)
                        parts = param.split()
                        if parts:
                            params_list.append(parts[-1])
            
            entity = {
                "Name": method_name,
                "Type": "Method",
                "Params": params_list,
                "Docs": javadoc_clean if javadoc_clean else "No documentation found"
            }
            entities.append(entity)
        
        # Pattern for methods without JavaDoc
        # Matches: public/private/protected methods without preceding JavaDoc
        method_pattern = r'(?:public|private|protected)\s+(?:static\s+)?(?:final\s+)?[\w\<\>\[\]]+\s+(\w+)\s*\((.*?)\)\s*(?:throws\s+[\w\s,]+)?\s*\{'
        
        # Find all methods
        all_methods = re.finditer(method_pattern, source_code)
        
        # Track methods we've already added via JavaDoc
        existing_methods = {entity['Name'] for entity in entities}
        
        for match in all_methods:
            method_name = match.group(1)
            params_str = match.group(2)
            
            # Skip if already added with JavaDoc
            if method_name in existing_methods:
                continue
            
            # Parse parameters
            params_list = []
            if params_str.strip():
                param_parts = params_str.split(',')
                for param in param_parts:
                    param = param.strip()
                    if param:
                        parts = param.split()
                        if parts:
                            params_list.append(parts[-1])
            
            entity = {
                "Name": method_name,
                "Type": "Method",
                "Params": params_list,
                "Docs": "No documentation found"
            }
            entities.append(entity)
            
    except Exception as e:
        print(f"Error parsing Java code: {str(e)}")
        return []
    
    return entities

# Made with Bob
