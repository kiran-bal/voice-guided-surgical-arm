"""The command mapper is pure logic: LLM fields + detection flags -> ESP32 command string."""

import pytest

from backend.services.command_service import CommandService

NO_OBJECT = {"object_detected": False, "height_match": False, "distance_match": False}
OBJECT = {"object_detected": True, "height_match": True, "distance_match": True}


@pytest.fixture
def svc():
    return CommandService()


@pytest.mark.parametrize("action,handedness,detection,expected", [
    ("incision", "right", NO_OBJECT, "a0r"),
    ("incision", "left", NO_OBJECT, "a0l"),
    ("incision", "right", OBJECT, "a1r"),
    ("stitch", "left", OBJECT, "b1l"),
    ("stitch", "right", NO_OBJECT, "b0r"),
    ("grasp", "right", NO_OBJECT, "d0r"),
    ("grasp", "left", OBJECT, "d1l"),
    ("cut", "right", OBJECT, "e1r"),
    ("cut", "left", NO_OBJECT, "e0l"),
])
def test_action_object_handedness_matrix(svc, action, handedness, detection, expected):
    assert svc.map_to_command({"action": action, "handedness": handedness}, detection) == expected


def test_object_requires_all_three_criteria(svc):
    partial = {"object_detected": True, "height_match": True, "distance_match": False}
    assert svc.map_to_command({"action": "incision", "handedness": "right"}, partial) == "a0r"


def test_color_only_mode_overrides_geometry(svc):
    detection = {**NO_OBJECT, "color_only_detected": True}
    assert svc.map_to_command({"action": "stitch", "handedness": "right"}, detection) == "b1r"
    detection = {**OBJECT, "color_only_detected": False}
    assert svc.map_to_command({"action": "stitch", "handedness": "right"}, detection) == "b0r"


def test_missing_or_unknown_action_is_noop(svc):
    assert svc.map_to_command({"action": None, "handedness": "right"}, OBJECT) == "x"
    assert svc.map_to_command({"action": "levitate", "handedness": "right"}, OBJECT) == "x"
    assert svc.map_to_command({}, OBJECT) == "x"


def test_handedness_defaults_to_right_and_is_case_insensitive(svc):
    assert svc.map_to_command({"action": "incision"}, NO_OBJECT) == "a0r"
    assert svc.map_to_command({"action": "INCISION", "handedness": "LEFT"}, NO_OBJECT) == "a0l"


def test_mapping_is_extensible(svc):
    svc.add_action_mapping("retract", "f0", "f1")
    assert svc.map_to_command({"action": "retract", "handedness": "left"}, OBJECT) == "f1l"
    assert svc.validate_command("f0")


def test_malformed_input_never_raises(svc):
    assert svc.map_to_command({"action": 42}, OBJECT) == "x"


@pytest.mark.parametrize("spoken,expected", [
    ("suture", "b0r"), ("Suturing", "b0r"), ("hold", "d0r"), ("grab", "d0r"), ("cutting", "e0r"),
])
def test_action_synonyms_map_to_known_commands(svc, spoken, expected):
    assert svc.map_to_command({"action": spoken, "handedness": "right"}, NO_OBJECT) == expected
