from index.openapi.models import *


def test_boolean():
    assert BooleanField().verify("True")
    assert not BooleanField().verify("0")


def test_email():
    EmailField().verify("中文邮箱@亚马逊.中国")
    EmailField().verify("me@abersheeran.com")
    try:
        EmailField().verify("index.py")
        EmailField().verify("@index.py")
        EmailField().verify("py@index")
        assert False
    except FieldVerifyError:
        pass
