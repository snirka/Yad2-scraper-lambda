"""
S3 storage manager for Yad2 Car Scraper.

This module handles storing and retrieving JSON data from S3 buckets
instead of local filesystem, making it compatible with AWS Lambda.
"""

import json
import logging
import os
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class S3StorageManager:
    """Manages storage of JSON data in S3 buckets."""
    
    def __init__(self, bucket_name: Optional[str] = None, prefix: str = "yad2-scraper/"):
        """
        Initialize S3 storage manager.
        
        Args:
            bucket_name: S3 bucket name (can be set via S3_BUCKET_NAME env var)
            prefix: S3 key prefix for all objects
        """
        self.logger = logging.getLogger('s3_storage')
        
        # Get bucket name from parameter or environment
        self.bucket_name = bucket_name or os.environ.get('S3_BUCKET_NAME')
        if not self.bucket_name:
            raise ValueError("S3 bucket name must be provided via bucket_name parameter or S3_BUCKET_NAME environment variable")
        
        self.prefix = prefix
        self.s3_client = None
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client('s3')
            self.logger.info(f"Initialized S3 client for bucket: {self.bucket_name}")
        except NoCredentialsError:
            self.logger.error("AWS credentials not found. Please configure AWS credentials.")
            raise
        except Exception as e:
            self.logger.error(f"Failed to initialize S3 client: {e}")
            raise
    
    def _get_s3_key(self, filename: str) -> str:
        """Get full S3 key for a filename."""
        return f"{self.prefix}{filename}"
    
    def bucket_exists(self) -> bool:
        """Check if the S3 bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                self.logger.warning(f"S3 bucket '{self.bucket_name}' does not exist")
            elif error_code == '403':
                self.logger.warning(f"No permission to access S3 bucket '{self.bucket_name}'")
            else:
                self.logger.error(f"Error checking S3 bucket: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error checking S3 bucket: {e}")
            return False
    
    def create_bucket_if_not_exists(self) -> bool:
        """Create S3 bucket if it doesn't exist."""
        if self.bucket_exists():
            return True
        
        try:
            # Create bucket
            if os.environ.get('AWS_DEFAULT_REGION', 'us-east-1') == 'us-east-1':
                # us-east-1 doesn't need LocationConstraint
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
                    }
                )
            
            self.logger.info(f"Created S3 bucket: {self.bucket_name}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyOwnedByYou':
                self.logger.info(f"S3 bucket '{self.bucket_name}' already exists and is owned by you")
                return True
            elif error_code == 'BucketAlreadyExists':
                self.logger.error(f"S3 bucket '{self.bucket_name}' already exists and is owned by someone else")
                return False
            else:
                self.logger.error(f"Failed to create S3 bucket: {e}")
                return False
        except Exception as e:
            self.logger.error(f"Unexpected error creating S3 bucket: {e}")
            return False
    
    def file_exists(self, filename: str) -> bool:
        """Check if a JSON file exists in S3."""
        try:
            s3_key = self._get_s3_key(filename)
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                self.logger.error(f"Error checking if file exists in S3: {e}")
                return False
        except Exception as e:
            self.logger.error(f"Unexpected error checking file existence: {e}")
            return False
    
    def load_json(self, filename: str, default_value: Any = None) -> Any:
        """
        Load JSON data from S3.
        
        Args:
            filename: Name of the JSON file
            default_value: Value to return if file doesn't exist
            
        Returns:
            Parsed JSON data or default_value if file doesn't exist
        """
        try:
            s3_key = self._get_s3_key(filename)
            self.logger.debug(f"Loading JSON from S3: s3://{self.bucket_name}/{s3_key}")
            
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            content = response['Body'].read().decode('utf-8')
            data = json.loads(content)
            
            self.logger.debug(f"Successfully loaded JSON from S3: {filename}")
            return data
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                self.logger.debug(f"JSON file not found in S3: {filename}, returning default value")
                return default_value
            else:
                self.logger.error(f"Error loading JSON from S3: {e}")
                return default_value
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON from S3 file {filename}: {e}")
            return default_value
        except Exception as e:
            self.logger.error(f"Unexpected error loading JSON from S3: {e}")
            return default_value
    
    def save_json(self, filename: str, data: Any) -> bool:
        """
        Save JSON data to S3.
        
        Args:
            filename: Name of the JSON file
            data: Data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            s3_key = self._get_s3_key(filename)
            json_content = json.dumps(data, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"Saving JSON to S3: s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_content.encode('utf-8'),
                ContentType='application/json',
                ServerSideEncryption='AES256'
            )
            
            self.logger.debug(f"Successfully saved JSON to S3: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving JSON to S3: {e}")
            return False
    
    def delete_json(self, filename: str) -> bool:
        """
        Delete JSON file from S3.
        
        Args:
            filename: Name of the JSON file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            s3_key = self._get_s3_key(filename)
            self.logger.debug(f"Deleting JSON from S3: s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            self.logger.debug(f"Successfully deleted JSON from S3: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting JSON from S3: {e}")
            return False
    
    def list_json_files(self) -> list:
        """
        List all JSON files in the S3 bucket with the configured prefix.
        
        Returns:
            List of filenames (without prefix)
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Remove prefix to get just the filename
                    filename = obj['Key'][len(self.prefix):]
                    if filename.endswith('.json'):
                        files.append(filename)
            
            self.logger.debug(f"Found {len(files)} JSON files in S3")
            return files
            
        except Exception as e:
            self.logger.error(f"Error listing JSON files from S3: {e}")
            return []
    
    def get_file_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a file in S3.
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Dictionary with file metadata or None if file doesn't exist
        """
        try:
            s3_key = self._get_s3_key(filename)
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'filename': filename,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType', 'unknown')
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            else:
                self.logger.error(f"Error getting file info from S3: {e}")
                return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting file info: {e}")
            return None


def get_s3_storage() -> S3StorageManager:
    """
    Get S3 storage manager instance.
    
    Returns:
        Configured S3StorageManager instance
    """
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    if not bucket_name:
        raise ValueError("S3_BUCKET_NAME environment variable must be set")
    
    return S3StorageManager(bucket_name=bucket_name)


# For backwards compatibility - provide a way to detect if we're in Lambda mode
def is_lambda_environment() -> bool:
    """Check if we're running in AWS Lambda environment."""
    return os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None


def should_use_s3() -> bool:
    """Check if we should use S3 storage instead of local files."""
    # Use S3 if explicitly enabled or if in Lambda environment
    return (
        os.environ.get('USE_S3_STORAGE', '').lower() in ('true', '1', 'yes') or
        is_lambda_environment()
    )