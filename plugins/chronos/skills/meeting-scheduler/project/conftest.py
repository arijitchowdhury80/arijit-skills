import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring live APIs"
    )

def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests that require live gws Google Workspace auth",
    )

def pytest_collection_modifyitems(config, items):
    """
    Skip integration-marked tests by default. Without this, a plain `pytest`
    run hits live Google APIs against whatever account the machine running
    the tests happens to be authenticated as — not reproducible on a fresh
    install with no gws auth configured yet.
    """
    if config.getoption("--run-integration"):
        return
    skip_integration = pytest.mark.skip(reason="requires --run-integration (live gws auth)")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
