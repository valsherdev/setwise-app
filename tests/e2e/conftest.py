import pytest 

import os
import sys
import random
from pathlib import Path

from xprocess import ProcessStarter


@pytest.fixture
def test_web_address(xprocess):
    python_executable = sys.executable
    app_file = Path(__file__).resolve().parents[2] / "app.py"
    port = str(random.randint(4000, 4999))

    class Starter(ProcessStarter):
        env = {
            "PORT": port,
            "APP_ENV": "test",
            **os.environ
        }
        pattern = "Debugger PIN"
        args = [python_executable, app_file]

    xprocess.ensure("setwise_test_server", Starter)

    yield f"http://127.0.0.1:{port}"

    xprocess.getinfo("setwise_test_server").terminate()
