import os
from shutil import rmtree

here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

rmtree(os.path.join(here, "site"), ignore_errors=True)

os.system("pipenv run mkdocs build")

os.chdir(os.path.join(here, "site"))
os.system("echo index-py.abersheeran.com > CNAME")  # Custom domain name
os.system("git init")
os.system("git remote add origin https://github.com/abersheeran/index.py")
os.system("git checkout -B gh-pages")
os.system("git add .")
os.system('git commit -m "auto build by mkdocs"')
os.system("git push --set-upstream  origin gh-pages -f")

rmtree(os.path.join(here, "site"), ignore_errors=True)
