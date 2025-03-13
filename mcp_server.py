import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import openai
from typing import List, Dict, Any, Optional, Union
from mcp.server import MCPServer
from mcp.model import ModelInfo, ModelCapability
from mcp.git_service import GitService
from mcp.filesystem_service import FilesystemService
from mcp.prometheus_service import PrometheusService
from datetime import datetime

# Initialize FastAPI app
app = FastAPI(title="MCP AI Server")

# Configure Azure OpenAI client
def get_azure_client():
    client = openai.AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    return client

# Configure standard OpenAI client
def get_openai_client():
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )
    return client

# Define the Azure OpenAI deployment to use
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")  # Default to more accessible model
OPENAI_COMPLETION_MODEL = os.getenv("OPENAI_COMPLETION_MODEL", "gpt-3.5-turbo-instruct")  # For completions

# Create MCP server instance
mcp_server = MCPServer()

# Create services
filesystem_service = FilesystemService()
prometheus_service = PrometheusService(os.getenv("PROMETHEUS_URL", "http://localhost:9090"))

# Define model info for Azure OpenAI
azure_gpt_model = ModelInfo(
    id="azure-gpt-4",
    name="Azure GPT-4",
    description="Azure OpenAI GPT-4 model accessed through MCP",
    capabilities=[
        ModelCapability.COMPLETION,
        ModelCapability.CHAT
    ],
    context_length=8192,
    pricing={
        "input_token_price": 0.03,  # Example pricing - update with actual pricing
        "output_token_price": 0.06,  # Example pricing - update with actual pricing
    }
)

# Define model info for standard OpenAI Chat
openai_gpt_chat_model = ModelInfo(
    id="openai-gpt-chat",
    name=f"OpenAI {OPENAI_CHAT_MODEL}",
    description=f"Standard OpenAI {OPENAI_CHAT_MODEL} chat model accessed through MCP",
    capabilities=[
        ModelCapability.CHAT
    ],
    context_length=8192,
    pricing={
        "input_token_price": 0.01,  # Example pricing - update with actual pricing
        "output_token_price": 0.03,  # Example pricing - update with actual pricing
    }
)

# Define model info for standard OpenAI Completion
openai_gpt_completion_model = ModelInfo(
    id="openai-gpt-completion",
    name=f"OpenAI {OPENAI_COMPLETION_MODEL}",
    description=f"Standard OpenAI {OPENAI_COMPLETION_MODEL} completion model accessed through MCP",
    capabilities=[
        ModelCapability.COMPLETION
    ],
    context_length=4096,
    pricing={
        "input_token_price": 0.0015,  # Example pricing - update with actual pricing
        "output_token_price": 0.002,  # Example pricing - update with actual pricing
    }
)

# Define model info for Git service
git_model = ModelInfo(
    id="git-analyzer",
    name="Git Repository Analyzer",
    description="Analyzes Git repositories through MCP",
    capabilities=[
        ModelCapability.GIT
    ],
    context_length=0,  # Not applicable for Git operations
    pricing={},  # No pricing for Git operations
    metadata={
        "supports_analyze": True,
        "supports_search": True
    }
)

# Define model info for Filesystem service
filesystem_model = ModelInfo(
    id="filesystem",
    name="Filesystem Access",
    description="Access to the local filesystem through MCP",
    capabilities=[
        ModelCapability.FILESYSTEM
    ],
    context_length=0,  # Not applicable for filesystem operations
    pricing={},  # No pricing for filesystem operations
    metadata={
        "supports_list": True,
        "supports_read": True,
        "supports_write": True,
        "supports_search": True
    }
)

# Define model info for Prometheus service
prometheus_model = ModelInfo(
    id="prometheus",
    name="Prometheus Metrics",
    description="Access to Prometheus metrics through MCP",
    capabilities=[
        ModelCapability.PROMETHEUS
    ],
    context_length=0,  # Not applicable for Prometheus operations
    pricing={},  # No pricing for Prometheus operations
    metadata={
        "supports_query": True,
        "supports_query_range": True,
        "supports_series": True,
        "supports_labels": True,
        "supports_targets": True,
        "supports_rules": True,
        "supports_alerts": True
    }
)

# Define model info for Git diff analyzer
git_diff_analyzer_model = ModelInfo(
    id="git-diff-analyzer",
    name="Git Diff Analyzer",
    description="Analyzes the differences between Git commits",
    capabilities=[
        ModelCapability.GIT
    ],
    context_length=0,  # Not applicable for Git operations
    pricing={},  # No pricing for Git operations
    metadata={
        "supports_analyze": True,
        "supports_diff": True
    }
)

# Register models with MCP server
mcp_server.register_model(azure_gpt_model)
mcp_server.register_model(openai_gpt_chat_model)
mcp_server.register_model(openai_gpt_completion_model)
mcp_server.register_model(git_model)
mcp_server.register_model(git_diff_analyzer_model)  # Register the Git diff analyzer model
mcp_server.register_model(filesystem_model)
mcp_server.register_model(prometheus_model)

# Define request models
class Message(BaseModel):
    role: str
    content: str

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 100
    temperature: Optional[float] = 0.7

class ChatRequest(BaseModel):
    messages: List[Message]
    max_tokens: Optional[int] = 100
    temperature: Optional[float] = 0.7

# Define Git request models
class GitAnalyzeRequest(BaseModel):
    repo_url: str

class GitSearchRequest(BaseModel):
    repo_url: str
    pattern: str

class GitDiffRequest(BaseModel):
    repo_url: str

class GitDiffAnalysisRequest(BaseModel):
    repo_url: str
    commit_sha: str
    target_commit: Optional[str] = 'HEAD'

# Add the new Requirements Analysis request model
class RequirementsAnalysisRequest(BaseModel):
    repo_url: str
    commit_sha: str
    target_commit: Optional[str] = 'HEAD'

# Define Filesystem request models
class ListDirectoryRequest(BaseModel):
    path: str = "."  # Default to current directory

class ReadFileRequest(BaseModel):
    path: str

class ReadFilesRequest(BaseModel):
    paths: List[str]

class WriteFileRequest(BaseModel):
    path: str
    content: str

class EditFileRequest(BaseModel):
    path: str
    edits: List[Dict[str, str]]
    dry_run: bool = False

class CreateDirectoryRequest(BaseModel):
    path: str

class MoveFileRequest(BaseModel):
    source: str
    destination: str

class SearchFilesRequest(BaseModel):
    path: str = "."  # Default to current directory
    pattern: str
    exclude_patterns: Optional[List[str]] = None

class FileInfoRequest(BaseModel):
    path: str

# Define Prometheus request models
class PrometheusQueryRequest(BaseModel):
    query: str
    time: Optional[str] = None

class PrometheusQueryRangeRequest(BaseModel):
    query: str
    start: str
    end: str
    step: str

class PrometheusSeriesRequest(BaseModel):
    match: List[str]
    start: Optional[str] = None
    end: Optional[str] = None

class PrometheusLabelValuesRequest(BaseModel):
    label_name: str

# Implement Azure completion endpoint
@app.post("/v1/models/azure-gpt-4/completion")
async def azure_completion(request: CompletionRequest):
    try:
        client = get_azure_client()
        response = client.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        result = {
            "id": response.id,
            "created": response.created,
            "model": "azure-gpt-4",
            "choices": [
                {
                    "text": choice.text,
                    "index": choice.index,
                    "finish_reason": choice.finish_reason
                } for choice in response.choices
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Implement Azure chat endpoint
@app.post("/v1/models/azure-gpt-4/chat")
async def azure_chat(request: ChatRequest):
    try:
        client = get_azure_client()
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        result = {
            "id": response.id,
            "created": response.created,
            "model": "azure-gpt-4",
            "choices": [
                {
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content
                    },
                    "index": choice.index,
                    "finish_reason": choice.finish_reason
                } for choice in response.choices
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Implement OpenAI completion endpoint
@app.post("/v1/models/openai-gpt-completion/completion")
async def openai_completion(request: CompletionRequest):
    try:
        client = get_openai_client()
        
        # Use the completion API with a model that actually supports it
        response = client.completions.create(
            model=OPENAI_COMPLETION_MODEL,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        result = {
            "id": response.id,
            "created": response.created,
            "model": "openai-gpt-completion",
            "choices": [
                {
                    "text": choice.text,
                    "index": choice.index,
                    "finish_reason": choice.finish_reason
                } for choice in response.choices
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Implement OpenAI chat endpoint
@app.post("/v1/models/openai-gpt-chat/chat")
async def openai_chat(request: ChatRequest):
    try:
        client = get_openai_client()
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        response = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        result = {
            "id": response.id,
            "created": response.created,
            "model": "openai-gpt-chat",
            "choices": [
                {
                    "message": {
                        "role": choice.message.role,
                        "content": choice.message.content
                    },
                    "index": choice.index,
                    "finish_reason": choice.finish_reason
                } for choice in response.choices
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Implement Git analysis endpoint
@app.post("/v1/models/git-analyzer/analyze")
async def analyze_git_repo(request: GitAnalyzeRequest):
    try:
        result = GitService.analyze_repository(request.repo_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Implement Git search endpoint
@app.post("/v1/models/git-analyzer/search")
async def search_git_repo(request: GitSearchRequest):
    try:
        result = GitService.search_repository(request.repo_url, request.pattern)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Implement Git diff endpoint
@app.post("/v1/models/git-analyzer/diff")
async def get_git_diff(request: GitDiffRequest):
    """Get the diff of the last commit in a Git repository"""
    try:
        return GitService.get_last_commit_diff(request.repo_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Implement Filesystem endpoints
@app.post("/v1/models/filesystem/list")
async def list_directory(request: ListDirectoryRequest):
    try:
        result = filesystem_service.list_directory(request.path)
        return {"path": request.path, "entries": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/models/filesystem/read")
async def read_file(request: ReadFileRequest):
    try:
        content = filesystem_service.read_file(request.path)
        return {"path": request.path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/models/filesystem/read-multiple")
async def read_multiple_files(request: ReadFilesRequest):
    try:
        result = filesystem_service.read_multiple_files(request.paths)
        return {"results": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/models/filesystem/write")
async def write_file(request: WriteFileRequest):
    try:
        result = filesystem_service.write_file(request.path, request.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/models/filesystem/edit")
async def edit_file(request: EditFileRequest):
    try:
        result = filesystem_service.edit_file(request.path, request.edits, request.dry_run)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/models/filesystem/mkdir")
async def create_directory(request: CreateDirectoryRequest):
    try:
        result = filesystem_service.create_directory(request.path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/models/filesystem/move")
async def move_file(request: MoveFileRequest):
    try:
        result = filesystem_service.move_file(request.source, request.destination)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/models/filesystem/search")
async def search_files(request: SearchFilesRequest):
    try:
        result = filesystem_service.search_files(request.path, request.pattern, request.exclude_patterns)
        return {"path": request.path, "pattern": request.pattern, "matches": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/models/filesystem/info")
async def get_file_info(request: FileInfoRequest):
    try:
        result = filesystem_service.get_file_info(request.path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Implement Prometheus endpoints
@app.post("/v1/models/prometheus/query")
async def prometheus_query(request: PrometheusQueryRequest):
    """Query Prometheus for metrics"""
    result = prometheus_service.query(request.query, request.time)
    return result

@app.post("/v1/models/prometheus/query_range")
async def prometheus_query_range(request: PrometheusQueryRangeRequest):
    """Query Prometheus over a time range"""
    result = prometheus_service.query_range(
        request.query, 
        request.start, 
        request.end, 
        request.step
    )
    return result

@app.post("/v1/models/prometheus/series")
async def prometheus_series(request: PrometheusSeriesRequest):
    """Get series from Prometheus"""
    result = prometheus_service.get_series(
        request.match, 
        request.start, 
        request.end
    )
    return result

@app.get("/v1/models/prometheus/labels")
async def prometheus_labels():
    """Get all label names from Prometheus"""
    result = prometheus_service.get_labels()
    return result

@app.post("/v1/models/prometheus/label_values")
async def prometheus_label_values(request: PrometheusLabelValuesRequest):
    """Get values for a specific label from Prometheus"""
    result = prometheus_service.get_label_values(request.label_name)
    return result

@app.get("/v1/models/prometheus/targets")
async def prometheus_targets():
    """Get targets from Prometheus"""
    result = prometheus_service.get_targets()
    return result

@app.get("/v1/models/prometheus/rules")
async def prometheus_rules():
    """Get rules from Prometheus"""
    result = prometheus_service.get_rules()
    return result

@app.get("/v1/models/prometheus/alerts")
async def prometheus_alerts():
    """Get alerts from Prometheus"""
    result = prometheus_service.get_alerts()
    return result

# Implement Git diff analysis endpoint
@app.post("/v1/models/git-diff-analyzer/analyze")
async def analyze_git_diff(request: GitDiffAnalysisRequest):
    """Analyze the diff between two commits in a Git repository"""
    try:
        diff_result = GitService.get_commit_diff(
            request.repo_url, 
            request.commit_sha, 
            request.target_commit
        )
        
        # Add AI-generated insights if available
        diff_result["summary"] = f"Analyzed diff between {request.commit_sha[:7]} and {request.target_commit[:7] if request.target_commit != 'HEAD' else 'HEAD'}."
        diff_result["major_changes"] = [
            f"Changed {diff_result['total_files_changed']} files with {diff_result['total_additions']} additions and {diff_result['total_deletions']} deletions."
        ]
        diff_result["recommendations"] = [
            "Review all changes carefully before merging."
        ]
        
        return diff_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add the requirements analysis endpoint
@app.post("/v1/models/git-diff-analyzer/analyze-requirements")
async def analyze_requirements_changes(request: RequirementsAnalysisRequest):
    """Analyze changes in requirements.txt between two commits"""
    try:
        result = GitService.analyze_requirements_changes(
            request.repo_url,
            request.commit_sha,
            request.target_commit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/git/analyze_diff")
async def analyze_git_diff_v1(request: GitDiffAnalysisRequest):
    """API endpoint for analyzing the diff between two commits (v1 API)"""
    try:
        diff_result = GitService.get_commit_diff(
            request.repo_url, 
            request.commit_sha, 
            request.target_commit
        )
        
        # Add AI-generated insights if available
        diff_result["summary"] = f"Analyzed diff between {request.commit_sha[:7]} and {request.target_commit[:7] if request.target_commit != 'HEAD' else 'HEAD'}."
        diff_result["major_changes"] = [
            f"Changed {diff_result['total_files_changed']} files with {diff_result['total_additions']} additions and {diff_result['total_deletions']} deletions."
        ]
        diff_result["recommendations"] = [
            "Review all changes carefully before merging."
        ]
        
        return diff_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add the v1 requirements analysis endpoint
@app.post("/v1/git/analyze_requirements")
async def analyze_requirements_changes_v1(request: RequirementsAnalysisRequest):
    """API endpoint for analyzing changes in requirements.txt between two commits (v1 API)"""
    try:
        result = GitService.analyze_requirements_changes(
            request.repo_url,
            request.commit_sha,
            request.target_commit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Define the comprehensive analysis request model
class ComprehensiveAnalysisRequest(BaseModel):
    repo_url: str
    commit_sha: str
    target_commit: Optional[str] = 'HEAD'

# Add a comprehensive analysis endpoint that combines diff and requirements analysis
@app.post("/v1/git/analyze_comprehensive")
async def analyze_comprehensive_v1(request: ComprehensiveAnalysisRequest):
    """API endpoint for comprehensive analysis combining code diff and requirements changes"""
    try:
        # Get diff analysis with better error handling
        try:
            diff_result = GitService.get_commit_diff(
                request.repo_url, 
                request.commit_sha, 
                request.target_commit
            )
        except Exception as diff_error:
            print(f"Error during diff analysis: {diff_error}")
            # Create a default diff result structure with empty values
            diff_result = {
                "total_files_changed": 0,
                "total_additions": 0,
                "total_deletions": 0,
                "base_commit": {
                    "id": request.commit_sha,
                    "message": "Commit information not available",
                },
                "target_commit": {
                    "id": request.target_commit,
                    "message": "Commit information not available",
                },
                "error": str(diff_error)
            }
        
        # Get requirements analysis
        req_result = GitService.analyze_requirements_changes(
            request.repo_url,
            request.commit_sha,
            request.target_commit
        )
        
        # Combine the results
        comprehensive_result = {
            "status": "success",
            "repository": request.repo_url,
            "base_commit": request.commit_sha,
            "target_commit": request.target_commit,
            "diff_analysis": {
                "total_files_changed": diff_result.get("total_files_changed", 0),
                "total_additions": diff_result.get("total_additions", 0),
                "total_deletions": diff_result.get("total_deletions", 0),
                "base_commit": diff_result.get("base_commit", {}),
                "target_commit": diff_result.get("target_commit", {})
            },
            "requirements_analysis": {
                "status": req_result.get("status", "unknown"),
                "summary": req_result.get("summary", "No requirements changes detected."),
                "added_packages": req_result.get("added_packages", {}),
                "removed_packages": req_result.get("removed_packages", {}),
                "changed_packages": req_result.get("changed_packages", {})
            }
        }
        
        # Include the AI analysis if available
        if "ai_analysis" in req_result:
            comprehensive_result["ai_analysis"] = req_result["ai_analysis"]
        
        # Add a comprehensive summary
        comprehensive_result["summary"] = f"Analyzed changes between {request.commit_sha[:7]} and {request.target_commit[:7] if request.target_commit != 'HEAD' else 'HEAD'}: "
        
        # Add code diff information to the summary if available
        if not diff_result.get("error"):
            comprehensive_result["summary"] += f"Found {diff_result.get('total_files_changed', 0)} changed files with {diff_result.get('total_additions', 0)} additions and {diff_result.get('total_deletions', 0)} deletions. "
        else:
            comprehensive_result["summary"] += "Could not analyze code changes. "
        
        # Add requirements info to summary if available
        if req_result.get("status") == "success":
            comprehensive_result["summary"] += f"Requirements changes: {len(req_result.get('added_packages', {}))} added, {len(req_result.get('removed_packages', {}))} removed, and {len(req_result.get('changed_packages', {}))} changed dependencies."
        
        # Generate overall recommendations
        comprehensive_result["recommendations"] = []
        
        # Add code-related recommendations
        if diff_result.get("total_files_changed", 0) > 0 and not diff_result.get("error"):
            comprehensive_result["recommendations"].append(f"Review all {diff_result.get('total_files_changed', 0)} changed files before merging.")
        
        # Add requirements-related recommendations from the AI analysis
        if req_result.get("ai_analysis") and req_result["ai_analysis"].get("dependency_analysis"):
            ai_recs = req_result["ai_analysis"]["dependency_analysis"].get("recommendations", [])
            comprehensive_result["recommendations"].extend(ai_recs)
        
        # Add general recommendations if we have potential issues from requirements analysis
        if req_result.get("potential_issues"):
            if any(issue["severity"] == "high" for issue in req_result["potential_issues"]):
                comprehensive_result["recommendations"].append("Address the high-severity dependency issues before proceeding.")
            
            if any(issue["severity"] == "medium" for issue in req_result["potential_issues"]):
                comprehensive_result["recommendations"].append("Consider reviewing the medium-severity dependency issues.")
        
        # Add next steps
        comprehensive_result["next_steps"] = []
        
        # Suggest running tests if there are significant changes
        if diff_result.get("total_additions", 0) + diff_result.get("total_deletions", 0) > 20:
            comprehensive_result["next_steps"].append("Run comprehensive tests to verify functionality after these changes.")
        
        # Add dependency-specific next steps
        if req_result.get("status") == "success":
            # For high-risk dependency changes
            high_risk_deps = []
            if req_result.get("ai_analysis") and req_result["ai_analysis"].get("dependency_analysis"):
                high_risk_deps = req_result["ai_analysis"]["dependency_analysis"]["risk_assessment"].get("high_risk", [])
            
            if high_risk_deps:
                comprehensive_result["next_steps"].append(f"Prioritize testing of features that depend on: {', '.join(pkg['package'] for pkg in high_risk_deps)}")
            
            # For added dependencies
            if req_result.get("added_packages"):
                comprehensive_result["next_steps"].append(f"Ensure all new dependencies are properly documented and compatible with your environment.")
            
            # For removed dependencies
            if req_result.get("removed_packages"):
                comprehensive_result["next_steps"].append(f"Verify that functionality previously provided by removed dependencies is either no longer needed or has been reimplemented.")
        
        return comprehensive_result
    except Exception as e:
        error_detail = str(e)
        print(f"Error in comprehensive analysis: {error_detail}")
        return {
            "status": "error",
            "message": f"Error processing comprehensive analysis: {error_detail}",
            "repository": request.repo_url,
            "base_commit": request.commit_sha,
            "target_commit": request.target_commit
        }

# Fix the Git analyze endpoint by adding a correct mapping to the proper model
@app.post("/v1/git/analyze")
async def analyze_git_repo_v1(request: GitAnalyzeRequest):
    """API endpoint for analyzing a Git repository (v1 API)"""
    try:
        result = GitService.analyze_repository(request.repo_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Expose MCP protocol endpoints
@app.get("/v1/models")
async def list_models():
    return {"models": [model.dict() for model in mcp_server.list_models()]}

@app.get("/v1/models/{model_id}")
async def get_model_info(model_id: str):
    model = mcp_server.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
    return model.dict()

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)