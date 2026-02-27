# Connect to the BLE API database with DBeaver

The stack uses **PostgreSQL** (RDS) with a **self-managed password**. Defaults: database **ble**, user **ble**, port **5432**.

---

## 1. Connection details

**Host (RDS endpoint):**
```bash
aws cloudformation describe-stacks --stack-name ble-people-tracker --region us-east-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`DBEndpoint`].OutputValue' --output text
```

**Password:** Use the **self-managed** password you set in the RDS Console (Credentials management). Default used by the stack: **`SAmtvs1234`**.

| Field      | Value |
|-----------|--------|
| **Host**  | From `DBEndpoint` output (e.g. `ble-people-tracker-postgres.xxxx.us-east-2.rds.amazonaws.com`) |
| **Port**  | `5432` |
| **Database** | `ble` (default) |
| **Username** | `ble` (default) |
| **Password** | The RDS master password (e.g. `SAmtvs1234` if you set it in Console) |

---

## 2. RDS is in a private VPC

The RDS instance has **PubliclyAccessible: false**, so it is **not reachable from the internet**. DBeaver on your laptop cannot connect to it directly unless you use one of these:

### Option A: SSH tunnel (bastion)

If you have a bastion host (EC2) in the same VPC that you can SSH into:

1. In DBeaver: **New Connection** → **PostgreSQL**.
2. **Main** tab: set Host to the **RDS endpoint**, Port **5432**, Database **ble**, Username **ble**, Password (self-managed, e.g. **SAmtvs1234**).
3. Open the **SSH** tab: enable **Use SSH Tunnel**.
   - **Host/IP**: bastion public IP or DNS.
   - **Port**: 22.
   - **User**: your SSH user (e.g. `ec2-user`).
   - **Authentication**: Key pair (choose your `.pem`) or password.
4. **Test connection** and finish.

DBeaver will connect to the bastion via SSH and forward traffic to RDS.

### Option B: AWS Session Manager port forwarding

If you have a bastion (or any EC2) in the VPC and use **AWS Systems Manager Session Manager**:

1. In AWS Console (or CLI) start a session with port forwarding, e.g. forward local port **15432** to **RDS_ENDPOINT:5432**.
2. In DBeaver: Host **localhost**, Port **15432**, Database **ble**, Username **ble**, Password (self-managed, e.g. **SAmtvs1234**). No SSH tab needed.

### Option C: Same network as RDS

If you are on a VPN or a machine inside the VPC (e.g. EC2 in the same subnet), use the RDS endpoint and port 5432 directly in DBeaver (no tunnel).

---

## 3. DBeaver steps (when you can reach the host)

1. **Database** → **New Database Connection** → **PostgreSQL**.
2. **Main** tab:
   - **Host**: RDS endpoint (or `localhost` if using a tunnel).
   - **Port**: `5432` (or your local port if using tunnel).
   - **Database**: `ble`
   - **Username**: `ble`
   - **Password**: your RDS self-managed password (e.g. **SAmtvs1234**).
3. Optionally **Test connection** (download drivers if prompted).
4. **Finish**.

You can then browse **readers** and **events** and run SQL.

---

## Summary

| Item       | How to get it |
|------------|----------------|
| Host       | Stack output **DBEndpoint** |
| Port       | `5432` |
| Database   | `ble` |
| Username   | `ble` |
| Password   | Self-managed (set in RDS Console; default **SAmtvs1234**) |
| Reachability | Use SSH tunnel, Session Manager, or VPN; RDS is not public. |
