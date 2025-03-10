#!/usr/bin/env python3
"""
Script to simulate memory pressure for testing Prometheus alerts

This script allocates memory incrementally to simulate memory pressure
and trigger Prometheus memory alerts. Use with caution in production
environments as it can cause system instability if too much memory is allocated.

Usage:
  python simulate_memory_pressure.py [target_percentage] [duration_seconds]
  
  target_percentage: Target memory usage percentage (default: 85)
  duration_seconds: How long to maintain the pressure (default: 300 seconds/5 minutes)
"""

import os
import sys
import time
import psutil
import argparse

def get_memory_info():
    """Get current memory information"""
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "percent": memory.percent,
        "free": memory.free
    }

def print_memory_info(memory):
    """Print memory information in a readable format"""
    total_gb = memory["total"] / (1024 * 1024 * 1024)
    available_gb = memory["available"] / (1024 * 1024 * 1024)
    used_gb = memory["used"] / (1024 * 1024 * 1024)
    
    print(f"Memory total: {total_gb:.2f} GB")
    print(f"Memory used: {used_gb:.2f} GB ({memory['percent']}%)")
    print(f"Memory available: {available_gb:.2f} GB")

def allocate_memory(target_percent, duration_seconds):
    """Allocate memory to reach target percentage"""
    
    print("Starting memory allocation simulation")
    print("Initial memory state:")
    mem_info = get_memory_info()
    print_memory_info(mem_info)
    
    # Calculate how much memory we need to allocate to reach target
    total_bytes = mem_info["total"]
    current_used_bytes = mem_info["used"]
    target_used_bytes = (target_percent / 100) * total_bytes
    
    bytes_to_allocate = max(0, target_used_bytes - current_used_bytes)
    mb_to_allocate = bytes_to_allocate / (1024 * 1024)
    
    print(f"\nTarget memory usage: {target_percent}%")
    print(f"Need to allocate approximately: {mb_to_allocate:.2f} MB")
    
    if mb_to_allocate <= 0:
        print("Current memory usage already at or above target. Nothing to allocate.")
        return
    
    # Allocate memory in chunks to avoid sudden large allocations
    chunk_size = 10 * 1024 * 1024  # 10 MB chunks
    num_chunks = int(bytes_to_allocate / chunk_size) + 1
    
    memory_blocks = []
    allocated_mb = 0
    
    print("\nAllocating memory...")
    try:
        for i in range(num_chunks):
            if i % 5 == 0:  # Update progress every 5 chunks (50 MB)
                mem_info = get_memory_info()
                print(f"Current memory usage: {mem_info['percent']}% (allocated {allocated_mb:.2f} MB so far)")
                
                if mem_info['percent'] >= target_percent:
                    print(f"Reached target memory usage of {target_percent}%")
                    break
            
            # Allocate a chunk of memory
            memory_blocks.append(bytearray(chunk_size))
            allocated_mb += chunk_size / (1024 * 1024)
            
            # Small pause to give system time to update metrics
            time.sleep(0.1)
    
        # Final memory state
        print("\nMemory allocation complete. Current memory state:")
        mem_info = get_memory_info()
        print_memory_info(mem_info)
        
        # Hold the memory for the specified duration
        print(f"\nMaintaining memory pressure for {duration_seconds} seconds...")
        time.sleep(duration_seconds)
        
    except MemoryError:
        print("Memory allocation failed - system is out of memory")
    except KeyboardInterrupt:
        print("\nMemory allocation interrupted by user")
    finally:
        # Clean up by releasing memory
        print("\nReleasing allocated memory...")
        memory_blocks.clear()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        print("Final memory state:")
        mem_info = get_memory_info()
        print_memory_info(mem_info)
        
        print("Memory pressure simulation completed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate memory pressure for testing Prometheus alerts")
    parser.add_argument("--target", type=int, default=85, help="Target memory usage percentage (default: 85)")
    parser.add_argument("--duration", type=int, default=300, help="Duration to maintain pressure in seconds (default: 300)")
    
    args = parser.parse_args()
    
    if not os.geteuid() == 0:
        print("Warning: This script may need to be run as root to allocate significant memory")
    
    allocate_memory(args.target, args.duration) 