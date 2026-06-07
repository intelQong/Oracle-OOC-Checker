# iPhone-only setup guide

This is the easiest way to run the checker when you do not have a PC. Your iPhone only edits cloud settings; GitHub Actions runs the checker every 10 minutes in GitHub's servers.

## What you will need

- An Oracle Cloud account where you want the Always Free Ampere A1 VM.
- A GitHub account and this repository in GitHub.
- A Discord webhook URL, Slack webhook URL, or another compatible webhook URL if you want phone notifications.
- Safari or another iPhone browser.

## Big picture

1. Use Oracle Cloud Shell from your iPhone browser to generate an API private key and public key.
2. Add the public key to your Oracle Cloud user.
3. Copy the generated OCI config and private key into GitHub repository secrets.
4. Enable the included GitHub Actions workflow.
5. Wait for webhook alerts or check the workflow logs.

The checker does not create the VM. It only tells you when OCI reports capacity. When you get an `AVAILABLE` alert, open Oracle Cloud on your iPhone and create the Ampere VM immediately.

## Step 1: Create an API key in Oracle Cloud Shell

1. Open Oracle Cloud Console on your iPhone.
2. Tap the Cloud Shell icon.
3. Run these commands in Cloud Shell:

   ```bash
   mkdir -p ~/.oci
   openssl genrsa -out ~/.oci/ooc_api_key.pem 2048
   openssl rsa -pubout -in ~/.oci/ooc_api_key.pem -out ~/.oci/ooc_api_key_public.pem
   chmod 600 ~/.oci/ooc_api_key.pem
   cat ~/.oci/ooc_api_key_public.pem
   ```

4. Copy the full public key output, including the `BEGIN PUBLIC KEY` and `END PUBLIC KEY` lines.

## Step 2: Add the public key to your Oracle user

1. In Oracle Cloud Console, open your user profile.
2. Go to **API keys**.
3. Choose **Add API key**.
4. Paste the public key from Cloud Shell.
5. Save it.
6. Copy the fingerprint Oracle shows after saving the key.

## Step 3: Collect OCI values

You need these values:

- `tenancy` OCID.
- `user` OCID.
- `region`, for example `us-ashburn-1`.
- API key `fingerprint` from Step 2.
- Availability domain names.

In Cloud Shell, list availability domains with:

```bash
oci iam availability-domain list --compartment-id '<TENANCY_OCID>' \
  --query 'data[].name' --raw-output
```

Copy the names and join them with commas for the GitHub secret, for example:

```text
abcd:US-ASHBURN-AD-1,abcd:US-ASHBURN-AD-2,abcd:US-ASHBURN-AD-3
```

## Step 4: Create the GitHub secrets from your iPhone

Open this repository in GitHub using Safari, then go to:

**Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

### `OCI_COMPARTMENT_ID`

Use your tenancy OCID, or the compartment OCID where you will create the VM.

### `OCI_AVAILABILITY_DOMAINS`

Use the comma-separated availability domain names from Step 3.

### `OCI_PRIVATE_KEY`

In Cloud Shell, run:

```bash
cat ~/.oci/ooc_api_key.pem
```

Copy the full private key, including the `BEGIN PRIVATE KEY` and `END PRIVATE KEY` lines, and paste it as the secret value.

### `OCI_CONFIG_FILE_CONTENT`

Create this text on your iPhone and replace the placeholders:

```ini
[DEFAULT]
user=<USER_OCID>
fingerprint=<API_KEY_FINGERPRINT>
tenancy=<TENANCY_OCID>
region=<REGION>
key_file=/home/runner/.oci/oci_api_key.pem
```

Paste that full block as the `OCI_CONFIG_FILE_CONTENT` secret.

### Optional: `WEBHOOK_URL`

Add a Discord or Slack-compatible webhook URL if you want a phone notification when capacity is available.

## Step 5: Start the automatic checker

1. In GitHub, open the **Actions** tab.
2. Select **Check OCI Ampere A1 Capacity**.
3. Tap **Run workflow** to test it immediately.
4. After that, GitHub runs it automatically every 10 minutes.

## How you will know capacity is available

- If you added `WEBHOOK_URL`, you will receive a message that says `OCI Ampere A1 capacity is AVAILABLE`.
- If you did not add a webhook, open GitHub **Actions**, open the latest workflow run, and read the **Check capacity** step output.
- Available output looks like this:

```text
abcd:US-ASHBURN-AD-2/FAULT-DOMAIN-1: AVAILABLE (VM.Standard.A1.Flex, 1 OCPU, 6 GB, available count: 1)
```

Out-of-capacity output looks like this:

```text
abcd:US-ASHBURN-AD-1/FAULT-DOMAIN-1: OUT_OF_HOST_CAPACITY (VM.Standard.A1.Flex, 1 OCPU, 6 GB, available count: 0)
```

## Optional: check the full Always Free Ampere size

The workflow defaults to `1` OCPU and `6` GB RAM. To check the full Always Free Ampere allowance:

1. In GitHub, go to **Settings → Secrets and variables → Actions → Variables**.
2. Add repository variable `OCI_OCPUS` with value `4`.
3. Add repository variable `OCI_MEMORY_GB` with value `24`.

## Security cleanup

Do not share these values with anyone:

- `OCI_PRIVATE_KEY`.
- `OCI_CONFIG_FILE_CONTENT`.
- Your OCI user OCID and tenancy OCID.

If you accidentally expose the private key, delete that API key from your Oracle user and create a new one.
