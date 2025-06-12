#!/usr/bin/env python3
"""
Script to remove all emojis from project files.
"""

import os
import re
import sys

def remove_emojis(text):
    """Remove emojis and other Unicode symbols from text."""
    # Pattern to match emojis and various Unicode symbols
    emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"  # dingbats
        u"\U000024C2-\U0001F251"  # enclosed characters
        u"\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        u"\U00002600-\U000026FF"  # miscellaneous symbols
        u"\U00002700-\U000027BF"  # dingbats
        u"\u2600-\u26FF"          # miscellaneous symbols
        u"\u2700-\u27BF"          # dingbats
        u"\u2300-\u23FF"          # miscellaneous technical
        u"\u2B50"                 # star
        u"\u2705"                 # check mark
        u"\u274C"                 # cross mark
        u"\u2714"                 # heavy check mark
        u"\u2716"                 # heavy multiplication x
        u"\u2717"                 # ballot x
        u"\u2718"                 # heavy ballot x
        u"\u2753"                 # question mark ornament
        u"\u2754"                 # white question mark ornament
        u"\u2755"                 # white exclamation mark ornament
        u"\u2795"                 # heavy plus sign
        u"\u2796"                 # heavy minus sign
        u"\u2797"                 # heavy division sign
        u"\u27A1"                 # black rightwards arrow
        u"\uFE0F"                 # variation selector
        "]+", 
        flags=re.UNICODE
    )
    
    # Also remove other common emoji-like characters
    text = emoji_pattern.sub('', text)
    
    # Remove some specific characters that might be missed
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('ℹ', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('', '')
    text = text.replace('•', '•')  # Keep bullet points
    
    return text

def process_file(filepath):
    """Process a single file to remove emojis."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_length = len(content)
        cleaned_content = remove_emojis(content)
        
        if content != cleaned_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            removed_chars = original_length - len(cleaned_content)
            print(f" Processed {filepath} (removed {removed_chars} characters)")
            return True
        else:
            return False
    except Exception as e:
        print(f" Error processing {filepath}: {e}")
        return False

def find_project_files():
    """Find all relevant project files."""
    extensions = {'.py', '.md', '.txt', '.yaml', '.yml', '.json', '.html', '.sh'}
    exclude_dirs = {'venv', '.git', '__pycache__', '.pytest_cache', 'node_modules'}
    
    files = []
    for root, dirs, filenames in os.walk('.'):
        # Remove excluded directories from dirs to prevent walking into them
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for filename in filenames:
            if any(filename.endswith(ext) for ext in extensions):
                filepath = os.path.join(root, filename)
                files.append(filepath)
    
    return files

def main():
    """Main function."""
    print("Emoji Removal Script")
    print("=" * 50)
    
    files = find_project_files()
    print(f"Found {len(files)} files to process")
    print()
    
    processed_count = 0
    for filepath in files:
        if process_file(filepath):
            processed_count += 1
    
    print()
    print("=" * 50)
    print(f"Processed {processed_count} files with emoji removal")
    print("Done!")

if __name__ == "__main__":
    main()
