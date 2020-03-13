import os

os.system("coverage run -m pytest")
os.system("coverage report --skip-covered")
