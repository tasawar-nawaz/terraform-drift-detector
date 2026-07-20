from drift_detector.config import StateConfig
from drift_detector.state.backends import load_state_document


def test_load_local_state():
    cfg = StateConfig(path="tests/fixtures/sample.tfstate", backend="local")
    doc = load_state_document(cfg)
    assert doc.serial == 42
    assert len(doc.resources) == 3
