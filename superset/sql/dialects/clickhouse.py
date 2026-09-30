# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""
ClickHouse dialect for Superset, extending sqlglot's built-in ClickHouse dialect.
"""

from __future__ import annotations

from sqlglot.dialects.clickhouse import ClickHouse as _ClickHouse
from sqlglot.tokens import TokenType


class ClickHouse(_ClickHouse):
    """
    ClickHouse dialect.

    ``SETTINGS`` and ``FORMAT`` are registered as query modifier tokens so the
    ``GROUP BY`` parser stops before them. Without this, ``GROUP BY ALL
    SETTINGS max_threads = 1`` reads ``SETTINGS`` as a grouping expression and
    fails on the remainder of the clause.
    """

    class Parser(_ClickHouse.Parser):
        QUERY_MODIFIER_TOKENS = _ClickHouse.Parser.QUERY_MODIFIER_TOKENS | {
            TokenType.SETTINGS,
            TokenType.FORMAT,
        }
