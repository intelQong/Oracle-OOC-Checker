# Oracle OOC Checker

Checks whether Oracle Cloud Infrastructure (OCI) has host capacity for the **Always Free Ampere A1 / Arm** shape `VM.Standard.A1.Flex` before you try to create a VM.

The checker uses OCI's **Compute Capacity Report** API, which is the supported way to determine whether capacity is available for a shape before launching an instance.

## What it checks

Default target:

- Shape: `VM.Standard.A1.Flex`
- CPU: `1` OCPU
- Memory: `6` GB
- Availability domains: every AD you configure in `OCI_AVAILABILITY_DOMAINS`

You can raise the request to the Always Free Ampere allocation, for example `OCI_OCPUS=4` and `OCI_MEMORY_GB=24`.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
cp .env.example .env
```

Edit `.env`, then export it and run a check:

```bash
set -a
. ./.env
set +a
ooc-checker
```

Example output:

```text
abcd:US-ASHBURN-AD-1/FAULT-DOMAIN-1: OUT_OF_HOST_CAPACITY (VM.Standard.A1.Flex, 1 OCPU, 6 GB, available count: 0)
abcd:US-ASHBURN-AD-2/FAULT-DOMAIN-1: AVAILABLE (VM.Standard.A1.Flex, 1 OCPU, 6 GB, available count: 1)
```

## OCI setup

1. Install and configure the OCI CLI or SDK credentials on the machine that runs the checker.
2. Set `OCI_COMPARTMENT_ID` to the root tenancy OCID or the compartment where you create Always Free instances.
3. Set `OCI_AVAILABILITY_DOMAINS` to your region's AD names. You can list them with:

   ```bash
   oci iam availability-domain list --compartment-id "$OCI_COMPARTMENT_ID" \
     --query 'data[].name' --raw-output
   ```

4. If running on an OCI instance with instance principals, set `OCI_AUTH=instance_principal` and grant that dynamic group permission to inspect/use compute capacity reports in the compartment.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `OCI_COMPARTMENT_ID` | required | Root tenancy OCID or target compartment OCID. |
| `OCI_AVAILABILITY_DOMAINS` | required | Comma-separated availability domain names. |
| `OCI_SHAPE` | `VM.Standard.A1.Flex` | Shape to query. |
| `OCI_OCPUS` | `1` | Requested OCPUs for the flexible shape. |
| `OCI_MEMORY_GB` | `6` | Requested memory in GB. |
| `OCI_FAULT_DOMAIN` | unset | Optional single fault domain to check. Unset checks all fault domains returned by the report. |
| `OCI_AUTH` | `config` | `config` for API-key auth or `instance_principal` on OCI compute. |
| `OCI_CONFIG_FILE` | SDK default | Path to OCI config file when `OCI_AUTH=config`. |
| `OCI_PROFILE` | `DEFAULT` | OCI config profile. |
| `WEBHOOK_URL` | unset | Optional generic webhook URL. Discord and Slack-compatible endpoints are supported. |
| `NOTIFY_ON_UNAVAILABLE` | `false` | Notify every run, even when capacity is not available. By default the webhook fires only when capacity is available. |
| `OUTPUT_JSON` | `false` | Print machine-readable JSON. |
| `EXIT_NONZERO_WHEN_UNAVAILABLE` | `false` | Exit with code `2` when all checked rows are unavailable. |

## Run continuously

```bash
ooc-checker --watch --interval 300
```

`--watch` keeps checking until capacity is found. For background operation, run it under `systemd`, `cron`, a container scheduler, or the included GitHub Actions workflow.

## GitHub Actions automatic check

The workflow in `.github/workflows/check-capacity.yml` runs every 10 minutes and can also be started manually.

Add these repository secrets:

- `OCI_COMPARTMENT_ID`
- `OCI_AVAILABILITY_DOMAINS`
- `OCI_CONFIG_FILE_CONTENT` — contents of your OCI config file, with `key_file=/home/runner/.oci/oci_api_key.pem`
- `OCI_PRIVATE_KEY` — your API private key PEM
- Optional: `WEBHOOK_URL`

Then enable Actions for the repository. The workflow uses `EXIT_NONZERO_WHEN_UNAVAILABLE=false` so scheduled checks do not show as failures when capacity is simply out.

## Notes

- Capacity can change quickly; an `AVAILABLE` result is a signal to try creating the VM immediately, not a reservation.
- The checker does not create or delete any OCI resources.
- If you want a single large Always Free VM, set `OCI_OCPUS=4` and `OCI_MEMORY_GB=24`; if you want smaller instances, use the exact size you plan to launch.
