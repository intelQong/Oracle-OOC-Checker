from unittest.mock import MagicMock
import pytest
import oci

from ooc_checker.config import CheckerConfig
from ooc_checker.checker import check_capacity


def test_check_capacity_resilient_to_ad_failure():
    # Setup config with two ADs
    config = CheckerConfig(
        compartment_id="ocid1.tenancy.oc1..example",
        availability_domains=("abcd:REGION-AD-1", "abcd:REGION-AD-2"),
    )

    # Setup mock client
    mock_client = MagicMock()

    # Success response mock
    mock_response = MagicMock()
    mock_row = MagicMock()
    mock_row.fault_domain = "FAULT-DOMAIN-1"
    mock_row.instance_shape = "VM.Standard.A1.Flex"
    mock_row.instance_shape_config = MagicMock(ocpus=1, memory_in_gbs=6)
    mock_row.availability_status = "AVAILABLE"
    mock_row.available_count = 1
    mock_response.data.shape_availabilities = [mock_row]

    # side_effect: raise exception for the first AD, succeed for the second AD
    def side_effect(details):
        if details.availability_domain == "abcd:REGION-AD-1":
            raise oci.exceptions.ServiceError(
                status=500,
                code="InternalError",
                message="Internal OCI error",
                headers={},
            )
        return mock_response

    mock_client.create_compute_capacity_report.side_effect = side_effect

    # Execute check_capacity
    results = check_capacity(config, client=mock_client)

    # Verify that the check did not raise an exception, and returned the result for the second AD
    assert len(results) == 1
    assert results[0].availability_domain == "abcd:REGION-AD-2"
    assert results[0].is_available is True
