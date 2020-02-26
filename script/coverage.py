import os

os.system("coverage run -m pytest; coverage report --skip-covered")
