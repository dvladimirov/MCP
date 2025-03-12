#!/bin/bash
# Run memory analysis with OpenAI models

# Set environment variables for OpenAI models
export OPENAI_CHAT_MODEL="gpt-4o-mini"
export OPENAI_COMPLETION_MODEL="gpt-3.5-turbo-instruct"

echo "===== MCP Memory Analysis with OpenAI Models ====="
echo "Using chat model environment variable: $OPENAI_CHAT_MODEL"
echo "Using completion model environment variable: $OPENAI_COMPLETION_MODEL"

# Choose the analysis to run
echo ""
echo "Select analysis to run:"
echo "1) Basic Prometheus Test (test_prometheus.py)"
echo "2) AI Memory Diagnostics (ai_memory_diagnostics.py)"
echo "3) Memory Dashboard (mcp_memory_dashboard.py)"
echo "4) All of the above"
echo "5) List available AI models"
echo ""
read -p "Enter choice (1-5): " choice

case $choice in
    1)
        echo -e "\nRunning basic Prometheus test with AI recommendations..."
        uv run test_prometheus.py --quiet
        ;;
    2)
        echo -e "\nRunning AI Memory Diagnostics..."
        uv run ai_memory_diagnostics.py
        ;;
    3)
        echo -e "\nRunning Memory Dashboard..."
        uv run mcp_memory_dashboard.py
        ;;
    4)
        echo -e "\nRunning all analysis tools..."
        
        echo -e "\n1. Basic Prometheus test with AI recommendations"
        uv run test_prometheus.py --quiet
        
        echo -e "\n2. AI Memory Diagnostics"
        uv run ai_memory_diagnostics.py
        
        echo -e "\n3. Memory Dashboard"
        uv run mcp_memory_dashboard.py --once
        ;;
    5)
        echo -e "\nListing available AI models..."
        uv run ai_memory_diagnostics.py --list-models
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo -e "\nMemory analysis completed." 