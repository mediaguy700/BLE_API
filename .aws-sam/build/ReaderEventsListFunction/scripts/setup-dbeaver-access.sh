#!/usr/bin/env bash
# Deploy the bastion stack (create or update), then print exact DBeaver connection values.
# Prerequisite: Create an EC2 key pair in us-east-2 (e.g. "ble-bastion") and have the .pem file.
#
# Usage:
#   ./scripts/setup-dbeaver-access.sh [KEY_NAME]
#   KEY_NAME defaults to "ble-bastion". Example: ./scripts/setup-dbeaver-access.sh my-key
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KEY_NAME="${1:-ble-bastion}"
STACK_MAIN="${STACK_NAME:-ble-people-tracker}"
STACK_BASTION="${STACK_MAIN}-bastion"
REGION="${REGION:-us-east-2}"

echo "=== BLE DBeaver access setup ==="
echo "Main stack: $STACK_MAIN"
echo "Bastion stack: $STACK_BASTION"
echo "Region: $REGION"
echo "Key pair name: $KEY_NAME"
echo ""

# 0. Check EC2 key pair exists
if ! aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &>/dev/null; then
  echo "Error: EC2 key pair '$KEY_NAME' not found in region $REGION." >&2
  echo "Create one in AWS Console: EC2 → Key Pairs → Create key pair (name: $KEY_NAME)." >&2
  echo "Or with CLI: aws ec2 create-key-pair --key-name $KEY_NAME --region $REGION --query 'KeyMaterial' --output text > $KEY_NAME.pem && chmod 400 $KEY_NAME.pem" >&2
  exit 1
fi

# 1. Get VpcId and RDSSecurityGroupId from main stack
echo "Getting VPC and RDS security group from $STACK_MAIN..."
VPC_ID=$(aws cloudformation list-stack-resources --stack-name "$STACK_MAIN" --region "$REGION" \
  --query "StackResourceSummaries[?LogicalResourceId=='BLEVpc'].PhysicalResourceId" --output text 2>/dev/null || true)
RDS_SG=$(aws cloudformation list-stack-resources --stack-name "$STACK_MAIN" --region "$REGION" \
  --query "StackResourceSummaries[?LogicalResourceId=='RDSSecurityGroup'].PhysicalResourceId" --output text 2>/dev/null || true)

if [ -z "$VPC_ID" ] || [ -z "$RDS_SG" ]; then
  echo "Error: Could not get BLEVpc or RDSSecurityGroup from stack $STACK_MAIN. Is the main stack deployed?" >&2
  exit 1
fi
echo "  VpcId: $VPC_ID"
echo "  RDSSecurityGroupId: $RDS_SG"
echo ""

# 2. Deploy bastion stack (create or update)
cd "$PROJECT_ROOT"
if aws cloudformation describe-stacks --stack-name "$STACK_BASTION" --region "$REGION" &>/dev/null; then
  echo "Updating bastion stack $STACK_BASTION..."
  if aws cloudformation update-stack --stack-name "$STACK_BASTION" --region "$REGION" \
    --template-body file://bastion.yaml \
    --parameters \
      "ParameterKey=VpcId,ParameterValue=$VPC_ID" \
      "ParameterKey=RDSSecurityGroupId,ParameterValue=$RDS_SG" \
      "ParameterKey=KeyName,ParameterValue=$KEY_NAME" 2>/dev/null; then
    echo "Waiting for stack update..."
    aws cloudformation wait stack-update-complete --stack-name "$STACK_BASTION" --region "$REGION"
  else
    echo "(No updates to apply or update failed; continuing.)"
  fi
else
  echo "Creating bastion stack $STACK_BASTION..."
  aws cloudformation create-stack --stack-name "$STACK_BASTION" --region "$REGION" \
    --template-body file://bastion.yaml \
    --parameters \
      "ParameterKey=VpcId,ParameterValue=$VPC_ID" \
      "ParameterKey=RDSSecurityGroupId,ParameterValue=$RDS_SG" \
      "ParameterKey=KeyName,ParameterValue=$KEY_NAME"
  echo "Waiting for stack creation (2–4 min)..."
  aws cloudformation wait stack-create-complete --stack-name "$STACK_BASTION" --region "$REGION"
fi
echo "Bastion stack ready."
echo ""

# 3. Get bastion public IP
BASTION_IP=$(aws cloudformation describe-stacks --stack-name "$STACK_BASTION" --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`BastionPublicIp`].OutputValue' --output text)
if [ -z "$BASTION_IP" ] || [ "$BASTION_IP" == "None" ]; then
  echo "Error: Could not get BastionPublicIp from $STACK_BASTION" >&2
  exit 1
fi
echo "Bastion public IP: $BASTION_IP"
echo ""

# 4. Get RDS endpoint; password is self-managed (no Secrets Manager)
DB_HOST=$(aws cloudformation describe-stacks --stack-name "$STACK_MAIN" --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`DBEndpoint`].OutputValue' --output text)
DB_PASSWORD="${DB_PASSWORD:-SAmtvs1234}"
echo ""

# 5. Print DBeaver values
echo "=============================================="
echo "DBeaver – copy these values"
echo "=============================================="
echo ""
echo "--- Main tab ---"
echo "  Host:     $DB_HOST"
echo "  Port:     5432"
echo "  Database: ble"
echo "  Username: ble"
echo "  Password: $DB_PASSWORD"
echo ""
echo "--- SSH tab (enable 'Use SSH Tunnel') ---"
echo "  Host/IP:  $BASTION_IP"
echo "  Port:     22"
echo "  User:     ec2-user"
echo "  Auth:     Public Key"
echo "  Private key: path to your $KEY_NAME.pem file"
echo ""
echo "=============================================="
echo "Save the password above; it will not be shown again."
echo "In DBeaver: Test Connection, then OK."
echo "=============================================="
