# DBeaver: Get a successful connection

The database is **not** reachable directly from the internet. You must use an **SSH tunnel** through a bastion host.

---

## Step 1: One-time setup (bastion + key)

**1a. Create an EC2 key pair** (if you don’t have `ble-bastion` in region **us-east-2**):

- **Console:** EC2 → Key Pairs → Create key pair → Name: `ble-bastion` → Save the `.pem` file.
- **CLI:**  
  `aws ec2 create-key-pair --key-name ble-bastion --region us-east-2 --query 'KeyMaterial' --output text > ble-bastion.pem && chmod 400 ble-bastion.pem`

**1b. Deploy the bastion and get connection values:**

```bash
cd /Users/juanprice/Desktop/BLE_API
./scripts/setup-dbeaver-access.sh
```

The script prints **Host**, **Port**, **Database**, **Username**, **Password**, and **Bastion IP**. Keep that output; you’ll use it in DBeaver.

---

## Step 2: DBeaver configuration (both tabs)

### Main tab

| Field      | Value |
|------------|--------|
| Connect by | **Host** |
| Host       | `ble-people-tracker-postgres.c58ukigqw7n9.us-east-2.rds.amazonaws.com` |
| Port       | `5432` |
| Database   | `ble` |
| Username   | `ble` |
| Password   | Self-managed RDS password (e.g. **SAmtvs1234**). Same as in RDS Console. |

### SSH tab (required)

| Field        | Value |
|-------------|--------|
| Use SSH Tunnel | **ON** (checked) |
| Host/IP     | *(Bastion public IP from script output)* |
| Port        | `22` |
| User        | `ec2-user` |
| Auth method | **Public Key** |
| Private key | Full path to your `ble-bastion.pem` (e.g. `/Users/juanprice/Desktop/BLE_API/ble-bastion.pem`) |

If the SSH tab is not configured, the connection will **fail** because your machine cannot reach the private RDS endpoint.

---

## Step 3: Test

Click **Test Connection**. If it succeeds, click **OK** and you can browse **Tables** under the connection.

---

## If it still fails

- **“Connection timed out” / “Could not connect”:** Bastion not used or wrong. Ensure **Use SSH Tunnel** is ON and **Host/IP** is the bastion IP from the script.
- **“Authentication failed” (SSH):** Wrong key path or wrong key. Use the `.pem` you created for `ble-bastion`.
- **“Password authentication failed” (DB):** Use the password from the script output (from Secrets Manager), not a password you made up.
