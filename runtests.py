#!/usr/bin/env python
import os
import sys
import warnings

import django
from django.test.utils import get_runner


if __name__ == "__main__":
    tests = sys.argv[1:] or ["tests"]
    warnings.simplefilter("always", DeprecationWarning)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.test_settings")

    if hasattr(django, "setup"):
        django.setup()

    from django.test.runner import DiscoverRunner as TestRunner

    test_runner = TestRunner()
    failures = test_runner.run_tests(tests)
    sys.exit(bool(failures))