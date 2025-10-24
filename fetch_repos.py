#!/usr/bin/env python3
import requests
import json
import boto3

def fetch_all_awslabs_repos():
    repos = []
    page = 1
    per_page = 100
    
    while True:
        url = f"https://api.github.com/orgs/awslabs/repos?page={page}&per_page={per_page}"
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
    
    return repos

# Fetch repositories
print("Fetching all awslabs repositories...")
all_repos = fetch_all_awslabs_repos()
print(f"Total repositories found: {len(all_repos)}")

# Upload to S3
s3 = boto3.client('s3')
bucket = 'aws-github-repo-classification'

s3.put_object(
    Bucket=bucket,
    Key='master-index/awslabs_repos_939.json',
    Body=json.dumps(all_repos, indent=2),
    ContentType='application/json'
)

print(f"✅ Uploaded {len(all_repos)} repositories to S3")
