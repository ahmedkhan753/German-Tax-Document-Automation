#!/usr/bin/env python3
"""Test document discovery with the fixed configuration"""
import sys
import os

# Add script directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'script'))

from document_processor import discover_files, CONFIG

input_dir = CONFIG['input_dir']
print(f"Scanning directory: {input_dir}\n")

found = discover_files(input_dir)

if found:
    print("=" * 60)
    print("DISCOVERY RESULTS:")
    print("=" * 60)
    for doc_type in CONFIG['merge_order']:
        if doc_type in found:
            print(f"\n{doc_type.upper()}:")
            for file_path in found[doc_type]:
                print(f"  ✓ {os.path.basename(file_path)}")
    
    print("\n" + "=" * 60)
    print("EXPECTED MERGE ORDER:")
    print("=" * 60)
    seq = 1
    for doc_type in CONFIG['merge_order']:
        if doc_type in found:
            print(f"  [{seq}] {doc_type}")
            seq += 1
else:
    print("NO FILES FOUND")
