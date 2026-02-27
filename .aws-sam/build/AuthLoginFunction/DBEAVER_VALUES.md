# DBeaver – exact values to paste

Use these in **Database → New Database Connection → PostgreSQL**.

---

## Configure everything (one command)

This deploys the **bastion stack** (new or update), then prints the exact values for DBeaver.

**1. Create an EC2 key pair (once)**  
In **AWS Console → EC2 → Key Pairs → Create key pair** (region **us-east-2**). Name it e.g. **ble-bastion**, save the `.pem` file.

Or with CLI (run in project root, saves `ble-bastion.pem`):
```bash
aws ec2 create-key-pair --key-name ble-bastion --region us-east-2 --query 'KeyMaterial' --output text > ble-bastion.pem && chmod 400 ble-bastion.pem
```

**2. Run the setup script**
```bash
./scripts/setup-dbeaver-access.sh
```
Or with a different key name: `./scripts/setup-dbeaver-access.sh your-key-name`

The script will create/update the stack **ble-people-tracker-bastion**, then print **Host**, **Port**, **Database**, **Username**, **Password**, and **SSH tab** values (bastion IP, user `ec2-user`, private key path). Copy those into DBeaver.

**3. In DBeaver**  
Paste the printed values into the **Main** and **SSH** tabs (SSH: enable **Use SSH Tunnel**, set **Host/IP** to the bastion IP, **Private key** to your `.pem` path). Click **Test Connection**, then **OK**.

---

## Main tab (reference)

| Field      | Exact value |
|------------|-------------|
| **Host**   | `ble-people-tracker-postgres.c58ukigqw7n9.us-east-2.rds.amazonaws.com` |
| **Port**   | `5432` |
| **Database** | `ble` |
| **Username** | `ble` |
| **Password** | Self-managed RDS password (e.g. **SAmtvs1234** – same as set in RDS Console) |

---

## SSH tab (required – RDS is private)

Turn **Use SSH Tunnel** **ON**, then:

| Field | Exact value |
|-------|-------------|
| **Host/IP** | *(bastion public IP – see below)* |
| **Port** | `22` |
| **User** | `ec2-user` |
| **Authentication method** | Public Key |
| **Private key** | Path to your `.pem` file (e.g. `~/Downloads/ble-bastion.pem`) |

**Get bastion IP** (after deploying the bastion stack):
```bash
aws cloudformation describe-stacks --stack-name ble-people-tracker-bastion --region us-east-2 --query 'Stacks[0].Outputs[?OutputKey==`BastionPublicIp`].OutputValue' --output text
```
Paste that IP into **Host/IP** in the SSH tab.

---

## If you don’t have a bastion yet

1. Deploy the bastion stack (see **VPC_ACCESS.md**).
2. Get the bastion IP with the command above.
3. In DBeaver SSH tab set **Host/IP** to that IP and **Private key** to your `.pem` path.

Then **Test connection** in DBeaver.
