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

sys.path.insert(0, os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..", "..", "agents", "root_agent",
    "after_model_callbacks", "after_model",
))

import python_code  # noqa: E402
from python_code import after_model_callback  # noqa: E402
from cxas_scrapi.utils.callback_libs import CallbackContext, LlmResponse  # noqa: E402


class TestStub:
    def test_returns_none(self):
        context = CallbackContext()
        response = LlmResponse()
        res = after_model_callback(context, response)
        assert res is None
