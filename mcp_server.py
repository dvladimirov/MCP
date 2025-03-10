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

# Register models with MCP server
mcp_server.register_model(azure_gpt_model)
mcp_server.register_model(openai_gpt_chat_model)
mcp_server.register_model(openai_gpt_completion_model)
mcp_server.register_model(git_model)
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
    try:
        result = GitService.get_last_commit_diff(request.repo_url)
        return result
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