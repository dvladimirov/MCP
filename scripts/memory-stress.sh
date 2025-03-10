#!/bin/sh

# Memory stress script for Prometheus alert testing
# This script allocates memory incrementally to trigger Prometheus alerts

echo "Memory stress container started"
echo "This container will incrementally increase memory usage to trigger alerts"

# Start with minimal memory usage
stress_level=0
max_stress=10
sleep_time=60

# Monitor and gradually increase memory usage
while true; do
    # Calculate VM workers based on stress level (each worker uses about 10% of available memory)
    vm_workers=$((stress_level))
    
    if [ $stress_level -lt $max_stress ]; then
        stress_level=$((stress_level + 1))
        echo "Increasing memory stress level to $stress_level / $max_stress"
    fi
    
    # Stop any existing stress process
    pkill stress-ng || true
    
    if [ $vm_workers -gt 0 ]; then
        echo "Running stress-ng with $vm_workers VM workers for $sleep_time seconds"
        # Run stress-ng with VM stressors to allocate memory
        stress-ng --vm $vm_workers --vm-bytes 10% --timeout ${sleep_time}s &
    else
        echo "Idle state, no memory stress"
        sleep $sleep_time
    fi
    
    # Report memory usage
    free -m
    
    # Exit if container receives signal
    if [ -f "/tmp/stop" ]; then
        echo "Stopping memory stress"
        pkill stress-ng || true
        exit 0
    fi
done 