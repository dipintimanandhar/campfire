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

"""
before_model_callback — Billing Agent
"""

from typing import Optional

ESCALATION_MAP = {
    "escalate": {
        "text": "I understand. Let me connect you with a representative in our billing department who can help. Please hold.",
        "payload": {
            "escalation_reason": "_escalation_reason",
            "main_topic": "_escalation_topic",
            "summary": "Billing inquiry escalation to live agent",
        },
    },
    "escalate_tier_2": {
        "text": "This billing issue requires Tier 2 specialized review. Let me transfer you to our Tier 2 billing support team. Please hold.",
        "payload": {
            "escalation_reason": "_escalation_reason",
            "main_topic": "_escalation_topic",
            "summary": "Billing escalation to Tier 2 Support",
        },
    },
}


def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """Intercepts LLM request to handle deterministic billing escalations."""
    state = callback_context.state
    trigger_value = state.get("_action_trigger", "")
    if trigger_value:
        state["_action_trigger"] = ""  # clear trigger

    if not trigger_value:
        return None

    escalation = ESCALATION_MAP.get(trigger_value)
    if not escalation:
        return None

    payload_args = {}
    for key, value in escalation["payload"].items():
        if isinstance(value, str) and value.startswith("_"):
            payload_args[key] = state.get(value, value)
        else:
            payload_args[key] = value

    try:
        tools.payload_update_tool(payload_args)
    except Exception as e:
        print(f"Failed to run payload_update_tool: {e}")

    return LlmResponse.from_parts(parts=[
        Part.from_text(text=escalation["text"]),
        Part.from_function_call(
            name="end_session",
            args={"session_escalated": True},
        ),
    ])
