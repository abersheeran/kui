from indexpy import Index

app = Index(templates=["templates", "other_templates"])

from . import events
from . import exceptions
from . import mounts
from . import responses
