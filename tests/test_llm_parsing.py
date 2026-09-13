"""Parsing of LLM replies and doctor detection, without calling a model."""

import pytest
from pydantic import ValidationError

from backend.config import Config
from backend.services.llm_service import detect_doctor, extract_json_block, parse_tool_action


def test_detect_doctor_is_case_insensitive_and_first_match():
    assert detect_doctor("Hi Sarath, start the incision", Config.DOCTOR_PROFILES) == "sarath"
    assert detect_doctor("KIRAN please stitch", Config.DOCTOR_PROFILES) == "kiran"
    assert detect_doctor("nurse, hand me the scalpel", Config.DOCTOR_PROFILES) is None


@pytest.mark.parametrize("raw", [
    '{"tool": "scalpel", "action": "incision", "handedness": "right"}',
    '```json\n{"tool": "scalpel", "action": "incision", "handedness": "right"}\n```',
    '```\n{"tool": "scalpel", "action": "incision", "handedness": "right"}\n```',
    'Sure! Here you go: {"tool": "scalpel", "action": "incision", "handedness": "right"} Hope that helps.',
])
def test_json_is_recovered_from_fences_and_prose(raw):
    result = parse_tool_action(raw)
    assert (result.tool, result.action, result.handedness) == ("scalpel", "incision", "right")


def test_missing_fields_are_optional_but_wrong_types_fail():
    assert parse_tool_action('{"tool": "forceps"}').action is None
    with pytest.raises(ValidationError):
        parse_tool_action('{"tool": ["a", "b"]}')


def test_garbage_raises():
    with pytest.raises(ValueError):
        parse_tool_action("no json here")


def test_extract_json_block_prefers_outermost_braces():
    assert extract_json_block('x {"a": {"b": 1}} y') == '{"a": {"b": 1}}'
