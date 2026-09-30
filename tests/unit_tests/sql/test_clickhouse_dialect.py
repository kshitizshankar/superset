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

"""Tests for ClickHouse dialect support in sqlglot."""

import pytest

from superset.sql.parse import LimitMethod, SQLScript


@pytest.mark.parametrize("engine", ["clickhouse", "clickhousedb"])
@pytest.mark.parametrize(
    "sql",
    [
        "SELECT a, sum(b) AS s FROM t GROUP BY ALL SETTINGS max_threads = 1",
        (
            "SELECT a, sum(b) AS s FROM t "
            "GROUP BY ALL WITH TOTALS SETTINGS max_threads = 1"
        ),
    ],
)
def test_clickhouse_group_by_all_followed_by_settings(engine: str, sql: str) -> None:
    """
    ClickHouse ``GROUP BY ALL`` must parse when followed directly by a
    ``SETTINGS`` clause, and SQL Lab's limit must be applied without dropping
    either clause.
    """
    script = SQLScript(sql, engine)  # Must not raise SupersetParseError.
    assert not script.has_mutation()

    statement = script.statements[0]
    statement.set_limit_value(1001, LimitMethod.FORCE_LIMIT)
    formatted = " ".join(statement.format().split())
    assert "GROUP BY ALL" in formatted
    assert "SETTINGS max_threads = 1" in formatted
    assert "LIMIT 1001" in formatted
