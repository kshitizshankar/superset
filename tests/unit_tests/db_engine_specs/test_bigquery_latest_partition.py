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
Latest-partition predicate for BigQuery must ignore special partition IDs.

INFORMATION_SCHEMA.PARTITIONS is emulated with an in-memory SQLite database
attached under the schema name the engine spec queries, so the real
partition lookup SQL is executed against realistic partition IDs.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from unittest import mock

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import select, text
from sqlalchemy.dialects.sqlite import dialect as sqlite_dialect
from sqlalchemy_bigquery import BigQueryDialect

from superset.db_engine_specs.bigquery import BigQueryEngineSpec
from superset.sql.parse import Table


def _database_with_partitions(partition_ids: list[str | None]) -> mock.MagicMock:
    conn = sqlite3.connect(":memory:")
    conn.execute("ATTACH DATABASE ':memory:' AS \"my_dataset.INFORMATION_SCHEMA\"")
    conn.execute(
        'CREATE TABLE "my_dataset.INFORMATION_SCHEMA"."PARTITIONS" '
        "(table_name TEXT, partition_id TEXT)"
    )
    conn.executemany(
        'INSERT INTO "my_dataset.INFORMATION_SCHEMA"."PARTITIONS" VALUES (?, ?)',
        [("my_table", partition_id) for partition_id in partition_ids],
    )

    @contextmanager
    def get_raw_connection(
        *args: object, **kwargs: object
    ) -> Iterator[sqlite3.Connection]:
        yield conn

    database = mock.MagicMock()
    database.get_dialect.return_value = sqlite_dialect()
    database.get_raw_connection.side_effect = get_raw_connection
    return database


def _latest_partition_sql(database: mock.MagicMock) -> str:
    query = select(text("*")).select_from(text("`my_dataset`.`my_table`"))
    result = BigQueryEngineSpec.where_latest_partition(
        database,
        Table("my_table", "my_dataset"),
        query,
    )
    assert result is not None
    return str(
        result.compile(
            dialect=BigQueryDialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


@pytest.fixture(autouse=True)
def partitioned_by_date(mocker: MockerFixture) -> None:
    mocker.patch.object(
        BigQueryEngineSpec,
        "get_time_partition_column",
        return_value="date",
    )


@pytest.mark.parametrize("special_id", ["__NULL__", "__UNPARTITIONED__"])
def test_latest_partition_ignores_special_partition_ids(special_id: str) -> None:
    database = _database_with_partitions(["20240101", "20240315", special_id])

    sql = _latest_partition_sql(database)

    assert special_id not in sql
    assert "20240315" in sql


def test_latest_partition_omitted_without_time_partition() -> None:
    database = _database_with_partitions(["__NULL__", "__UNPARTITIONED__"])

    sql = _latest_partition_sql(database)

    assert "WHERE" not in sql.upper()
    assert "PARSE_DATE" not in sql.upper()
