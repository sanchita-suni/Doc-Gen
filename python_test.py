"""
Utility functions for data processing and analysis.
This module provides various helper functions for common tasks.
"""

import math
from typing import List, Dict, Optional


def calculate_average(numbers: List[float]) -> float:
    """
    Calculate the average of a list of numbers.
    
    Args:
        numbers: A list of numeric values
        
    Returns:
        The arithmetic mean of the numbers
        
    Raises:
        ValueError: If the list is empty
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)


def find_maximum(data: List[int]) -> int:
    """
    Find the maximum value in a list.
    
    Args:
        data: List of integers to search
        
    Returns:
        The largest integer in the list
    """
    return max(data)


def filter_even_numbers(numbers: List[int]) -> List[int]:
    """
    Filter and return only even numbers from a list.
    
    Args:
        numbers: List of integers to filter
        
    Returns:
        A new list containing only even numbers
        
    Example:
        >>> filter_even_numbers([1, 2, 3, 4, 5, 6])
        [2, 4, 6]
    """
    return [num for num in numbers if num % 2 == 0]


def calculate_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        x1: X-coordinate of first point
        y1: Y-coordinate of first point
        x2: X-coordinate of second point
        y2: Y-coordinate of second point
        
    Returns:
        The Euclidean distance between the two points
    """
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def merge_dictionaries(dict1: Dict, dict2: Dict) -> Dict:
    """
    Merge two dictionaries into one.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        A new dictionary containing all key-value pairs from both inputs.
        If keys overlap, values from dict2 take precedence.
    """
    result = dict1.copy()
    result.update(dict2)
    return result


def validate_email(email: str) -> bool:
    """
    Validate if a string is a properly formatted email address.
    
    Args:
        email: String to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    return '@' in email and '.' in email.split('@')[1]


def chunk_list(data: List, chunk_size: int) -> List[List]:
    """
    Split a list into smaller chunks of specified size.
    
    Args:
        data: List to be chunked
        chunk_size: Size of each chunk
        
    Returns:
        List of lists, each containing chunk_size elements (last chunk may be smaller)
    """
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def count_occurrences(text: str, substring: str) -> int:
    """
    Count how many times a substring appears in text.
    
    Args:
        text: The text to search in
        substring: The substring to count
        
    Returns:
        Number of times substring appears in text
    """
    return text.count(substring)


def reverse_string(text: str) -> str:
    """
    Reverse a string.
    
    Args:
        text: String to reverse
        
    Returns:
        The reversed string
    """
    return text[::-1]


def is_palindrome(text: str) -> bool:
    """
    Check if a string is a palindrome (reads same forwards and backwards).
    
    Args:
        text: String to check
        
    Returns:
        True if text is a palindrome, False otherwise
    """
    cleaned = text.lower().replace(' ', '')
    return cleaned == cleaned[::-1]


class DataProcessor:
    """A class for processing and analyzing data."""
    
    def __init__(self, data: List[float]):
        """
        Initialize the DataProcessor with data.
        
        Args:
            data: List of numeric values to process
        """
        self.data = data
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Calculate basic statistics for the data.
        
        Returns:
            Dictionary containing mean, min, max, and count
        """
        return {
            'mean': sum(self.data) / len(self.data),
            'min': min(self.data),
            'max': max(self.data),
            'count': len(self.data)
        }
    
    def normalize(self) -> List[float]:
        """
        Normalize data to range [0, 1].
        
        Returns:
            List of normalized values
        """
        min_val = min(self.data)
        max_val = max(self.data)
        range_val = max_val - min_val
        return [(x - min_val) / range_val for x in self.data]

# Made with Bob
