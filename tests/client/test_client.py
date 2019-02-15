import os
import pathlib

from cli import client


def test_creds():
    creds = client.read_credentials(pathlib.Path(os.path.dirname(__file__)) / "lala.ini")

    assert creds.url == "http://localhost"
    assert creds.user == "uname"
    assert creds.password == "pass"
