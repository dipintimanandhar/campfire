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
import json

sys.path.insert(0, os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..", "agents", "root_agent",
    "before_agent_callbacks", "before_agent",
))

import python_code  # noqa: E402
from python_code import before_agent_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext  # noqa: E402


class TestProfileAlreadyInitialized:
    def test_profile_exists_early_return(self):
        context = CallbackContext(state={
            "customer_profile": '{"name": "Alice"}',
            "auth_status": "AUTHENTICATED",
        })
        res = before_agent_callback(context)
        assert res is None
        assert json.loads(context.state["customer_profile"]) == {"name": "Alice"}
        assert context.state["auth_status"] == "AUTHENTICATED"


class TestProfileNotInitialized:
    def test_initializes_profile_with_defaults_and_ids(self):
        context = CallbackContext(state={
            "account_id": "ACC123",
            "customer_id": "CUST999",
        })
        res = before_agent_callback(context)
        assert res is None
        assert context.state["auth_status"] == "NOT_STARTED"
        profile = json.loads(context.state["customer_profile"])
        assert profile["account_id"] == "ACC123"
        assert profile["customer_id"] == "CUST999"
        assert profile["name"] == "John Doe"
        assert profile["plan_details"] == "Premium Plan"
        assert profile["active_promotions"] == "WIFI_PROMO_2026"
        assert profile["billing_cycle"] == "Monthly"
        assert profile["auth_status"] == "NOT_STARTED"

    def test_initializes_profile_with_missing_ids(self):
        context = CallbackContext(state={})
        res = before_agent_callback(context)
        assert res is None
        assert context.state["auth_status"] == "NOT_STARTED"
        profile = json.loads(context.state["customer_profile"])
        assert profile["account_id"] == ""
        assert profile["customer_id"] == ""
