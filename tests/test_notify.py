from ooc_checker.models import AvailabilityResult
from ooc_checker.notify import format_summary


def test_format_summary_includes_capacity_details():
    summary = format_summary(
        [
            AvailabilityResult(
                availability_domain="abcd:REGION-AD-1",
                fault_domain="FAULT-DOMAIN-1",
                shape="VM.Standard.A1.Flex",
                ocpus=4,
                memory_gb=24,
                status="AVAILABLE",
                available_count=1,
            )
        ]
    )

    assert "abcd:REGION-AD-1/FAULT-DOMAIN-1" in summary
    assert "AVAILABLE" in summary
    assert "4 OCPU" in summary
    assert "24 GB" in summary
