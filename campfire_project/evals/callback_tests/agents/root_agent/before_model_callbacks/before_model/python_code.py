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
before_model_callback — Root Agent before model callback
"""

import re
from typing import Iterator, Optional


def is_user_inactive(contents: list) -> bool:
    """Check if the latest user message is a 'no activity' silence signal."""
    silence_pattern = (
        r"<context>no user activity detected for \d+ seconds\.</context>"
    )
    return len(contents) > 1 and any(
        re.search(silence_pattern, p.text, re.IGNORECASE)
        for p in contents[-1].parts
        if p.text
    )


def get_reversed_agent_messages(contents: list) -> Iterator[str]:
    """Yield agent messages from most recent to oldest."""
    for content in reversed(contents):
        texts = []
        for part in content.parts:
            if content.role == "model" and part.text is not None:
                texts.append(part.text)
        if texts:
            yield "".join(texts)


# Escalation Map for resolving triggers to live transfer payload
ESCALATION_MAP = {
    "escalate": {
        "text": "I understand. Let me connect you with a representative who can help. Please hold for a moment.",
        "payload": {
            "escalation_reason": "_escalation_reason",
            "main_topic": "_escalation_topic",
            "summary": "Escalating customer to a live representative.",
        },
    },
    "escalate_tier_2": {
        "text": "This request requires specialized review. I am transferring you to our Tier 2 Billing Support team now. Please hold.",
        "payload": {
            "escalation_reason": "_escalation_reason",
            "main_topic": "_escalation_topic",
            "summary": "Escalating customer to Tier 2 Billing Support.",
        },
    },
    "api_failure_escalate": {
        "text": "I am experiencing technical difficulties. Let me transfer you to a live representative to assist you directly.",
        "payload": {
            "escalation_reason": "API Failure",
            "main_topic": "technical",
            "summary": "System error inside callback",
        },
    },
}


def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    """Intercepts LLM requests for greeting, silence, and escalation."""
    state = callback_context.state

    # 1. Deterministic greeting
    for part in callback_context.get_last_user_input():
        if part.text == "<event>session start</event>":
            greeting = (
                "Thank you for calling Campfire customer support. "
                "How can I help you today?"
            )
            return LlmResponse.from_parts(parts=[
                Part.from_text(text=greeting),
            ])

    # 2. Silence handling
    try:
        if is_user_inactive(llm_request.contents):
            no_input_counter = int(state.get("no_input_counter", 0)) + 1
            state["no_input_counter"] = str(no_input_counter)

            if no_input_counter < 3:
                reversed_msgs = get_reversed_agent_messages(llm_request.contents)
                if no_input_counter == 1:
                    last_msg = next(reversed_msgs, "How can I help you?")
                    return LlmResponse.from_parts(parts=[
                        Part.from_text(text=f"Sorry, I didn't hear anything. {last_msg}")
                    ])
                else:
                    next(reversed_msgs, None)
                    original_msg = next(reversed_msgs, "How can I help you?")
                    return LlmResponse.from_parts(parts=[
                        Part.from_text(text=f"I still can't hear you. {original_msg}")
                    ])
            else:
                return LlmResponse.from_parts(parts=[
                    Part.from_text(
                        text="I'm sorry, but I'm unable to hear you. "
                             "Please try calling again later. Have a great day."
                    ),
                    Part.from_function_call(
                        name="end_session",
                        args={"session_escalated": False, "reason": "no_input_limit"},
                    ),
                ])
        else:
            state["no_input_counter"] = "0"
    except Exception as e:
        print(f"Error in silence handling: {e}")

    # 3. Trigger resolution
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

    # Invoke platform's payload update tool
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
