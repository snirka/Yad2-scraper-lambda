#!/bin/bash

# Yad2 Car Scraper Lambda Deployment Script
# This script packages and deploys the Lambda function

set -e

echo "🚀 Starting Lambda deployment for Yad2 Car Scraper"

# Configuration
FUNCTION_NAME="yad2-car-scraper"
REGION="${AWS_REGION:-us-east-1}"
MEMORY_SIZE=512
TIMEOUT=900
RUNTIME="python3.9"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

print_status "AWS credentials verified"

# Create deployment package
print_status "Creating deployment package..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
PACKAGE_DIR="$TEMP_DIR/package"
mkdir -p "$PACKAGE_DIR"

# Copy Python files
print_status "Copying source files..."
cp lambda_handler.py "$PACKAGE_DIR/"
cp lambda_config.py "$PACKAGE_DIR/"
cp config.py "$PACKAGE_DIR/"
cp scraper.py "$PACKAGE_DIR/"
cp telegram_bot.py "$PACKAGE_DIR/"
cp manufacturer_mapper.py "$PACKAGE_DIR/"

# Install dependencies
print_status "Installing dependencies..."
pip install -r lambda_requirements.txt -t "$PACKAGE_DIR/" --quiet

# Create manufacturer and model data files in the package
print_status "Including data files..."
mkdir -p "$PACKAGE_DIR/data"

# Copy existing data files if they exist
if [ -f "data/manufacturers.json" ]; then
    cp "data/manufacturers.json" "$PACKAGE_DIR/data/"
    print_status "Included manufacturers.json"
else
    print_warning "manufacturers.json not found - Lambda will use built-in data"
fi

if [ -f "data/models.json" ]; then
    cp "data/models.json" "$PACKAGE_DIR/data/"
    print_status "Included models.json"
else
    print_warning "models.json not found - Lambda will use built-in data"
fi

# Create ZIP package
print_status "Creating ZIP package..."
cd "$PACKAGE_DIR"
zip -r "../lambda-package.zip" . -q
cd - > /dev/null

ZIP_FILE="$TEMP_DIR/lambda-package.zip"
ZIP_SIZE=$(du -h "$ZIP_FILE" | cut -f1)
print_status "Package created: $ZIP_SIZE"

# Deploy Lambda function
print_status "Deploying Lambda function..."

# Check if function exists
if aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &> /dev/null; then
    print_status "Updating existing function..."
    aws lambda update-function-code \
        --function-name "$FUNCTION_NAME" \
        --zip-file "fileb://$ZIP_FILE" \
        --region "$REGION" \
        --output table
    
    # Update function configuration
    aws lambda update-function-configuration \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --memory-size "$MEMORY_SIZE" \
        --timeout "$TIMEOUT" \
        --region "$REGION" \
        --output table
else
    print_status "Creating new function..."
    
    # Get default execution role (you may need to create this)
    ROLE_ARN="arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/lambda-execution-role"
    
    aws lambda create-function \
        --function-name "$FUNCTION_NAME" \
        --runtime "$RUNTIME" \
        --role "$ROLE_ARN" \
        --handler "lambda_handler.lambda_handler" \
        --zip-file "fileb://$ZIP_FILE" \
        --memory-size "$MEMORY_SIZE" \
        --timeout "$TIMEOUT" \
        --region "$REGION" \
        --description "Yad2 Car Scraper - Automated car listing monitor" \
        --output table
fi

# Clean up
rm -rf "$TEMP_DIR"

print_success "Lambda function deployed successfully!"

echo ""
print_status "Next steps:"
echo "1. Set environment variables for your filters:"
echo "   aws lambda update-function-configuration --function-name $FUNCTION_NAME --environment Variables='{\"TELEGRAM_BOT_TOKEN\":\"your_token\",\"TELEGRAM_CHAT_ID\":\"your_chat_id\",\"FILTER_1\":\"{\\\"name\\\":\\\"my-filter\\\",\\\"manufacturer\\\":\\\"37\\\",\\\"model\\\":\\\"10507\\\",\\\"year\\\":\\\"2012-2015\\\"}\"}'"
echo ""
echo "2. Create CloudWatch Events rule for scheduling:"
echo "   aws events put-rule --name yad2-scraper-schedule --schedule-expression 'rate(15 minutes)'"
echo ""
echo "3. Add permission for CloudWatch Events to invoke Lambda:"
echo "   aws lambda add-permission --function-name $FUNCTION_NAME --statement-id allow-cloudwatch --action lambda:InvokeFunction --principal events.amazonaws.com"
echo ""
echo "4. Create target for the rule:"
echo "   aws events put-targets --rule yad2-scraper-schedule --targets 'Id'='1','Arn'='arn:aws:lambda:$REGION:$(aws sts get-caller-identity --query Account --output text):function:$FUNCTION_NAME'"

print_success "Deployment complete! 🎉"