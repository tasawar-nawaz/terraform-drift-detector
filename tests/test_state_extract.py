from drift_detector.extract.registry import get_default_registry
from drift_detector.extract.state import state_to_normalized
from drift_detector.state.reader import StateReader


def test_state_to_normalized_instance():
    doc = StateReader().read("tests/fixtures/sample.tfstate")
    registry = get_default_registry()
    inst = next(r for r in doc.resources if r.resource_type == "aws_instance")
    normalized = state_to_normalized(inst, registry)
    assert normalized is not None
    assert normalized.attributes["instance_type"] == "t3.micro"
    assert normalized.tags["Environment"] == "dev"
    assert normalized.identity.external_id == "i-0123456789abcdef0"
