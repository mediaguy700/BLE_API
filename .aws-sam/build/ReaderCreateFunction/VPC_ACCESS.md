# Enable access to the VPC (e.g. DBeaver to RDS)

RDS stays in a **private VPC** (no direct internet). The stack’s **RDS security group** allows TCP 5432 from **0.0.0.0/0** so anything that can reach the VPC (e.g. a bastion) can connect to the DB. To connect from your laptop (e.g. DBeaver), use a **bastion host** and an SSH tunnel.

**One-command setup:** Create an EC2 key pair in us-east-2 (e.g. `ble-bastion`), then run:
```bash
./scripts/setup-dbeaver-access.sh
```
This deploys the bastion stack and prints the exact DBeaver values. See **DBEAVER_VALUES.md** for details.

---

## Option 1: Deploy the bastion stack manually (optional)

A CloudFormation template **`bastion.yaml`** adds a small EC2 (bastion) in a public subnet. You SSH to it and forward port 5432 to RDS, or use DBeaver’s SSH tunnel.

### 1. Get values from the main stack

Run from the project root:

```bash
./scripts/get-bastion-params.sh
```

This prints **VpcId** and **RDSSecurityGroupId** and an example `create-stack` command. Or get them manually:

```bash
aws cloudformation list-stack-resources --stack-name ble-people-tracker --region us-east-2 \
  --query "StackResourceSummaries[?LogicalResourceId=='BLEVpc'].PhysicalResourceId" --output text
aws cloudformation list-stack-resources --stack-name ble-people-tracker --region us-east-2 \
  --query "StackResourceSummaries[?LogicalResourceId=='RDSSecurityGroup'].PhysicalResourceId" --output text
```

Or in **AWS Console**: CloudFormation → stack **ble-people-tracker** → **Resources** tab → find **BLEVpc** (Physical ID = vpc-xxxx) and **RDSSecurityGroup** (Physical ID = sg-xxxx).

### 2. Create an EC2 key pair (if you don’t have one)

In **EC2 → Key Pairs → Create key pair** (e.g. name `ble-bastion`). Save the `.pem` file; you’ll use it for SSH and in DBeaver.

### 3. Deploy the bastion stack

```bash
cd /path/to/BLE_API

aws cloudformation create-stack --stack-name ble-people-tracker-bastion \
  --template-body file://bastion.yaml \
  --parameters \
    ParameterKey=VpcId,ParameterValue=vpc-XXXXXXXX \
    ParameterKey=RDSSecurityGroupId,ParameterValue=sg-XXXXXXXX \
    ParameterKey=KeyName,ParameterValue=ble-bastion \
  --region us-east-2
```

Replace `vpc-XXXXXXXX` and `sg-XXXXXXXX` with the values from step 1, and `ble-bastion` with your key pair name.

### 4. Get the bastion public IP

```bash
aws cloudformation describe-stacks --stack-name ble-people-tracker-bastion --region us-east-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`BastionPublicIp`].OutputValue' --output text
```

### 5. Connect with DBeaver (SSH tunnel)

1. **Database** → **New Database Connection** → **PostgreSQL**.
2. **Main** tab:
   - **Host:** RDS endpoint (e.g. `ble-people-tracker-postgres.xxxx.rds.amazonaws.com`)
   - **Port:** 5432
   - **Database:** ble
   - **Username:** ble
   - **Password:** (from Secrets Manager – see DBEAVER_CONNECT.md)
3. **SSH** tab: enable **Use SSH Tunnel**:
   - **Host/IP:** bastion public IP from step 4
   - **Port:** 22
   - **User:** ec2-user
   - **Authentication method:** Public Key
   - **Private key:** path to your `.pem` file
4. **Test connection** → **Finish**.

---

## Option 2: Manual SSH port forward (no DBeaver SSH tab)

From your terminal:

```bash
ssh -i /path/to/your-key.pem -L 15432:RDS_ENDPOINT:5432 ec2-user@BASTION_PUBLIC_IP
```

Replace `RDS_ENDPOINT` with the RDS hostname (e.g. `ble-people-tracker-postgres.c58ukigqw7n9.us-east-2.rds.amazonaws.com`) and `BASTION_PUBLIC_IP` with the bastion IP. Keep the session open.

Then in DBeaver connect to **Host:** localhost, **Port:** 15432 (no SSH tab).

---

## Summary

| Step | What to do |
|------|-------------|
| 1 | Get **VpcId** and **RDSSecurityGroupId** from the main stack (console or CLI). |
| 2 | Create an EC2 key pair and save the `.pem` file. |
| 3 | Deploy **bastion.yaml** with those parameters and the key name. |
| 4 | Use the bastion **public IP** in DBeaver’s SSH tab (or in an `ssh -L` command). |

After that, you have VPC access for DBeaver (and any other tool) via the bastion.
