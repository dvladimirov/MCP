import pytest

def pytest_addoption(parser):
    """Add command-line options to pytest"""
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that require external services"
    )

def pytest_configure(config):
    """Add markers to pytest configuration"""
    config.addinivalue_line("markers", "integration: mark test as integration test")

def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration is specified"""
    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="Need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration) 