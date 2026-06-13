# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..", "agents", "root_agent",
    "before_model_callbacks", "before_model",
))

import python_code  # noqa: E402
python_code.tools = MagicMock()

from cxas_scrapi.utils.callback_libs import (  # noqa: E402
    CallbackContext,
    Event,
    Content,
    Part,
    LlmRequest,
    LlmResponse,
)
python_code.CallbackContext = CallbackContext
python_code.Event = Event
python_code.Content = Content
python_code.Part = Part
python_code.LlmRequest = LlmRequest
python_code.LlmResponse = LlmResponse

from python_code import before_model_callback  # noqa: E402


class TestGreeting:
    def test_session_start_trigger_greeting(self):
        context = CallbackContext(
            events=[
                Event(
                    id="e1",
                    author="user",
                    timestamp=1000,
                    invocationId="inv1",
                    content=Content(role="user", parts=[Part(text="<event>session start</event>")]),
                )
            ]
        )
        request = LlmRequest()
        response = before_model_callback(context, request)
        assert response is not None
        assert len(response.content.parts) == 1
        assert "Thank you for calling Campfire customer support" in response.content.parts[0].text


class TestSilenceHandling:
    def test_silence_turn_1(self):
        context = CallbackContext(state={"no_input_counter": "0"})
        request = LlmRequest(contents=[
            Content(role="model", parts=[Part(text="How can I help you?")]),
            Content(role="user", parts=[Part(text="<context>no user activity detected for 10 seconds.</context>")]),
        ])
        response = before_model_callback(context, request)
        assert response is not None
        assert context.state["no_input_counter"] == "1"
        assert response.content.parts[0].text == "Sorry, I didn't hear anything. How can I help you?"

    def test_silence_turn_2(self):
        context = CallbackContext(state={"no_input_counter": "1"})
        request = LlmRequest(contents=[
            Content(role="model", parts=[Part(text="Hello!")]),
            Content(role="user", parts=[Part(text="Hi")]),
            Content(role="model", parts=[Part(text="How can I help you?")]),
            Content(role="user", parts=[Part(text="<context>no user activity detected for 10 seconds.</context>")]),
        ])
        response = before_model_callback(context, request)
        assert response is not None
        assert context.state["no_input_counter"] == "2"
        # original message (second to last model message) should be "Hello!"
        assert response.content.parts[0].text == "I still can't hear you. Hello!"

    def test_silence_turn_3(self):
        context = CallbackContext(state={"no_input_counter": "2"})
        request = LlmRequest(contents=[
            Content(role="model", parts=[Part(text="How can I help you?")]),
            Content(role="user", parts=[Part(text="<context>no user activity detected for 10 seconds.</context>")]),
        ])
        response = before_model_callback(context, request)
        assert response is not None
        assert len(response.content.parts) == 2
        assert "I'm sorry, but I'm unable to hear you." in response.content.parts[0].text
        assert response.content.parts[1].function_call.name == "end_session"
        assert response.content.parts[1].function_call.args == {"session_escalated": False, "reason": "no_input_limit"}

    def test_active_turn_resets_counter(self):
        context = CallbackContext(state={"no_input_counter": "2"})
        request = LlmRequest(contents=[
            Content(role="model", parts=[Part(text="How can I help you?")]),
            Content(role="user", parts=[Part(text="I have a question")]),
        ])
        response = before_model_callback(context, request)
        # Should return None (normal model execution path)
        assert response is None
        assert context.state["no_input_counter"] == "0"


class TestEscalationTriggers:
    def test_escalate(self):
        python_code.tools.payload_update_tool.reset_mock()
        context = CallbackContext(state={
            "_action_trigger": "escalate",
            "_escalation_reason": "bad_billing",
            "_escalation_topic": "billing_issue",
        })
        request = LlmRequest()
        response = before_model_callback(context, request)
        assert response is not None
        assert context.state.get("_action_trigger") == ""
        python_code.tools.payload_update_tool.assert_called_once_with({
            "escalation_reason": "bad_billing",
            "main_topic": "billing_issue",
            "summary": "Escalating customer to a live representative.",
        })
        assert len(response.content.parts) == 2
        assert "Let me connect you with a representative who can help." in response.content.parts[0].text
        assert response.content.parts[1].function_call.name == "end_session"
        assert response.content.parts[1].function_call.args == {"session_escalated": True}

    def test_escalate_tier_2(self):
        python_code.tools.payload_update_tool.reset_mock()
        context = CallbackContext(state={
            "_action_trigger": "escalate_tier_2",
            "_escalation_reason": "tier_2_billing",
            "_escalation_topic": "special_billing",
        })
        request = LlmRequest()
        response = before_model_callback(context, request)
        assert response is not None
        assert context.state.get("_action_trigger") == ""
        python_code.tools.payload_update_tool.assert_called_once_with({
            "escalation_reason": "tier_2_billing",
            "main_topic": "special_billing",
            "summary": "Escalating customer to Tier 2 Billing Support.",
        })
        assert "I am transferring you to our Tier 2 Billing Support team" in response.content.parts[0].text

    def test_api_failure_escalate(self):
        python_code.tools.payload_update_tool.reset_mock()
        context = CallbackContext(state={
            "_action_trigger": "api_failure_escalate",
        })
        request = LlmRequest()
        response = before_model_callback(context, request)
        assert response is not None
        assert context.state.get("_action_trigger") == ""
        python_code.tools.payload_update_tool.assert_called_once_with({
            "escalation_reason": "API Failure",
            "main_topic": "technical",
            "summary": "System error inside callback",
        })
        assert "I am experiencing technical difficulties." in response.content.parts[0].text
