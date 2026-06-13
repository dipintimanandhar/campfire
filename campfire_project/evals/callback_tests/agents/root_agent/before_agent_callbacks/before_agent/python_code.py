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
before_agent_callback — Root Agent initialization
"""

import json
from typing import Optional


def before_agent_callback(callback_context: CallbackContext) -> Optional[Content]:
    """Fires on every turn to initialize user profile state if not already set.

    Args:
        callback_context: The execution context containing session state and variables.

    Returns:
        Optional[Content]: None to continue execution.
    """
    state = callback_context.state

    # Early return if customer_profile is already initialized
    if state.get("customer_profile"):
        return None

    # Retrieve account identifiers from telephony session context
    account_id = state.get("account_id", "")
    customer_id = state.get("customer_id", "")

    # Default profile values - normally fetched via API connector tool
    # e.g., tools.Read_Customer_Datastore_readDatastore(account_id=account_id)
    profile = {
        "account_id": account_id,
        "customer_id": customer_id,
        "name": "John Doe",
        "plan_details": "Premium Plan",
        "active_promotions": "WIFI_PROMO_2026",
        "billing_cycle": "Monthly",
        "auth_status": "NOT_STARTED",
    }

    # Store customer profile as stringified JSON in the session variable
    state["customer_profile"] = json.dumps(profile)
    state["auth_status"] = "NOT_STARTED"

    return None
