#!/usr/bin/env python3
"""
Generic Repository Fetcher
Fetches all repositories from any GitHub organization
"""

import requests
import json
import boto3
import argparse

def fetch_and_upload_repos(org_name: str):
    """Fetch all repositories for an organization and upload to S3"""
    repos = []
    page = 1
    per_page = 100
    
    print(f"Fetching all {org_name} repositories...")
    
    while True:
        url = f"https://api.github.com/orgs/{org_name}/repos?page={page}&per_page={per_page}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"API Error: {response.status_code}")
            break
            
        page_repos = response.json()
        if not page_repos:
            break
            
        repos.extend(page_repos)
        print(f"Fetched page {page}: {len(page_repos)} repos (total: {len(repos)})")
        page += 1
    
    print(f"Total repositories found: {len(repos)}")
    
    # Upload to S3
    s3 = boto3.client('s3')
    bucket = f'aws-github-repo-classification-{org_name.lower()}'
    
    # Create bucket if it doesn't exist
    try:
        s3.head_bucket(Bucket=bucket)
    except:
        s3.create_bucket(Bucket=bucket)
        print(f"✅ Created bucket: {bucket}")
    
    master_data = {"repositories": repos}
    s3.put_object(
        Bucket=bucket,
        Key=f'master-index/{org_name}_repos.json',
        Body=json.dumps(master_data, indent=2),
        ContentType='application/json'
    )
    
    print(f"✅ Uploaded {len(repos)} repositories to S3")

def main():
    parser = argparse.ArgumentParser(description='Fetch repositories from GitHub organization')
    parser.add_argument('org_name', help='GitHub organization name (e.g., awslabs, microsoft, google)')
    
    args = parser.parse_args()
    fetch_and_upload_repos(args.org_name)

if __name__ == "__main__":
    main()
