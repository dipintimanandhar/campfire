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
    "..", "..", "..", "..", "agents", "dispute_agent",
    "before_model_callbacks", "before_model",
))

import python_code  # noqa: E402
python_code.tools = MagicMock()

from cxas_scrapi.utils.callback_libs import CallbackContext, LlmRequest, LlmResponse, Part  # noqa: E402
python_code.CallbackContext = CallbackContext
python_code.LlmRequest = LlmRequest
python_code.LlmResponse = LlmResponse
python_code.Part = Part

from python_code import before_model_callback  # noqa: E402


class TestNoTrigger:
    def test_no_trigger_returns_none(self):
        context = CallbackContext(state={})
        request = LlmRequest()
        response = before_model_callback(context, request)
        assert response is None

    def test_empty_trigger_returns_none(self):
        context = CallbackContext(state={"_action_trigger": ""})
        request = LlmRequest()
        response = before_model_callback(context, request)
        assert response is None
        assert context.state.get("_action_trigger") == ""


class TestUnrecognizedTrigger:
    def test_unrecognized_trigger_clears_trigger_and_returns_none(self):
        context = CallbackContext(state={"_action_trigger": "unknown_trigger"})
        request = LlmRequest()
        response = before_model_callback(context, request)
        assert response is None
        assert context.state.get("_action_trigger") == ""


class TestEscalationTrigger:
    def test_escalate_trigger_executes_payload_update_and_returns_response(self):
        python_code.tools.payload_update_tool.reset_mock()
        context = CallbackContext(state={
            "_action_trigger": "escalate",
            "_escalation_reason": "wrong_charge",
            "_escalation_topic": "disputes",
        })
        request = LlmRequest()
        response = before_model_callback(context, request)

        assert response is not None
        assert context.state.get("_action_trigger") == ""
        
        # Verify payload update tool call
        python_code.tools.payload_update_tool.assert_called_once_with({
            "escalation_reason": "wrong_charge",
            "main_topic": "disputes",
            "summary": "Dispute inquiry escalation to live agent",
        })

        # Verify response structure
        assert len(response.content.parts) == 2
        assert response.content.parts[0].text == "I understand. Let me connect you with a representative who can help. Please hold."
        assert response.content.parts[1].function_call.name == "end_session"
        assert response.content.parts[1].function_call.args == {"session_escalated": True}

    def test_escalate_tier_2_trigger_executes_payload_update_and_returns_response(self):
        python_code.tools.payload_update_tool.reset_mock()
        context = CallbackContext(state={
            "_action_trigger": "escalate_tier_2",
            "_escalation_reason": "high_dispute",
            "_escalation_topic": "tier2_dispute",
        })
        request = LlmRequest()
        response = before_model_callback(context, request)

        assert response is not None
        assert context.state.get("_action_trigger") == ""
        
        # Verify payload update tool call
        python_code.tools.payload_update_tool.assert_called_once_with({
            "escalation_reason": "high_dispute",
            "main_topic": "tier2_dispute",
            "summary": "Dispute escalation to Tier 2 Billing Support",
        })

        # Verify response structure
        assert len(response.content.parts) == 2
        assert response.content.parts[0].text == "This dispute request requires specialized Tier 2 review. Let me transfer you to our Tier 2 billing support team. Please hold."
        assert response.content.parts[1].function_call.name == "end_session"
        assert response.content.parts[1].function_call.args == {"session_escalated": True}

    def test_payload_update_tool_exception_handled(self):
        python_code.tools.payload_update_tool.reset_mock()
        python_code.tools.payload_update_tool.side_effect = Exception("API error")
        context = CallbackContext(state={
            "_action_trigger": "escalate",
            "_escalation_reason": "wrong_charge",
            "_escalation_topic": "disputes",
        })
        request = LlmRequest()
        
        # Should not raise exception
        response = before_model_callback(context, request)
        assert response is not None
        assert response.content.parts[1].function_call.name == "end_session"
        # Reset side effect
        python_code.tools.payload_update_tool.side_effect = None
