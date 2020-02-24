在开始使用 Index 之前，下面这些概念你必须了解

### 热重载以及注意事项

Index 借助 Python 的 `importlib.reload` 函数，提供了真正的热重载能力。

传统的 Python Web 开发里，所谓热重载，做的最好的也只是将新进程渐步代替旧进程。而 Index 内置的热重载只在进程内更新代码，没有任何进程的新创建或者死亡。你需要做的，只是更新代码。

由于 Python 的设计，在代码文件被更新前已经在处理的请求，依旧会使用旧代码处理；只有在代码文件更新后的请求，才使用新代码去处理。

你最好不要定义可变的全局变量（如：list、dict 等），如果一定要定义，那么请按照下面的格式定义

```python
try:
    users
except NameError:
    users = []
```

也不要直接从其他模块 import 对象，假设 `utils.db` 模块里有一个对象为 `settings`，那么在其他模块中使用时，应使用 `from utils import db` 代替 `from utils.db import settings`，这同样是受限于 Python 的 reload 功能。

违反以上两条规则，并不会影响代码的正常运行，但会在热重载时出现问题。除非你愿意每次更新代码，都重启 Index，否则还是遵守为妙。
