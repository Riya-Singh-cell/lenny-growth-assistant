import pytest
from app.agents.router import IntentRouter, AgentIntent


@pytest.fixture
def router():
    return IntentRouter()


def test_routes_general_product_question_to_grounded_qa(router):
    intent = router.route("How should an early-stage startup prioritize growth experiments?")
    assert intent == AgentIntent.GROUNDED_QA

    intent2 = router.route("What did Adam Fishman say about onboarding?")
    assert intent2 == AgentIntent.GROUNDED_QA

    intent3 = router.route("Explain Elena Verna's B2B growth loops.")
    assert intent3 == AgentIntent.GROUNDED_QA


def test_routes_ship30_requests(router):
    intent = router.route("Write a Ship 30 for 30 essay on product-led growth onboarding.")
    assert intent == AgentIntent.SHIP30_ESSAY

    intent2 = router.route("Write a 1250 words atomic essay about retention loops")
    assert intent2 == AgentIntent.SHIP30_ESSAY

    intent3 = router.route("Turn this into a publishable essay using ship30 principles")
    assert intent3 == AgentIntent.SHIP30_ESSAY


def test_routes_artifact_requests(router):
    intent = router.route("Create a visual HTML version of the growth framework.")
    assert intent == AgentIntent.ARTIFACT_GEN

    intent2 = router.route("Generate a one-page framework artifact.")
    assert intent2 == AgentIntent.ARTIFACT_GEN

    intent3 = router.route("Turn this into an HTML card document.")
    assert intent3 == AgentIntent.ARTIFACT_GEN
