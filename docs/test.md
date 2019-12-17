Index 借助了 [starlette 的 Test Client](https://www.starlette.io/testclient/) 用以提供测试能力。

## TestView

`TestView` 做了轻度的封装，你可以直接在需要测试的 HTTP/Socket 的同一个文件内直接编写测试程序，不需要指定测试的URI。

Test Client 的 HTTP 请求部分是基于 requests，保持了 requests 的所有的 API，故而你可以像使用 requests 一样去测试你的程序。

```python
# example/views/index.py

from index.test import TestView
...


class Test(TestView):
    def test_get(self):
        resp = self.client.get()
        assert resp.status_code == 200
        resp = self.client.get(params={"name": "darling"})
        assert resp.status_code == 200

    def test_post(self):
        resp = self.client.post()
        assert resp.status_code == 400
        resp = self.client.post(data={"name": "Aber", "text": "message"})
        assert resp.status_code == 200
```
