#!/usr/bin/env bash
# Output VpcId and RDSSecurityGroupId for deploying bastion.yaml.
# Usage: ./scripts/get-bastion-params.sh
# Then: aws cloudformation create-stack ... ParameterKey=VpcId,ParameterValue=<VpcId> ...
set -e
STACK="${STACK_NAME:-ble-people-tracker}"
REGION="${REGION:-us-east-2}"

VPC_ID=$(aws cloudformation list-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResourceSummaries[?LogicalResourceId=='BLEVpc'].PhysicalResourceId" --output text)
RDS_SG=$(aws cloudformation list-stack-resources --stack-name "$STACK" --region "$REGION" \
  --query "StackResourceSummaries[?LogicalResourceId=='RDSSecurityGroup'].PhysicalResourceId" --output text)

if [ -z "$VPC_ID" ] || [ -z "$RDS_SG" ]; then
  echo "Error: Could not get BLEVpc or RDSSecurityGroup from stack $STACK" >&2
  exit 1
fi

echo "VpcId:              $VPC_ID"
echo "RDSSecurityGroupId: $RDS_SG"
echo ""
echo "Deploy bastion with:"
echo "  aws cloudformation create-stack --stack-name ble-people-tracker-bastion \\"
echo "    --template-body file://bastion.yaml \\"
echo "    --parameters \\"
echo "      ParameterKey=VpcId,ParameterValue=$VPC_ID \\"
echo "      ParameterKey=RDSSecurityGroupId,ParameterValue=$RDS_SG \\"
echo "      ParameterKey=KeyName,ParameterValue=YOUR_KEY_PAIR_NAME \\"
echo "    --region $REGION"
