#!/usr/bin/env python3
"""
Test Anomaly Generator
Artificially creates system load anomalies for testing the Kubernetes anomaly detection
"""

import os
import sys
import time
import random
import argparse
import threading
import subprocess
import numpy as np
from datetime import datetime

def log(message):
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def cpu_stress(duration=60, cores=1):
    """Generate CPU stress for a specified duration"""
    log(f"Starting CPU stress test on {cores} cores for {duration} seconds")
    
    # Create a CPU-intensive calculation
    def stress_cpu():
        end_time = time.time() + duration
        while time.time() < end_time:
            # Generate CPU load with matrix operations
            size = 1000
            a = np.random.rand(size, size)
            b = np.random.rand(size, size)
            c = np.dot(a, b)
    
    # Start multiple threads based on core count
    threads = []
    for i in range(cores):
        t = threading.Thread(target=stress_cpu)
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    log("CPU stress test completed")

def memory_stress(duration=60, target_mb=1000):
    """Consume a specified amount of memory for a duration"""
    log(f"Starting memory stress test: allocating {target_mb}MB for {duration} seconds")
    
    # Allocate memory in chunks to avoid overwhelming the system
    memory_blocks = []
    chunk_size = 10  # MB per chunk
    chunks = target_mb // chunk_size
    
    try:
        for i in range(chunks):
            # Each allocation is roughly 1MB (actually 1024*1024 bytes)
            block = bytearray(chunk_size * 1024 * 1024)
            memory_blocks.append(block)
            # Fill with random data to ensure it's not optimized away
            for j in range(0, len(block), 4096):
                block[j] = random.randint(0, 255)
            
            if (i + 1) % 10 == 0:
                log(f"Allocated {(i+1) * chunk_size}MB of {target_mb}MB")
        
        log(f"Holding {target_mb}MB for {duration} seconds")
        time.sleep(duration)
    
    finally:
        # Explicitly delete blocks to release memory
        memory_blocks.clear()
        log("Memory released")

def disk_io_stress(duration=60, target_dir='.', file_size_mb=500):
    """Generate disk I/O by creating, writing, reading, and deleting files"""
    log(f"Starting disk I/O stress test for {duration} seconds in directory: {target_dir}")
    
    # Ensure target directory exists
    test_dir = os.path.join(target_dir, 'test_anomalies')
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a filename with timestamp to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(test_dir, f"disk_test_{timestamp}.dat")
    
    end_time = time.time() + duration
    bytes_written = 0
    bytes_read = 0
    
    try:
        while time.time() < end_time:
            # Write a large file
            log(f"Writing {file_size_mb}MB to disk...")
            with open(filename, 'wb') as f:
                # Write in 1MB chunks
                chunk = os.urandom(1024 * 1024)  # 1MB of random data
                for _ in range(file_size_mb):
                    f.write(chunk)
                    bytes_written += len(chunk)
            
            # Get file stats
            file_size = os.path.getsize(filename)
            log(f"Wrote {file_size_mb}MB file, actual size: {file_size/(1024*1024):.2f}MB")
            
            # Read back the file
            log("Reading file back from disk...")
            with open(filename, 'rb') as f:
                while True:
                    chunk = f.read(1024 * 1024)  # Read 1MB at a time
                    if not chunk:
                        break
                    bytes_read += len(chunk)
            
            # Delete the file
            log("Deleting file...")
            os.remove(filename)
            
            # Sleep briefly to avoid overwhelming the system
            time.sleep(1)
    
    finally:
        # Clean up if file still exists
        if os.path.exists(filename):
            os.remove(filename)
        
        log(f"Disk I/O test completed. Wrote {bytes_written/(1024*1024):.2f}MB, read {bytes_read/(1024*1024):.2f}MB")

def network_stress(duration=60, target='localhost', port=8080, bandwidth_mbps=50):
    """Generate network traffic using iperf3 or curl if available"""
    log(f"Starting network stress test to {target}:{port} for {duration} seconds")
    
    # Check if iperf3 is available
    iperf_available = subprocess.run(['which', 'iperf3'], stdout=subprocess.PIPE).returncode == 0
    
    if iperf_available:
        # Use iperf3 for precise bandwidth control
        log("Using iperf3 for network stress test")
        try:
            # Try to start an iperf3 server in the background
            server_proc = subprocess.Popen(['iperf3', '-s'], 
                                          stdout=subprocess.DEVNULL, 
                                          stderr=subprocess.DEVNULL)
            
            # Give the server a moment to start
            time.sleep(1)
            
            # Run the client with the specified bandwidth
            cmd = ['iperf3', '-c', 'localhost', '-t', str(duration), 
                   '-b', f'{bandwidth_mbps}M', '-R']
            
            log(f"Running: {' '.join(cmd)}")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if proc.returncode == 0:
                log(f"Network test completed successfully")
                result_lines = proc.stdout.splitlines()
                for line in result_lines[-5:]:  # Show the last few lines of output
                    if 'receiver' in line or 'sender' in line:
                        log(f"iperf3 result: {line.strip()}")
            else:
                log(f"Network test failed with error: {proc.stderr}")
            
            # Stop the server
            server_proc.terminate()
            
        except Exception as e:
            log(f"Error during iperf3 test: {e}")
            if 'server_proc' in locals():
                server_proc.terminate()
    else:
        # Fallback to HTTP requests
        log("iperf3 not available, using HTTP requests instead")
        
        # Generate repeated HTTP requests to the target
        bytes_transferred = 0
        start_time = time.time()
        end_time = start_time + duration
        
        while time.time() < end_time:
            try:
                # Generate a random 1MB payload
                data = os.urandom(1024 * 1024)
                
                # Use curl to POST the data
                cmd = ['curl', '-s', '-X', 'POST', 
                       '-H', 'Content-Type: application/octet-stream',
                       '--data-binary', '@-',
                       f'http://{target}:{port}/']
                
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
                
                proc.stdin.write(data)
                proc.stdin.close()
                proc.wait()
                
                bytes_transferred += len(data)
                
                # Calculate current rate
                elapsed = time.time() - start_time
                rate_mbps = (bytes_transferred / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                
                # Adjust sleep time to try to match target bandwidth
                if rate_mbps > bandwidth_mbps and elapsed > 1:
                    sleep_time = 0.1  # Sleep briefly to reduce rate
                    time.sleep(sleep_time)
                
            except Exception as e:
                log(f"Error during HTTP request: {e}")
                time.sleep(1)
        
        # Calculate final statistics
        total_elapsed = time.time() - start_time
        total_mb = bytes_transferred / (1024 * 1024)
        final_rate_mbps = total_mb / total_elapsed if total_elapsed > 0 else 0
        
        log(f"Network test completed. Transferred {total_mb:.2f}MB at {final_rate_mbps:.2f}Mbps")

def run_all_stress_tests(duration=60):
    """Run all stress tests simultaneously"""
    log(f"Starting combined stress test for {duration} seconds")
    
    # Start all tests in parallel
    threads = []
    
    cpu_thread = threading.Thread(target=cpu_stress, args=(duration, 2))
    threads.append(cpu_thread)
    
    mem_thread = threading.Thread(target=memory_stress, args=(duration, 500))
    threads.append(mem_thread)
    
    disk_thread = threading.Thread(target=disk_io_stress, args=(duration, '.', 200))
    threads.append(disk_thread)
    
    net_thread = threading.Thread(target=network_stress, args=(duration, 'localhost', 8080, 20))
    threads.append(net_thread)
    
    # Start all threads
    for t in threads:
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    log("Combined stress test completed")

def create_docker_anomalies(duration=60):
    """Create anomalies in Docker containers"""
    log(f"Attempting to create anomalies in Docker containers for {duration} seconds")
    
    try:
        # Check if Docker is available
        docker_check = subprocess.run(['docker', 'ps'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if docker_check.returncode != 0:
            log("Docker is not available. Cannot create container anomalies.")
            return
        
        # Find the memory-stress container
        find_cmd = ['docker', 'ps', '-q', '--filter', 'name=memory-stress']
        container_id = subprocess.check_output(find_cmd).decode().strip()
        
        if not container_id:
            log("memory-stress container not found. Starting it...")
            start_cmd = ['docker', 'compose', 'up', '-d', 'memory-stress']
            subprocess.run(start_cmd, check=True)
            time.sleep(2)
            container_id = subprocess.check_output(find_cmd).decode().strip()
        
        if container_id:
            log(f"Found memory-stress container: {container_id}")
            
            # Create stress in the container
            stress_cmd = ['docker', 'exec', container_id, 'stress', 
                          '--cpu', '2', '--vm', '1', '--vm-bytes', '200M', 
                          '--io', '1', '--timeout', f'{duration}s']
            
            log(f"Running: {' '.join(stress_cmd)}")
            subprocess.Popen(stress_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            log(f"Stress process started in container. Will run for {duration} seconds.")
        else:
            log("Could not find or start memory-stress container.")
    
    except Exception as e:
        log(f"Error creating Docker anomalies: {e}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Generate artificial anomalies for testing')
    parser.add_argument('--all', action='store_true', help='Run all stress tests')
    parser.add_argument('--cpu', action='store_true', help='Run CPU stress test')
    parser.add_argument('--memory', action='store_true', help='Run memory stress test')
    parser.add_argument('--disk', action='store_true', help='Run disk I/O stress test')
    parser.add_argument('--network', action='store_true', help='Run network stress test')
    parser.add_argument('--docker', action='store_true', help='Create anomalies in Docker containers')
    parser.add_argument('--duration', type=int, default=60, help='Duration of stress tests in seconds')
    parser.add_argument('--cpu-cores', type=int, default=2, help='Number of CPU cores to stress')
    parser.add_argument('--memory-mb', type=int, default=500, help='Amount of memory to allocate in MB')
    parser.add_argument('--disk-mb', type=int, default=200, help='Size of disk test file in MB')
    parser.add_argument('--network-mbps', type=int, default=20, help='Target network bandwidth in Mbps')
    
    return parser.parse_args()

def main():
    """Main function to run the anomaly generator"""
    args = parse_arguments()
    
    log("=== Test Anomaly Generator ===")
    log(f"Duration: {args.duration} seconds")
    
    if args.all:
        log("Running all stress tests")
        run_all_stress_tests(args.duration)
    else:
        if args.cpu:
            log(f"Running CPU stress test with {args.cpu_cores} cores")
            cpu_stress(args.duration, args.cpu_cores)
        
        if args.memory:
            log(f"Running memory stress test with {args.memory_mb}MB")
            memory_stress(args.duration, args.memory_mb)
        
        if args.disk:
            log(f"Running disk I/O stress test with {args.disk_mb}MB file")
            disk_io_stress(args.duration, '.', args.disk_mb)
        
        if args.network:
            log(f"Running network stress test at {args.network_mbps}Mbps")
            network_stress(args.duration, 'localhost', 8080, args.network_mbps)
    
    if args.docker:
        log("Creating anomalies in Docker containers")
        create_docker_anomalies(args.duration)
    
    log("All requested tests completed")

if __name__ == "__main__":
    main() 