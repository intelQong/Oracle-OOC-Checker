"""OCI Compute Capacity Report wrapper."""

from __future__ import annotations

from typing import Iterable, Sequence

import oci

from .config import CheckerConfig
from .models import AvailabilityResult


def build_compute_client(config: CheckerConfig) -> oci.core.ComputeClient:
    """Build an OCI Compute client from API-key or instance-principal auth."""

    if config.auth == "instance_principal":
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        return oci.core.ComputeClient(config={}, signer=signer)

    if config.auth != "config":
        raise ValueError("OCI_AUTH must be either 'config' or 'instance_principal'.")

    file_location = config.oci_config_file or oci.config.DEFAULT_LOCATION
    sdk_config = oci.config.from_file(file_location=file_location, profile_name=config.oci_profile)
    oci.config.validate_config(sdk_config)
    return oci.core.ComputeClient(sdk_config)


def make_shape_availability(config: CheckerConfig) -> oci.core.models.CreateCapacityReportShapeAvailabilityDetails:
    """Create the shape availability request for an Ampere A1 Flex configuration."""

    shape_config = oci.core.models.CapacityReportInstanceShapeConfig(
        ocpus=config.ocpus,
        memory_in_gbs=config.memory_gb,
    )
    return oci.core.models.CreateCapacityReportShapeAvailabilityDetails(
        fault_domain=config.fault_domain,
        instance_shape=config.shape,
        instance_shape_config=shape_config,
    )


def normalize_report_rows(
    availability_domain: str,
    rows: Iterable[object],
    requested_ocpus: float,
    requested_memory_gb: float,
) -> list[AvailabilityResult]:
    """Normalize OCI SDK model rows into serializable result rows."""

    results: list[AvailabilityResult] = []
    for row in rows:
        shape_config = getattr(row, "instance_shape_config", None)
        ocpus = getattr(shape_config, "ocpus", None) or requested_ocpus
        memory_gb = getattr(shape_config, "memory_in_gbs", None) or requested_memory_gb
        results.append(
            AvailabilityResult(
                availability_domain=availability_domain,
                fault_domain=getattr(row, "fault_domain", None),
                shape=getattr(row, "instance_shape", ""),
                ocpus=float(ocpus),
                memory_gb=float(memory_gb),
                status=getattr(row, "availability_status", "UNKNOWN"),
                available_count=getattr(row, "available_count", None),
            )
        )
    return results


def check_capacity(config: CheckerConfig, client: oci.core.ComputeClient | None = None) -> list[AvailabilityResult]:
    """Check capacity for the configured shape across all configured availability domains."""

    compute_client = client or build_compute_client(config)
    shape_availability = make_shape_availability(config)
    results: list[AvailabilityResult] = []

    for availability_domain in config.availability_domains:
        details = oci.core.models.CreateComputeCapacityReportDetails(
            compartment_id=config.compartment_id,
            availability_domain=availability_domain,
            shape_availabilities=[shape_availability],
        )
        response = compute_client.create_compute_capacity_report(details)
        report_rows: Sequence[object] = response.data.shape_availabilities or []
        results.extend(normalize_report_rows(availability_domain, report_rows, config.ocpus, config.memory_gb))

    return results
