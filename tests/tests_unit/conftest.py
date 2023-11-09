from pathlib import Path
from unittest.mock import Mock

import pytest
from typer.testing import CliRunner

from _nebari.cli import create_cli
from _nebari.config import write_configuration
from _nebari.constants import (
    AWS_DEFAULT_REGION,
    AZURE_DEFAULT_REGION,
    DO_DEFAULT_REGION,
    GCP_DEFAULT_REGION,
)
from _nebari.initialize import render_config
from _nebari.render import render_template
from _nebari.stages.bootstrap import CiEnum
from nebari import schema
from nebari.plugins import nebari_plugin_manager


@pytest.fixture
def config_path():
    return Path(__file__).parent / "cli_validate"


@pytest.fixture
def config_gcp(config_path):
    return config_path / "gcp.happy.yaml"


@pytest.fixture(autouse=True)
def mock_all_cloud_methods(monkeypatch):
    def _mock_return_value(return_value):
        m = Mock()
        m.return_value = return_value
        return m

    MOCK_VALUES = {
        # AWS
        "_nebari.provider.cloud.amazon_web_services.kubernetes_versions": [
            "1.18",
            "1.19",
            "1.20",
        ],
        "_nebari.provider.cloud.amazon_web_services.check_credentials": None,
        "_nebari.provider.cloud.amazon_web_services.regions": [
            "us-east-1",
            "us-west-2",
        ],
        "_nebari.provider.cloud.amazon_web_services.zones": [
            "us-west-2a",
            "us-west-2b",
        ],
        "_nebari.provider.cloud.amazon_web_services.instances": {
            "m5.xlarge": "m5.xlarge",
            "m5.2xlarge": "m5.2xlarge",
        },
        # Azure
        "_nebari.provider.cloud.azure_cloud.kubernetes_versions": [
            "1.18",
            "1.19",
            "1.20",
        ],
        "_nebari.provider.cloud.azure_cloud.check_credentials": None,
        # Digital Ocean
        "_nebari.provider.cloud.digital_ocean.kubernetes_versions": [
            "1.19.2-do.3",
            "1.20.2-do.0",
            "1.21.5-do.0",
        ],
        "_nebari.provider.cloud.digital_ocean.check_credentials": None,
        "_nebari.provider.cloud.digital_ocean.regions": [
            {"name": "New York 3", "slug": "nyc3"},
        ],
        "_nebari.provider.cloud.digital_ocean.instances": [
            {"name": "s-2vcpu-4gb", "slug": "s-2vcpu-4gb"},
            {"name": "g-2vcpu-8gb", "slug": "g-2vcpu-8gb"},
            {"name": "g-8vcpu-32gb", "slug": "g-8vcpu-32gb"},
            {"name": "g-4vcpu-16gb", "slug": "g-4vcpu-16gb"},
        ],
        # Google Cloud
        "_nebari.provider.cloud.google_cloud.kubernetes_versions": [
            "1.18",
            "1.19",
            "1.20",
        ],
        "_nebari.provider.cloud.google_cloud.check_credentials": None,
        "_nebari.provider.cloud.google_cloud.regions": [
            "us-central1",
            "us-east1",
        ],
    }

    for attribute_path, return_value in MOCK_VALUES.items():
        monkeypatch.setattr(attribute_path, _mock_return_value(return_value))

    monkeypatch.setenv("PROJECT_ID", "pytest-project")


@pytest.fixture(
    params=[
        # cloud_provider, region
        (
            schema.ProviderEnum.do,
            DO_DEFAULT_REGION,
        ),
        (
            schema.ProviderEnum.aws,
            AWS_DEFAULT_REGION,
        ),
        (
            schema.ProviderEnum.gcp,
            GCP_DEFAULT_REGION,
        ),
        (
            schema.ProviderEnum.azure,
            AZURE_DEFAULT_REGION,
        ),
    ]
)
def nebari_config_options(request):
    """This fixtures creates a set of nebari configurations for tests"""
    cloud_provider, region = request.param
    return {
        "project_name": "testproject",
        "nebari_domain": "test.nebari.dev",
        "cloud_provider": cloud_provider,
        "region": region,
        "ci_provider": CiEnum.github_actions,
        "repository": "github.com/test/test",
        "disable_prompt": True,
    }


@pytest.fixture
def nebari_config(nebari_config_options, config_schema):
    return config_schema.model_validate(render_config(**nebari_config_options))


@pytest.fixture
def nebari_stages():
    return nebari_plugin_manager.ordered_stages


@pytest.fixture
def nebari_render(nebari_config, nebari_stages, tmp_path):
    NEBARI_CONFIG_FN = "nebari-config.yaml"

    config_filename = tmp_path / NEBARI_CONFIG_FN
    write_configuration(config_filename, nebari_config)
    render_template(tmp_path, nebari_config, nebari_stages)
    return tmp_path, config_filename


@pytest.fixture
def new_upgrade_cls():
    from _nebari.upgrade import UpgradeStep

    assert UpgradeStep._steps
    steps_cache = UpgradeStep._steps.copy()
    UpgradeStep.clear_steps_registry()
    assert not UpgradeStep._steps
    yield UpgradeStep
    UpgradeStep._steps = steps_cache


@pytest.fixture
def config_schema():
    return nebari_plugin_manager.config_schema


@pytest.fixture
def cli():
    return create_cli()


@pytest.fixture(scope="session")
def runner():
    return CliRunner()
