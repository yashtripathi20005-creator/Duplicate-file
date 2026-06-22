# filename: README.md

# Duplicate File Finder

A powerful command-line tool to find and manage duplicate files in your directory tree. Written in pure Python with no external dependencies.

## Features

- 🔍 Recursively scan directories for duplicate files
- 📊 Calculate SHA-256 hashes for accurate duplicate detection
- 💾 Show detailed information about duplicate groups
- 🗑️ Delete duplicates while keeping the oldest file
- 📋 Dry-run mode to preview deletions
- 🚀 Efficient chunk-based file reading
- 📦 No external dependencies - uses only Python standard library

## Installation

### Option 1: Direct download
```bash
# Download the script
wget https://raw.githubusercontent.com/yourusername/duplicate-finder/main/duplicate_finder.py

# Make it executable (Linux/Mac)
chmod +x duplicate_finder.py
