# tests/test_state_machine.py

import pytest
from app.core.state_machine import LISTING_MACHINE, PIPELINE_MACHINE, DOCUMENT_MACHINE


# --- Valid transitions ---
def test_listing_valid_transition():
    assert LISTING_MACHINE.can_transition("draft", "active") is True


def test_pipeline_valid_transition():
    assert PIPELINE_MACHINE.can_transition("new", "contacted") is True


def test_document_valid_transition():
    assert DOCUMENT_MACHINE.can_transition("draft", "sent") is True


# --- Invalid transitions ---
def test_listing_invalid_transition():
    assert LISTING_MACHINE.can_transition("sold", "active") is False


def test_pipeline_invalid_transition():
    assert PIPELINE_MACHINE.can_transition("closed", "new") is False


def test_document_invalid_transition():
    assert DOCUMENT_MACHINE.can_transition("signed", "draft") is False


# --- requires_approval flag ---
def test_listing_requires_approval():
    t = LISTING_MACHINE.get_transition("active", "under_contract")
    assert t.requires_approval is True


def test_listing_no_approval_required():
    t = LISTING_MACHINE.get_transition("draft", "active")
    assert t.requires_approval is False


def test_pipeline_requires_approval():
    t = PIPELINE_MACHINE.get_transition("negotiating", "under_contract")
    assert t.requires_approval is True


# --- automation_hook ---
def test_listing_automation_hook():
    t = LISTING_MACHINE.get_transition("draft", "active")
    assert t.automation_hook == "listing.active"


def test_pipeline_automation_hook():
    t = PIPELINE_MACHINE.get_transition("new", "contacted")
    assert t.automation_hook == "pipeline.contacted"


def test_document_automation_hook():
    t = DOCUMENT_MACHINE.get_transition("sent", "signed")
    assert t.automation_hook == "document.signed"


# --- get_transition returns None for invalid ---
def test_get_transition_invalid_returns_none():
    assert LISTING_MACHINE.get_transition("sold", "draft") is None
