#!/usr/bin/env python3
"""
Extract version from Python package files (setup.py, pyproject.toml, __init__.py)
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path


def extract_from_setup_py(file_path):
    """Extract version from setup.py"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Method 1: Look for version= in setup() call
    version_match = re.search(r'version\s*=\s*[\'\"](.*?)[\'\"]', content)
    if version_match:
        return version_match.group(1)
    
    # Method 2: Look for __version__ variable
    version_match = re.search(r'__version__\s*=\s*[\'\"](.*?)[\'\"]', content)
    if version_match:
        return version_match.group(1)
    
    # Method 3: Try AST parsing
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and hasattr(node.func, 'id') and node.func.id == 'setup':
                for keyword in node.keywords:
                    if keyword.arg == 'version':
                        if isinstance(keyword.value, ast.Str):
                            return keyword.value.s
                        elif isinstance(keyword.value, ast.Constant):
                            return str(keyword.value.value)
    except Exception:
        pass
    
    return None


def extract_from_pyproject_toml(file_path):
    """Extract version from pyproject.toml"""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            # Fallback to regex for basic cases
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            version_match = re.search(r'version\s*=\s*[\'\"](.*?)[\'\"]', content)
            return version_match.group(1) if version_match else None
    
    try:
        with open(file_path, 'rb') as f:
            data = tomllib.load(f)
        
        # Check different possible locations
        if 'project' in data and 'version' in data['project']:
            return data['project']['version']
        elif 'tool' in data and 'poetry' in data['tool'] and 'version' in data['tool']['poetry']:
            return data['tool']['poetry']['version']
        elif 'version' in data:
            return data['version']
    except Exception:
        pass
    
    return None


def extract_from_init_py(file_path):
    """Extract version from __init__.py"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for __version__ variable
    version_match = re.search(r'__version__\s*=\s*[\'\"](.*?)[\'\"]', content)
    if version_match:
        return version_match.group(1)
    
    return None


def find_version_files():
    """Find common version files in the current directory"""
    files_to_check = [
        'setup.py',
        'pyproject.toml',
        '__init__.py',
        'src/__init__.py',
    ]
    
    # Also check for package directories
    for item in os.listdir('.'):
        if os.path.isdir(item) and not item.startswith('.'):
            init_file = os.path.join(item, '__init__.py')
            if os.path.exists(init_file):
                files_to_check.append(init_file)
    
    return [f for f in files_to_check if os.path.exists(f)]


def extract_version(file_path='auto'):
    """Extract version from specified file or auto-detect"""
    if file_path == 'auto':
        files = find_version_files()
        if not files:
            return None
        
        # Try files in order of preference
        for file in ['setup.py', 'pyproject.toml'] + [f for f in files if f.endswith('__init__.py')]:
            if file in files:
                version = extract_version(file)
                if version:
                    return version
        return None
    
    if not os.path.exists(file_path):
        return None
    
    filename = os.path.basename(file_path)
    
    if filename == 'setup.py':
        return extract_from_setup_py(file_path)
    elif filename == 'pyproject.toml':
        return extract_from_pyproject_toml(file_path)
    elif filename == '__init__.py':
        return extract_from_init_py(file_path)
    else:
        # Try to detect based on content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'setup(' in content:
            return extract_from_setup_py(file_path)
        elif '[project]' in content or '[tool.poetry]' in content:
            return extract_from_pyproject_toml(file_path)
        else:
            return extract_from_init_py(file_path)


def parse_version_parts(version):
    """Parse version into major, minor, patch components"""
    if not version:
        return '0', '0', '0'
    
    # Remove v prefix if present
    clean_version = version.lstrip('v')
    
    # Extract numeric parts
    parts = re.findall(r'\d+', clean_version)
    
    major = parts[0] if len(parts) > 0 else '0'
    minor = parts[1] if len(parts) > 1 else '0'
    patch = parts[2] if len(parts) > 2 else '0'
    
    return major, minor, patch


def main():
    parser = argparse.ArgumentParser(description='Extract version from Python package files')
    parser.add_argument('--file-path', default='auto', help='Path to version file')
    parser.add_argument('--fallback-version', default='0.0.0', help='Fallback version')
    parser.add_argument('--output-file', help='GitHub Actions output file')
    
    args = parser.parse_args()
    
    version = extract_version(args.file_path)
    if not version:
        version = args.fallback_version
        print(f"Warning: No version found, using fallback: {version}", file=sys.stderr)
    
    tag = f"v{version}"
    major, minor, patch = parse_version_parts(version)
    
    print(f"Extracted version: {version}")
    print(f"Tag: {tag}")
    print(f"Parts: {major}.{minor}.{patch}")
    
    # Write to GitHub Actions output file if specified
    if args.output_file:
        with open(args.output_file, 'a', encoding='utf-8') as f:
            f.write(f"version={version}\n")
            f.write(f"tag={tag}\n")
            f.write(f"major={major}\n")
            f.write(f"minor={minor}\n")
            f.write(f"patch={patch}\n")


if __name__ == '__main__':
    main()