from __future__ import annotations

from typing import List, Union

try:
    import jinja2
except ImportError:
    pass
else:

    class Jinja2TemplatesBase:
        """
        templates = Jinja2Templates("dir", "package:dir")

        return templates.TemplateResponse("index.html", {"request": request})
        """

        def __init__(self, *directories: str) -> None:
            self.env = self.get_env(self.get_loaders(*directories))

        def get_loaders(self, *directories: str) -> jinja2.BaseLoader:
            templates_loaders: List[
                Union[jinja2.FileSystemLoader, jinja2.PackageLoader]
            ] = []
            for directory in directories:
                if ":" in directory:
                    package_name, package_path = directory.split(":", maxsplit=1)
                    templates_loaders.append(
                        jinja2.PackageLoader(package_name, package_path)
                    )
                else:
                    templates_loaders.append(jinja2.FileSystemLoader(directory))
            return jinja2.ChoiceLoader(templates_loaders)

        def get_env(self, loader: jinja2.BaseLoader) -> jinja2.Environment:
            return jinja2.Environment(loader=loader, autoescape=True)
