import pytest

from ooc_checker.config import load_from_env


def test_load_from_env_defaults_to_ampere_a1_shape():
    config = load_from_env(
        {
            "OCI_COMPARTMENT_ID": "ocid1.tenancy.oc1..example",
            "OCI_AVAILABILITY_DOMAINS": "abcd:REGION-AD-1, abcd:REGION-AD-2",
        }
    )

    assert config.shape == "VM.Standard.A1.Flex"
    assert config.ocpus == 1
    assert config.memory_gb == 6
    assert config.availability_domains == ("abcd:REGION-AD-1", "abcd:REGION-AD-2")


def test_load_from_env_requires_availability_domains():
    with pytest.raises(ValueError, match="OCI_AVAILABILITY_DOMAINS"):
        load_from_env({"OCI_COMPARTMENT_ID": "ocid1.tenancy.oc1..example"})
