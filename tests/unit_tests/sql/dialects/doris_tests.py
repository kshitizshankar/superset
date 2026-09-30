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

from superset.sql.parse import sanitize_clause, SQLScript


@pytest.mark.parametrize(
    "sql, predicate",
    [
        (
            "SELECT * FROM t WHERE column1 MATCH 'word1 word2'",
            "column1 MATCH 'word1 word2'",
        ),
        (
            "SELECT * FROM t WHERE column1 MATCH_ANY 'word1 word2'",
            "column1 MATCH_ANY 'word1 word2'",
        ),
        (
            "SELECT * FROM t WHERE column1 MATCH_ALL 'word1 word2'",
            "column1 MATCH_ALL 'word1 word2'",
        ),
        (
            "SELECT * FROM t WHERE column1 MATCH_PHRASE 'word1 word2'",
            "column1 MATCH_PHRASE 'word1 word2'",
        ),
        (
            "SELECT * FROM t WHERE column1 MATCH_PHRASE_PREFIX 'word1 word2'",
            "column1 MATCH_PHRASE_PREFIX 'word1 word2'",
        ),
        (
            "SELECT * FROM t WHERE column1 MATCH_PHRASE_EDGE 'word1 word2'",
            "column1 MATCH_PHRASE_EDGE 'word1 word2'",
        ),
        (
            "SELECT * FROM t WHERE column1 MATCH_REGEXP 'word1 word2'",
            "column1 MATCH_REGEXP 'word1 word2'",
        ),
    ],
)
def test_doris_full_text_search_operators(sql: str, predicate: str) -> None:
    """
    Doris full-text search operators are infix: `<column> MATCH_ANY '<text>'`.

    https://doris.apache.org/docs/table-design/index/inverted-index
    """
    script = SQLScript(sql, "pydoris")

    assert len(script.statements) == 1
    assert script.format() == "SELECT\n  *\nFROM t\nWHERE\n  " + predicate


def test_doris_full_text_search_operators_sanitize_clause_with_comment() -> None:
    """
    A clause with a comment is re-rendered by `sanitize_clause`, which must be able
    to generate Doris full-text search operators.
    """
    clause = "column1 MATCH_ANY 'word1 word2' -- comment"

    assert sanitize_clause(clause, "pydoris") == (
        "column1 MATCH_ANY 'word1 word2' /* comment */"
    )
