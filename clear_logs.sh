#!/bin/bash

LOG_DIR="./log"

if [ -d "$LOG_DIR" ]; then
    file_count=$(ls -1 "$LOG_DIR" | wc -l)
    total_size=$(du -sh "$LOG_DIR" | cut -f1)
    
    echo "Found $file_count files, total size: $total_size"
    
    rm -f "$LOG_DIR"/*
    echo "Deleted $file_count files."
else
    echo "Log directory not found."
fi
