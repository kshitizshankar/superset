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

from sqlglot.dialects.clickhouse import ClickHouse as SqlglotClickHouse
from sqlglot.parsers.clickhouse import ClickHouseParser
from sqlglot.tokens import TokenType


class ClickHouse(SqlglotClickHouse):
    class Parser(ClickHouseParser):
        # `GROUP BY ALL` keeps reading grouping expressions until it reaches a
        # query modifier token. sqlglot derives that set from the base parser, so
        # ClickHouse's `SETTINGS`/`FORMAT` clauses would otherwise be consumed as
        # column names, e.g. `GROUP BY ALL SETTINGS max_threads = 1`.
        QUERY_MODIFIER_TOKENS = ClickHouseParser.QUERY_MODIFIER_TOKENS | {
            TokenType.SETTINGS,
            TokenType.FORMAT,
        }
