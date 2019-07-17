import logging

import pytest


logger = logging.getLogger(__name__)


def pytest_configure(config):
    config.addinivalue_line("markers",
                            "check_env(check1, check2): mark test "
                            "to run only on env, which pass all checks")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item):
    """This hook adds test result info into request.node object."""
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # set a report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"

    setattr(item, "rep_" + rep.when, rep)
