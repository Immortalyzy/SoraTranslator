import app as backend_app
import pytest


class DummyConfig:
    def __init__(self, translator="galtransl"):
        self.translator = translator


class DummyProject:
    def __init__(self):
        self.project_path = ""

    def from_pickle(self, project_file_path):
        self.project_path = project_file_path
        return self


class DummyTranslatorSuccess:
    def __init__(self):
        self._progress_callback = None

    def set_progress_callback(self, callback):
        self._progress_callback = callback

    def translate_project(self, _project):
        if callable(self._progress_callback):
            self._progress_callback(
                {
                    "phase": "running",
                    "totalCount": 3,
                    "completedCount": 2,
                    "currentFile": "file2.json",
                }
            )
            self._progress_callback(
                {
                    "phase": "applying_results",
                    "totalCount": 3,
                    "completedCount": 3,
                    "currentFile": "file3.json",
                }
            )


class DummyTranslatorFail:
    def __init__(self):
        self._progress_callback = None

    def set_progress_callback(self, callback):
        self._progress_callback = callback

    def translate_project(self, _project):
        if callable(self._progress_callback):
            self._progress_callback(
                {
                    "phase": "running",
                    "totalCount": 2,
                    "completedCount": 1,
                    "currentFile": "file1.json",
                }
            )
        raise RuntimeError("boom")


@pytest.fixture(autouse=True)
def reset_progress_state():
    backend_app.GALTRANSL_PROGRESS.reset()
    yield
    backend_app.GALTRANSL_PROGRESS.reset()


def patch_galtransl_runtime(monkeypatch):
    monkeypatch.setattr(
        backend_app.Config,
        "load_runtime",
        staticmethod(lambda resolve_env_tokens=True: DummyConfig("galtransl")),
    )


def test_translate_project_progress_idle():
    with backend_app.app.test_client() as client:
        response = client.post("/translate_project_progress", json={})
    payload = response.get_json()
    assert payload["status"] is True
    assert payload["progress"]["active"] is False
    assert payload["progress"]["phase"] == "idle"


def test_translate_project_rejects_overlapping_sessions(monkeypatch):
    patch_galtransl_runtime(monkeypatch)
    backend_app.GALTRANSL_PROGRESS.try_start("D:/Work/SoraTranslator/sample.soraproject")

    with backend_app.app.test_client() as client:
        response = client.post("/translate_project", json={"project_file_path": "D:/busy.soraproject"})

    payload = response.get_json()
    assert response.status_code == 409
    assert payload["status"] is False
    assert payload["busy"] is True


def test_translate_project_sets_completed_terminal_state(monkeypatch):
    patch_galtransl_runtime(monkeypatch)
    monkeypatch.setattr(backend_app, "Project", DummyProject)
    monkeypatch.setattr(
        backend_app,
        "createTranslatorInstance",
        lambda translator, config=None: DummyTranslatorSuccess(),
    )

    with backend_app.app.test_client() as client:
        response = client.post("/translate_project", json={"project_file_path": "D:/ok.soraproject"})
        progress_response = client.post("/translate_project_progress", json={})

    payload = response.get_json()
    progress_payload = progress_response.get_json()["progress"]
    assert payload["status"] is True
    assert progress_payload["active"] is False
    assert progress_payload["phase"] == "completed"
    assert progress_payload["totalCount"] == 3
    assert progress_payload["completedCount"] == 3


def test_translate_project_sets_failed_terminal_state(monkeypatch):
    patch_galtransl_runtime(monkeypatch)
    monkeypatch.setattr(backend_app, "Project", DummyProject)
    monkeypatch.setattr(
        backend_app,
        "createTranslatorInstance",
        lambda translator, config=None: DummyTranslatorFail(),
    )

    with backend_app.app.test_client() as client:
        response = client.post("/translate_project", json={"project_file_path": "D:/fail.soraproject"})
        progress_response = client.post("/translate_project_progress", json={})

    payload = response.get_json()
    progress_payload = progress_response.get_json()["progress"]
    assert payload["status"] is False
    assert progress_payload["active"] is False
    assert progress_payload["phase"] == "failed"
    assert "boom" in progress_payload["error"]
