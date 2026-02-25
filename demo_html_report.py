"""
Demonstration of the generate_html_report function.

This script shows how to use the generate_html_report function to create
an interactive HTML documentation file from processed code data.
"""

from app import generate_html_report, process_files

def demo_basic_usage():
    """
    Basic usage example: Generate HTML report from Python files.
    """
    print("=" * 60)
    print("Demo 1: Basic Usage - Single Python File")
    print("=" * 60)
    
    # Process a single Python file
    processed_data = process_files(['demo_python_utils.py'], 'python')
    
    # Generate HTML report
    output_file = generate_html_report(processed_data, 'report_python.html')
    print(f"[SUCCESS] Generated: {output_file}\n")


def demo_multiple_files():
    """
    Advanced usage: Generate HTML report from multiple files.
    """
    print("=" * 60)
    print("Demo 2: Multiple Files - Mixed Languages")
    print("=" * 60)
    
    # Process multiple files with different languages
    files_to_process = [
        ('demo_python_utils.py', 'python'),
        ('demo_javascript_api.js', 'javascript'),
        ('demo_java_service.java', 'java'),
    ]
    
    all_processed_data = []
    
    for file_path, language in files_to_process:
        try:
            processed = process_files([file_path], language)
            all_processed_data.extend(processed)
            print(f"[OK] Processed: {file_path} ({language})")
        except Exception as e:
            print(f"[FAIL] Error processing {file_path}: {e}")
    
    # Generate comprehensive HTML report
    output_file = generate_html_report(all_processed_data, 'report_comprehensive.html')
    print(f"\n[SUCCESS] Generated: {output_file}\n")


def demo_custom_output():
    """
    Custom output: Specify custom output file name and location.
    """
    print("=" * 60)
    print("Demo 3: Custom Output Location")
    print("=" * 60)
    
    # Process files
    processed_data = process_files(['demo_mixed_project.py'], 'python')
    
    # Generate with custom name
    custom_output = 'my_custom_documentation.html'
    output_file = generate_html_report(processed_data, custom_output)
    print(f"[SUCCESS] Generated: {output_file}\n")


def demo_data_structure():
    """
    Show the expected data structure for generate_html_report.
    """
    print("=" * 60)
    print("Demo 4: Expected Data Structure")
    print("=" * 60)
    
    # Example of the expected data structure
    example_data = [
        {
            'file_name': 'example.py',
            'file_path': '/path/to/example.py',
            'language': 'python',
            'functions': [
                {
                    'name': 'calculate_sum',
                    'params': ['a', 'b'],
                    'docstring': 'Calculate the sum of two numbers.',
                    'usage_example': 'result = calculate_sum(5, 3)',
                    'source_code': 'def calculate_sum(a, b):\n    return a + b',
                    'type': 'function'
                },
                {
                    'name': 'MyClass',
                    'params': [],
                    'docstring': 'A sample class for demonstration.',
                    'usage_example': 'obj = MyClass()',
                    'source_code': 'class MyClass:\n    pass',
                    'type': 'class'
                }
            ]
        }
    ]
    
    print("Expected data structure:")
    print("""
    [
        {
            'file_name': 'example.py',
            'file_path': '/path/to/example.py',
            'language': 'python',
            'functions': [
                {
                    'name': 'function_name',
                    'params': ['param1', 'param2'],
                    'docstring': 'Function description',
                    'usage_example': 'function_name(arg1, arg2)',
                    'source_code': 'def function_name(...):\\n    ...',
                    'type': 'function'
                }
            ]
        }
    ]
    """)
    
    # Generate report from example data
    output_file = generate_html_report(example_data, 'report_example.html')
    print(f"\n[SUCCESS] Generated example report: {output_file}\n")


def main():
    """
    Run all demonstrations.
    """
    print("\n" + "=" * 60)
    print("HTML REPORT GENERATOR - DEMONSTRATION")
    print("=" * 60 + "\n")
    
    try:
        # Run demos
        demo_basic_usage()
        demo_multiple_files()
        demo_custom_output()
        demo_data_structure()
        
        print("=" * 60)
        print("All demonstrations completed successfully!")
        print("=" * 60)
        print("\nGenerated HTML files:")
        print("  - report_python.html")
        print("  - report_comprehensive.html")
        print("  - my_custom_documentation.html")
        print("  - report_example.html")
        print("\nOpen any of these files in your web browser to view the")
        print("interactive documentation with split-screen layout.")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Error during demonstration: {e}\n")


if __name__ == "__main__":
    main()

# Made with Bob
