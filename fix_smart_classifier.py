#!/usr/bin/env python3
"""
Fix: Add classification results storage to smart classifier
"""

import json
import boto3
import csv
from io import StringIO

def save_classification_results():
    """Re-run classification on completed repos and save actual results"""
    
    # Import the classifier
    import sys
    sys.path.append('/persistent/home/ubuntu/workspace/24oct/awsgithubresearch')
    from smart_rate_limit_classifier import SmartRateLimitClassifier
    
    s3_client = boto3.client('s3')
    bucket_name = 'aws-github-repo-classification-aws-samples'
    
    # Load progress and repos
    progress_response = s3_client.get_object(Bucket=bucket_name, Key='checkpoints/progress.json')
    progress = json.loads(progress_response['Body'].read().decode('utf-8'))
    completed_repos = set(progress.get('completed_repos', []))
    
    repos_response = s3_client.get_object(Bucket=bucket_name, Key='master-index/aws-samples_repos.json')
    data = json.loads(repos_response['Body'].read().decode('utf-8'))
    repos = data.get('repositories', [])
    
    print(f"Re-classifying {len(completed_repos)} completed repositories...")
    
    # Initialize classifier
    classifier = SmartRateLimitClassifier('aws-samples')
    
    # Store all classification results
    all_results = []
    
    # Process only completed repos (no API calls needed)
    for i, repo in enumerate(repos):
        if repo['full_name'] in completed_repos:
            print(f"🔍 Re-classifying {repo['full_name']} ({i+1}/{len(repos)})")
            
            # Run actual classification (this has the real logic)
            classification = classifier.classify_repository(repo)
            if classification:
                all_results.append(classification)
                print(f"✅ {repo['full_name']} - {classification['solution_type']}")
    
    # Generate CSV from actual results
    if all_results:
        csv_buffer = StringIO()
        fieldnames = list(all_results[0].keys())
        
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in all_results:
            writer.writerow(result)
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key='results/classification_results.csv',
            Body=csv_buffer.getvalue(),
            ContentType='text/csv'
        )
        
        # Save locally
        with open('/persistent/home/ubuntu/workspace/24oct/awsgithubresearch/aws_samples_real_classification.csv', 'w') as f:
            f.write(csv_buffer.getvalue())
        
        print(f"✅ Generated real CSV with {len(all_results)} repositories")
        print(f"🔗 CSV: https://{bucket_name}.s3.amazonaws.com/results/classification_results.csv")

if __name__ == "__main__":
    save_classification_results()
