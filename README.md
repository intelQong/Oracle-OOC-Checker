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
ooc-checker configure
```

`ooc-checker configure` reads your OCI config profile, discovers your tenancy OCID and availability domains, and writes a ready-to-use `.env` file. Add `--webhook-url <url>` if you want Discord/Slack-compatible alerts, or use `--ocpus 4 --memory-gb 24` if you want to check the full Always Free Ampere allocation.

If you cannot use OCI config auto-discovery, copy `.env.example` to `.env` and fill in the values manually.

After `.env` exists, export it and run a check:

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


## How it works

1. You configure the exact VM size you want to create, usually the Always Free Ampere A1 shape `VM.Standard.A1.Flex`.
2. The checker calls the OCI Compute Capacity Report API for each availability domain in `OCI_AVAILABILITY_DOMAINS`.
3. OCI returns a capacity status for the requested shape, OCPU count, memory amount, and fault domain.
4. The checker prints each result. If any row is `AVAILABLE` with a positive or unknown available count, the check is treated as successful.
5. If `WEBHOOK_URL` is set, the checker sends a Discord/Slack-compatible message when capacity is available.

The checker only asks OCI whether capacity exists. It does **not** reserve capacity and it does **not** create a VM for you. When you receive an `AVAILABLE` message, open OCI and create the VM immediately because capacity can disappear quickly.

## Automation and alerts

You have three common automation options:

- **GitHub Actions, included:** the workflow runs every 10 minutes after you add the required repository secrets. You will know capacity is available because the workflow log will show an `AVAILABLE` row, and if `WEBHOOK_URL` is configured you will also receive a webhook message.
- **Continuous local/server mode:** run `ooc-checker --watch --interval 300`. It checks every 5 minutes, prints each result, sends the webhook when capacity is found, then exits.
- **Cron/systemd/container scheduler:** run `ooc-checker` on your own schedule. This is useful if you want the checker to run on a VPS, NAS, or existing OCI instance.

By default, webhook notifications are sent **only when capacity is available**. Set `NOTIFY_ON_UNAVAILABLE=true` if you want a message for every check, including out-of-capacity checks.

## OCI setup

1. Install and configure the OCI CLI or SDK credentials on the machine that runs the checker.
2. Run `ooc-checker configure` to auto-create `.env` from your OCI profile.
3. If you are configuring manually, set `OCI_COMPARTMENT_ID` to the root tenancy OCID or the compartment where you create Always Free instances.
4. If you are configuring manually, set `OCI_AVAILABILITY_DOMAINS` to your region's AD names. You can list them with:

   ```bash
   oci iam availability-domain list --compartment-id "$OCI_COMPARTMENT_ID" \
     --query 'data[].name' --raw-output
   ```

5. If running on an OCI instance with instance principals, set `OCI_AUTH=instance_principal` and grant that dynamic group permission to inspect/use compute capacity reports in the compartment.

## Configure command

The easiest setup path is:

```bash
ooc-checker configure --webhook-url "https://discord.com/api/webhooks/..."
```

This command uses `~/.oci/config` and the `DEFAULT` profile by default. It writes `.env` and refuses to overwrite an existing file unless you pass `--force`. Useful options:

- `--config-file /path/to/config` and `--profile PROFILE` to choose OCI credentials.
- `--compartment-id ocid1.compartment...` to check a compartment instead of the root tenancy from the OCI config.
- `--availability-domains ad1,ad2,ad3` if you want to provide ADs manually instead of auto-discovery.
- `--ocpus 4 --memory-gb 24` to check the full Always Free Ampere allocation.
- `--auth instance_principal --compartment-id ... --availability-domains ...` when running from an OCI instance with instance-principal policies.

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
