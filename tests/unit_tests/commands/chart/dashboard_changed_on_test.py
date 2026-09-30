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
"""Regression coverage for apache/superset#44305.

Adding a chart to a dashboard via ``POST /api/v1/chart/`` (``dashboards``
payload) or ``PUT /api/v1/chart/{id}`` must bump that dashboard's
``changed_on`` / ``changed_by`` so the Dashboards list "Last modified"
column reflects the change. Today the commands only write the
``dashboard_slices`` M2M row, which does not dirty the parent dashboard
row and therefore never fires ``AuditMixin``'s ``onupdate``.
"""

from collections.abc import Iterator
from datetime import datetime, timedelta

import pytest
from flask import g
from pytest_mock import MockerFixture
from sqlalchemy.orm.session import Session

from superset.commands.chart.create import CreateChartCommand
from superset.commands.chart.update import UpdateChartCommand
from superset.models.dashboard import Dashboard
from superset.models.slice import Slice


@pytest.fixture
def session_with_dashboard(session: Session) -> Iterator[tuple[Session, Dashboard]]:
    engine = session.get_bind()
    Dashboard.metadata.create_all(engine)

    dashboard = Dashboard(
        id=1,
        dashboard_title="test_dashboard",
        slug="test_slug",
        slices=[],
        published=True,
    )
    session.add(dashboard)
    session.commit()

    # Backdate the audit stamp so a later save must visibly move it.
    dashboard.changed_on = datetime.now() - timedelta(days=7)
    session.commit()

    yield session, dashboard
    session.rollback()


def _mock_save_dependencies(mocker: MockerFixture, dashboard: Dashboard) -> None:
    datasource = mocker.MagicMock()
    datasource.name = "my_table"
    mocker.patch(
        "superset.commands.chart.create.get_datasource_by_id",
        return_value=datasource,
    )
    mocker.patch("superset.commands.chart.create.security_manager.raise_for_access")
    mocker.patch(
        "superset.commands.chart.create.security_manager.is_editor",
        return_value=True,
    )
    mocker.patch(
        "superset.commands.chart.create.populate_subjects",
        side_effect=lambda properties, exceptions: None,
    )
    mocker.patch(
        "superset.commands.chart.create.DashboardDAO.find_by_ids",
        return_value=[dashboard],
    )
    mocker.patch.object(g, "user", None, create=True)


def test_create_chart_added_to_dashboard_updates_dashboard_changed_on(
    session_with_dashboard: tuple[Session, Dashboard],
    mocker: MockerFixture,
) -> None:
    """Saving a new chart to a dashboard bumps the dashboard's changed_on."""
    session, dashboard = session_with_dashboard
    stale_changed_on = dashboard.changed_on
    _mock_save_dependencies(mocker, dashboard)

    chart = CreateChartCommand(
        {
            "datasource_id": 11,
            "datasource_type": "table",
            "slice_name": "some_name",
            "viz_type": "table",
            "dashboards": [dashboard.id],
        }
    ).run()

    session.refresh(dashboard)
    # The association is written correctly -- only the audit stamp is missed.
    assert chart in dashboard.slices
    assert dashboard.changed_on > stale_changed_on


def test_update_chart_added_to_dashboard_updates_dashboard_changed_on(
    session_with_dashboard: tuple[Session, Dashboard],
    mocker: MockerFixture,
) -> None:
    """PUT /api/v1/chart/{id} adding a dashboard bumps its changed_on too."""
    session, dashboard = session_with_dashboard
    stale_changed_on = dashboard.changed_on

    chart = Slice(
        id=1,
        slice_name="existing chart",
        datasource_id=42,
        datasource_type="table",
        viz_type="table",
        is_managed_externally=False,
    )
    session.add(chart)
    session.commit()

    mocker.patch(
        "superset.commands.chart.update.ChartDAO.find_by_id", return_value=chart
    )
    mocker.patch("superset.commands.chart.update.security_manager.raise_for_editorship")
    mocker.patch(
        "superset.commands.chart.update.security_manager.is_editor",
        return_value=True,
    )
    mocker.patch(
        "superset.commands.chart.update.compute_subjects",
        side_effect=lambda model, properties, exceptions: None,
    )
    mocker.patch(
        "superset.commands.chart.update.DashboardDAO.find_by_ids",
        return_value=[dashboard],
    )
    mocker.patch.object(g, "user", None, create=True)

    UpdateChartCommand(chart.id, {"dashboards": [dashboard.id]}).run()

    session.refresh(dashboard)
    assert chart in dashboard.slices
    assert dashboard.changed_on > stale_changed_on
