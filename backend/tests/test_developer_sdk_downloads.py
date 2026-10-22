from io import BytesIO
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from fastapi import HTTPException
from fastapi.responses import FileResponse

from app.routers import developer_portal as portal


def request(enabled=True):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
        settings=SimpleNamespace(version="99.0.0", developer_portal_enabled=enabled)
    )))


@pytest.mark.parametrize("language,entry", [("python", "client.py"), ("javascript", "index.mjs")])
def test_missing_release_archive_packages_shipped_sdk(tmp_path, monkeypatch, language, entry):
    monkeypatch.setattr(portal, "SDK_ROOT", tmp_path)
    source = tmp_path / language
    source.mkdir()
    (source / entry).write_text("SDK fixture")
    (source / "README.md").write_text("SDK documentation")
    for folder, name in [("__pycache__", "client.pyc"), (".private", "secret.json"), ("node_modules", "dependency.json")]:
        (source / folder).mkdir()
        (source / folder / name).write_text("excluded")
    response = portal._sdk_download(request(), language)
    assert response.media_type == "application/zip"
    assert f"{language}-v99.0.0.zip" in response.headers["content-disposition"]
    with ZipFile(BytesIO(response.body)) as archive:
        assert set(archive.namelist()) == {entry, "README.md"}
        assert archive.read(entry) == b"SDK fixture"
        assert archive.testzip() is None


def test_existing_release_archive_is_served(tmp_path, monkeypatch):
    monkeypatch.setattr(portal, "SDK_ROOT", tmp_path)
    path = tmp_path / "downloads" / "sc-platform-core-public-python-v99.0.0.zip"
    path.parent.mkdir()
    path.write_bytes(b"prebuilt")
    response = portal.python_sdk(request())
    assert isinstance(response, FileResponse)
    assert response.path == path


@pytest.mark.parametrize("enabled", [True, False])
def test_missing_sdk_or_disabled_portal_remains_unavailable(tmp_path, monkeypatch, enabled):
    monkeypatch.setattr(portal, "SDK_ROOT", tmp_path)
    if not enabled:
        source = tmp_path / "python"
        source.mkdir()
        (source / "client.py").write_text("SDK fixture")
    with pytest.raises(HTTPException) as error:
        portal.python_sdk(request(enabled))
    assert error.value.status_code == 404
