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
Doris dialect for Superset, extending sqlglot's built-in Doris dialect.

sqlglot's Doris parser inherits its grammar from MySQL, which only knows the
`MATCH (col) AGAINST (...)` function form. Doris' inverted-index full-text
search operators are infix instead (`col MATCH_ANY 'text'`), so without this
dialect any query using them fails to parse.
https://doris.apache.org/docs/table-design/index/inverted-index
"""

from __future__ import annotations

from sqlglot import exp
from sqlglot.dialects.doris import Doris as _Doris
from sqlglot.generators.doris import DorisGenerator as _DorisGenerator
from sqlglot.parsers.doris import DorisParser as _DorisParser
from sqlglot.tokens import TokenType

DORIS_FULL_TEXT_OPERATORS = frozenset(
    {
        "MATCH",
        "MATCH_ANY",
        "MATCH_ALL",
        "MATCH_PHRASE",
        "MATCH_PHRASE_PREFIX",
        "MATCH_PHRASE_EDGE",
        "MATCH_REGEXP",
    }
)


class DorisFullTextMatch(exp.Expression, exp.Binary, exp.Predicate):
    """
    `<expr> <kind> '<text>'`, where `kind` is one of `DORIS_FULL_TEXT_OPERATORS`.
    """

    arg_types = {"this": True, "expression": True, "kind": True}


class DorisParser(_DorisParser):
    def _parse_range(self, this: exp.Expr | None = None) -> exp.Expr | None:
        this = this or self._parse_bitwise()

        if (
            self._curr
            and self._next
            and self._curr.token_type == TokenType.VAR
            and self._curr.text.upper() in DORIS_FULL_TEXT_OPERATORS
            and self._next.token_type == TokenType.STRING
        ):
            operator = self._curr.text.upper()
            self._advance()
            this = self.expression(
                DorisFullTextMatch(
                    this=this,
                    expression=self._parse_bitwise(),
                    kind=operator,
                )
            )

        return super()._parse_range(this)


class DorisGenerator(_DorisGenerator):
    TRANSFORMS = {
        **_DorisGenerator.TRANSFORMS,
        DorisFullTextMatch: lambda self, e: (
            f"{self.sql(e, 'this')} {e.text('kind')} {self.sql(e, 'expression')}"
        ),
    }


class Doris(_Doris):
    Parser = DorisParser
    Generator = DorisGenerator
