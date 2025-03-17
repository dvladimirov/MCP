# MCP Test Suite

This directory contains pytest files for testing the MCP services and models.

## Test Structure

The test suite includes tests for:

- MCP Server and API endpoints (`test_mcp_server.py`)
- Filesystem Service (`test_filesystem_service.py`)
- Git Service (`test_git_service.py`)
- Prometheus Service (`test_prometheus_service.py`)
- Kubernetes Metrics Generator (`test_k8s_metrics_generator.py`)
- MCP Grafana Bridge (coming soon)
- MCP Component (coming soon)

## Running Tests

### Install Test Dependencies

```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
pytest
```

### Run Specific Test Files

```bash
pytest tests/test_mcp_server.py
pytest tests/test_filesystem_service.py
```

### Run Tests with Coverage

```bash
pytest --cov=mcp
```

## Integration Tests

Some tests are marked as integration tests because they require external services or create real HTTP servers. These tests are skipped by default.

To run integration tests:

```bash
pytest --run-integration
```

## Continuous Integration

The test suite is designed to be run in a CI environment. Integration tests are automatically skipped in CI to avoid failures due to missing external dependencies.

## Adding New Tests

When adding new tests:

1. Create a new file named `test_<component>.py`
2. Use pytest fixtures for common setup
3. Mock external dependencies where possible
4. Mark integration tests with `@pytest.mark.integration`

## Test Requirements

All tests depend on:
- pytest
- pytest-cov
- requests (for API testing)
- unittest.mock (for mocking external dependencies)

Additional dependencies may be required for specific tests. 