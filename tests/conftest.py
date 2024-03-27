# conftest.py
import sys
import os

# Get the path to the directory containing the tests
tests_dir = os.path.dirname(os.path.abspath(__file__))

# Add the directory containing your project code to the sys.path
project_dir = os.path.abspath(os.path.join(tests_dir, ".."))
sys.path.insert(0, project_dir)
