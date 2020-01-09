Index 借助了 [starlette 的 Test Client](https://www.starlette.io/testclient/) 用以提供测试能力。

## TestView

!!! notice
    在测试程序里，所有的 HTTP 请求、发送 ws 数据、接收 ws 数据都是同步的。

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

而 Test Client 的 websocket 请求部分，就像在 index.py 中使用 websocket 一样，同样有三对发送/接收数据的函数。

你只需要使用 `self.client.websocket_connect()` 即可连接并测试。

```python
class Test(TestView):
    def test_chat(self) -> None:
        with self.client.websocket_connect() as ws:
            ws.send_text("hello")
            assert ws.receive_json()["message"] == "hello"
```

## 执行测试

在项目根目录下执行 `index-cli test` 即可运行测试。更多参数请查看 [Command](/command/)
