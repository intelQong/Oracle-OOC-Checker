from pathlib import Path

import pytest

from ooc_checker.setup_wizard import SetupConfig, render_env, write_env_file


def test_render_env_includes_discovered_defaults():
    rendered = render_env(
        SetupConfig(
            compartment_id="ocid1.tenancy.oc1..example",
            availability_domains=("abcd:REGION-AD-1", "abcd:REGION-AD-2"),
            webhook_url="https://example.test/webhook",
            ocpus=4,
            memory_gb=24,
        )
    )

    assert "OCI_COMPARTMENT_ID=ocid1.tenancy.oc1..example" in rendered
    assert "OCI_AVAILABILITY_DOMAINS=abcd:REGION-AD-1,abcd:REGION-AD-2" in rendered
    assert "OCI_SHAPE=VM.Standard.A1.Flex" in rendered
    assert "OCI_OCPUS=4" in rendered
    assert "OCI_MEMORY_GB=24" in rendered
    assert "WEBHOOK_URL=https://example.test/webhook" in rendered


def test_write_env_file_refuses_to_overwrite(tmp_path: Path):
    destination = tmp_path / ".env"
    destination.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_env_file(
            destination,
            SetupConfig(
                compartment_id="ocid1.tenancy.oc1..example",
                availability_domains=("abcd:REGION-AD-1",),
            ),
        )
