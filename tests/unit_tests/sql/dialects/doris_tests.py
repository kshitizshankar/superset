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


import pytest

from superset.sql.parse import SQLScript


@pytest.mark.parametrize(
    "operator",
    [
        "MATCH",
        "MATCH_ANY",
        "MATCH_ALL",
        "MATCH_PHRASE",
        "MATCH_PHRASE_PREFIX",
        "MATCH_PHRASE_EDGE",
        "MATCH_REGEXP",
    ],
)
def test_doris_full_text_search_operators(operator: str) -> None:
    """
    Doris full-text search operators are infix: `<column> MATCH_ANY '<text>'`.

    https://doris.apache.org/docs/table-design/index/inverted-index
    """
    sql = f"SELECT * FROM t WHERE column1 {operator} 'word1 word2'"  # noqa: S608

    script = SQLScript(sql, "pydoris")

    assert len(script.statements) == 1
    assert script.format() == (
        f"SELECT\n  *\nFROM t\nWHERE\n  column1 {operator} 'word1 word2'"
    )
