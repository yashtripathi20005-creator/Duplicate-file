# filename: duplicate_finder.py

"""
Duplicate File Finder
Find and manage duplicate files in a directory tree.
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional


class DuplicateFileFinder:
    """Main class for finding and managing duplicate files."""
    
    def __init__(self, root_dir: str, chunk_size: int = 8192):
        """
        Initialize the duplicate file finder.
        
        Args:
            root_dir: Root directory to scan
            chunk_size: Chunk size for reading files (default: 8KB)
        """
        self.root_dir = Path(root_dir)
        self.chunk_size = chunk_size
        self.file_groups: Dict[str, List[Path]] = defaultdict(list)
        self.duplicate_groups: Dict[str, List[Path]] = {}
        
    def scan(self) -> None:
        """Scan the directory and find duplicate files."""
        if not self.root_dir.exists():
            raise ValueError(f"Directory does not exist: {self.root_dir}")
        
        if not self.root_dir.is_dir():
            raise ValueError(f"Path is not a directory: {self.root_dir}")
        
        print(f"Scanning directory: {self.root_dir}")
        print("Building initial file index...")
        
        # First pass: index all files by size
        size_map: Dict[int, List[Path]] = defaultdict(list)
        
        for file_path in self.root_dir.rglob('*'):
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    size_map[size].append(file_path)
                except (OSError, PermissionError):
                    print(f"Warning: Could not access {file_path}", file=sys.stderr)
        
        print(f"Found {sum(len(files) for files in size_map.values())} files")
        print("Checking for duplicates...")
        
        # Second pass: compare files with the same size
        total_checked = 0
        for size, file_paths in size_map.items():
            if len(file_paths) < 2:
                continue
                
            # Group by hash for files with same size
            hash_groups: Dict[str, List[Path]] = defaultdict(list)
            
            for file_path in file_paths:
                total_checked += 1
                if total_checked % 1000 == 0:
                    print(f"Processed {total_checked} files...")
                
                try:
                    file_hash = self._get_file_hash(file_path)
                    hash_groups[file_hash].append(file_path)
                except (OSError, PermissionError):
                    print(f"Warning: Could not read {file_path}", file=sys.stderr)
            
            # Keep groups with more than one file (duplicates)
            for file_hash, duplicate_paths in hash_groups.items():
                if len(duplicate_paths) > 1:
                    self.duplicate_groups[file_hash] = duplicate_paths
                    self.file_groups[file_hash] = duplicate_paths
        
        print(f"Scan complete. Found {len(self.duplicate_groups)} duplicate groups")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hex digest of the file hash
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as file:
            while True:
                data = file.read(self.chunk_size)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()
    
    def get_duplicates(self) -> Dict[str, List[Path]]:
        """
        Get all duplicate file groups.
        
        Returns:
            Dictionary mapping file hashes to lists of duplicate file paths
        """
        return self.duplicate_groups
    
    def get_duplicate_count(self) -> int:
        """
        Get total number of duplicate files (excluding originals).
        
        Returns:
            Number of duplicate files
        """
        count = 0
        for paths in self.duplicate_groups.values():
            count += len(paths) - 1  # Keep one original
        return count
    
    def print_summary(self) -> None:
        """Print a summary of found duplicates."""
        if not self.duplicate_groups:
            print("\nNo duplicate files found.")
            return
        
        total_duplicates = self.get_duplicate_count()
        total_space_wasted = 0
        
        print(f"\n{'='*60}")
        print(f"DUPLICATE FILES SUMMARY")
        print(f"{'='*60}")
        print(f"Found {len(self.duplicate_groups)} groups of duplicate files")
        print(f"Total duplicate files: {total_duplicates}")
        
        # Calculate wasted space
        for file_hash, paths in self.duplicate_groups.items():
            try:
                file_size = paths[0].stat().st_size
                total_space_wasted += file_size * (len(paths) - 1)
            except (OSError, PermissionError):
                pass
        
        if total_space_wasted > 0:
            print(f"Total wasted space: {self._format_size(total_space_wasted)}")
        
        print(f"\n{'='*60}")
        print("DETAILED DUPLICATE GROUPS:")
        print(f"{'='*60}")
        
        for idx, (file_hash, paths) in enumerate(self.duplicate_groups.items(), 1):
            print(f"\nGroup #{idx} (Hash: {file_hash[:16]}...):")
            print(f"  {len(paths)} duplicate files")
            try:
                size = paths[0].stat().st_size
                print(f"  Size per file: {self._format_size(size)}")
                print(f"  Total wasted space: {self._format_size(size * (len(paths) - 1))}")
            except (OSError, PermissionError):
                pass
            
            print("  Files:")
            for i, file_path in enumerate(paths):
                marker = " (ORIGINAL)" if i == 0 else " (DUPLICATE)"
                print(f"    {i+1}. {file_path}{marker}")
    
    def delete_duplicates(self, keep_oldest: bool = True, dry_run: bool = True) -> None:
        """
        Delete duplicate files keeping only one copy.
        
        Args:
            keep_oldest: Keep the oldest file, otherwise keep the first found
            dry_run: If True, only show what would be deleted
        """
        if not self.duplicate_groups:
            print("No duplicates to delete.")
            return
        
        total_deleted = 0
        total_space_freed = 0
        
        print(f"\n{'='*60}")
        print(f"{'DRY RUN' if dry_run else 'DELETING'} DUPLICATE FILES")
        print(f"{'='*60}")
        
        for file_hash, paths in self.duplicate_groups.items():
            if len(paths) < 2:
                continue
            
            # Determine which file to keep
            if keep_oldest:
                # Keep the oldest file
                sorted_paths = sorted(paths, key=lambda p: p.stat().st_ctime)
                keep_file = sorted_paths[0]
                delete_files = sorted_paths[1:]
            else:
                # Keep the first file found
                keep_file = paths[0]
                delete_files = paths[1:]
            
            try:
                file_size = keep_file.stat().st_size
                total_space_freed += file_size * len(delete_files)
            except (OSError, PermissionError):
                pass
            
            print(f"\nHash: {file_hash[:16]}...")
            print(f"  Keeping: {keep_file}")
            for file_path in delete_files:
                print(f"  Deleting: {file_path}")
                
                if not dry_run:
                    try:
                        os.remove(file_path)
                        total_deleted += 1
                    except (OSError, PermissionError) as e:
                        print(f"    Error: {e}")
        
        if dry_run:
            print(f"\n{'='*60}")
            print(f"DRY RUN COMPLETE")
            print(f"Would delete {total_deleted} files")
            print(f"Would free approximately {self._format_size(total_space_freed)}")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"CLEANUP COMPLETE")
            print(f"Deleted {total_deleted} files")
            print(f"Freed approximately {self._format_size(total_space_freed)}")
            print(f"{'='*60}")
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Find and manage duplicate files in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/directory           # Find duplicates
  %(prog)s /path/to/directory --delete  # Delete duplicates (keeps oldest)
  %(prog)s /path/to/directory --delete --keep-first  # Keep first found
  %(prog)s /path/to/directory --delete --dry-run     # Preview deletion
        """
    )
    
    parser.add_argument(
        'directory',
        help='Root directory to scan for duplicates'
    )
    
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete duplicate files (keeps the oldest file by default)'
    )
    
    parser.add_argument(
        '--keep-first',
        action='store_true',
        help='When deleting, keep the first file found instead of the oldest'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=8192,
        help='Chunk size for file reading (default: 8192 bytes)'
    )
    
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Show only summary, not detailed list'
    )
    
    args = parser.parse_args()
    
    try:
        # Create finder and scan
        finder = DuplicateFileFinder(args.directory, args.chunk_size)
        finder.scan()
        
        # Show summary
        if args.summary_only:
            if finder.duplicate_groups:
                print(f"\nFound {len(finder.duplicate_groups)} duplicate groups")
                print(f"Total duplicates: {finder.get_duplicate_count()}")
        else:
            finder.print_summary()
        
        # Handle deletion if requested
        if args.delete:
            if args.dry_run:
                print("\nDRY RUN MODE - No files will be deleted")
            
            finder.delete_duplicates(
                keep_oldest=not args.keep_first,
                dry_run=args.dry_run
            )
        
    except KeyboardInterrupt:
        print("\n\nScan interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
