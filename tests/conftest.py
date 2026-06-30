import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--live",
        action="store_true",
        default=False,
        help="Run live integration tests against Screener.in",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "live: mark test as a live integration test")


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--live"):
        skip_live = pytest.mark.skip(reason="use --live to run")
        for item in items:
            if "live" in item.keywords:
                item.add_marker(skip_live)
