#!/usr/bin/env python3
"""
Enhanced Classifier V2 - Production-ready AWS services detection and description enhancement
Fixes critical data quality issues: AWS services detection and missing descriptions
"""

import json
import boto3
import time
import requests
import re
import sys
import argparse
import base64
from datetime import datetime
from typing import Dict, List, Optional, Set
from smart_rate_limit_classifier import SmartRateLimitClassifier

class EnhancedClassifierV2(SmartRateLimitClassifier):
    def __init__(self, org_name: str):
        super().__init__(org_name)
        self.readme_cache = {}  # Cache README content to avoid duplicate API calls
        self.topics_cache = {}  # Cache topics
        
        # Enhanced AWS services mapping
        self.aws_services_map = {
            # Compute
            'lambda': 'Lambda', 'ec2': 'EC2', 'ecs': 'ECS', 'eks': 'EKS', 'fargate': 'Fargate',
            'batch': 'Batch', 'lightsail': 'Lightsail',
            
            # Storage
            's3': 'S3', 'ebs': 'EBS', 'efs': 'EFS', 'fsx': 'FSx',
            
            # Database
            'rds': 'RDS', 'dynamodb': 'DynamoDB', 'aurora': 'Aurora', 'redshift': 'Redshift',
            'documentdb': 'DocumentDB', 'neptune': 'Neptune', 'timestream': 'Timestream',
            
            # Networking
            'vpc': 'VPC', 'cloudfront': 'CloudFront', 'route53': 'Route53', 'elb': 'ELB',
            'alb': 'ALB', 'nlb': 'NLB', 'api gateway': 'API Gateway', 'apigateway': 'API Gateway',
            
            # Security
            'iam': 'IAM', 'cognito': 'Cognito', 'kms': 'KMS', 'secrets manager': 'Secrets Manager',
            'certificate manager': 'ACM', 'waf': 'WAF',
            
            # Analytics
            'kinesis': 'Kinesis', 'athena': 'Athena', 'glue': 'Glue', 'emr': 'EMR',
            'quicksight': 'QuickSight', 'elasticsearch': 'OpenSearch',
            
            # AI/ML
            'sagemaker': 'SageMaker', 'bedrock': 'Bedrock', 'comprehend': 'Comprehend',
            'rekognition': 'Rekognition', 'textract': 'Textract', 'polly': 'Polly',
            
            # DevOps
            'cloudformation': 'CloudFormation', 'cdk': 'CDK', 'codebuild': 'CodeBuild',
            'codedeploy': 'CodeDeploy', 'codepipeline': 'CodePipeline', 'codecommit': 'CodeCommit',
            
            # Monitoring
            'cloudwatch': 'CloudWatch', 'x-ray': 'X-Ray', 'cloudtrail': 'CloudTrail',
            
            # Messaging
            'sns': 'SNS', 'sqs': 'SQS', 'eventbridge': 'EventBridge', 'step functions': 'Step Functions'
        }

    def get_readme_content_cached(self, repo: Dict) -> str:
        """Get README content with caching and rate limit handling"""
        repo_name = repo['full_name']
        
        if repo_name in self.readme_cache:
            return self.readme_cache[repo_name]
        
        for attempt in range(self.max_retries):
            try:
                url = f"https://api.github.com/repos/{repo_name}/readme"
                headers = {}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if self.handle_rate_limit(response):
                    continue
                    
                if response.status_code == 200:
                    content = base64.b64decode(response.json()['content']).decode('utf-8', errors='ignore')
                    # Cache first 3000 chars for performance
                    self.readme_cache[repo_name] = content[:3000]
                    return self.readme_cache[repo_name]
                else:
                    break
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"⚠️  Failed to get README for {repo_name}: {e}")
                time.sleep(1)
        
        self.readme_cache[repo_name] = ""
        return ""

    def get_repo_topics_cached(self, repo: Dict) -> List[str]:
        """Get repository topics with caching"""
        repo_name = repo['full_name']
        
        if repo_name in self.topics_cache:
            return self.topics_cache[repo_name]
        
        # First try from repo data
        topics = repo.get('topics', [])
        if topics:
            self.topics_cache[repo_name] = topics
            return topics
        
        # Fallback to API call if needed
        for attempt in range(self.max_retries):
            try:
                url = f"https://api.github.com/repos/{repo_name}/topics"
                headers = {'Accept': 'application/vnd.github.mercy-preview+json'}
                if self.github_token:
                    headers['Authorization'] = f'token {self.github_token}'
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if self.handle_rate_limit(response):
                    continue
                    
                if response.status_code == 200:
                    topics = response.json().get('names', [])
                    self.topics_cache[repo_name] = topics
                    return topics
                else:
                    break
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"⚠️  Failed to get topics for {repo_name}: {e}")
                time.sleep(1)
        
        self.topics_cache[repo_name] = []
        return []

    def extract_aws_services_from_text(self, text: str) -> Set[str]:
        """Extract AWS services from text using enhanced keyword matching"""
        if not text:
            return set()
        
        text_lower = text.lower()
        services = set()
        
        for keyword, service in self.aws_services_map.items():
            # Look for keyword with word boundaries
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                services.add(service)
        
        return services

    def map_topics_to_services(self, topics: List[str]) -> Set[str]:
        """Map GitHub topics to AWS services"""
        services = set()
        
        for topic in topics:
            topic_lower = topic.lower()
            if topic_lower in self.aws_services_map:
                services.add(self.aws_services_map[topic_lower])
            # Handle common topic variations
            elif topic_lower in ['serverless', 'aws-lambda']:
                services.add('Lambda')
            elif topic_lower in ['aws-s3', 'amazon-s3']:
                services.add('S3')
            elif topic_lower in ['aws-dynamodb']:
                services.add('DynamoDB')
        
        return services

    def get_aws_services_enhanced(self, repo: Dict) -> str:
        """Enhanced AWS services detection from multiple sources"""
        services = set()
        sources = []
        
        # Source 1: Repository description
        desc = repo.get('description', '')
        if desc:
            desc_services = self.extract_aws_services_from_text(desc)
            services.update(desc_services)
            if desc_services:
                sources.append('description')
        
        # Source 2: README content
        readme = self.get_readme_content_cached(repo)
        if readme:
            readme_services = self.extract_aws_services_from_text(readme)
            services.update(readme_services)
            if readme_services:
                sources.append('readme')
        
        # Source 3: GitHub topics
        topics = self.get_repo_topics_cached(repo)
        if topics:
            topic_services = self.map_topics_to_services(topics)
            services.update(topic_services)
            if topic_services:
                sources.append('topics')
        
        # Return top 5 services
        service_list = sorted(list(services))[:5]
        
        if service_list:
            return ', '.join(service_list)
        else:
            return 'General AWS'

    def get_description_enhanced(self, repo: Dict) -> str:
        """Enhanced description with README fallback"""
        # 1. GitHub description
        desc = repo.get('description', '').strip()
        if desc and len(desc) > 10:
            return desc
        
        # 2. README first paragraph
        readme = self.get_readme_content_cached(repo)
        if readme:
            # Extract first meaningful paragraph
            lines = readme.split('\n')
            desc_lines = []
            
            for line in lines:
                line = line.strip()
                # Skip headers, images, badges
                if (line and 
                    not line.startswith('#') and 
                    not line.startswith('!') and
                    not line.startswith('[') and
                    not line.startswith('[![') and
                    len(line) > 20):
                    desc_lines.append(line)
                    if len(' '.join(desc_lines)) > 200:
                        break
                    if len(desc_lines) >= 2:
                        break
            
            if desc_lines:
                return ' '.join(desc_lines)[:300]
        
        # 3. Generate from repository name
        repo_name = repo.get('name', '').replace('-', ' ').replace('_', ' ')
        return f"AWS solution for {repo_name}"

    def classify_repository_enhanced(self, repo: Dict) -> Optional[Dict]:
        """Enhanced repository classification with improved data quality"""
        try:
            # Get enhanced data
            enhanced_description = self.get_description_enhanced(repo)
            enhanced_aws_services = self.get_aws_services_enhanced(repo)
            topics = self.get_repo_topics_cached(repo)
            
            classification = {
                # Basic Info
                "repository": repo["full_name"],
                "url": repo["html_url"],
                "description": enhanced_description,
                "created_date": repo.get("created_at", ""),
                "last_modified": repo["updated_at"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                
                # Enhanced AWS Services
                "aws_services": enhanced_aws_services,
                "topics": ", ".join(topics),
                
                # Business Classification (using enhanced description)
                "solution_type": self.get_solution_type_enhanced(repo, enhanced_description),
                "competency": self.get_competency_enhanced(enhanced_description, enhanced_aws_services),
                "customer_problems": self.get_customer_problems(repo),
                "solution_marketing": self.get_solution_marketing_enhanced(repo, enhanced_description),
                
                # Technical Classification
                "deployment_tools": self.get_deployment_tools(repo["name"]),
                "deployment_level": self.get_deployment_level(repo["name"]),
                "deployment_readiness": self.get_deployment_readiness(repo),
                "primary_language": repo["language"] or "Multiple",
                "secondary_language": self.get_secondary_language(repo),
                "framework": self.get_framework(repo),
                
                # Business Value
                "cost_range": self.get_cost_range(repo),
                "setup_time": self.get_setup_time(repo),
                "business_value": self.get_business_value(repo),
                "target_audience": self.get_target_audience(repo),
                "use_case_category": self.get_use_case_category(repo),
                "integration_complexity": self.get_integration_complexity(repo),
                "maintenance_level": self.get_maintenance_level(repo),
                "scalability": self.get_scalability(repo),
                "usp": self.get_usp(repo),
                "freshness_status": self.get_freshness(repo["updated_at"]),
                "days_since_update": self.get_days_since_update(repo["updated_at"]),
                
                # AI/GenAI
                "genai_agentic": self.is_genai_agentic_enhanced(repo, enhanced_description),
                
                # Metadata
                "classification_method": "Enhanced V2 - Multi-source Analysis",
                "classification_timestamp": datetime.now().isoformat()
            }
            return classification
        except Exception as e:
            print(f"❌ Failed to classify {repo['full_name']}: {e}")
            return None

    def get_solution_type_enhanced(self, repo: Dict, description: str) -> str:
        """Enhanced solution type detection"""
        text = f"{repo.get('name', '')} {description}".lower()
        
        if any(word in text for word in ['starter', 'template', 'boilerplate', 'example']):
            return "Quick Wins"
        elif any(word in text for word in ['security', 'compliance', 'governance']):
            return "Compliance Accelerators"
        elif any(word in text for word in ['ai', 'ml', 'machine learning', 'bedrock', 'sagemaker']):
            return "Innovation Catalysts"
        else:
            return "Foundation Builders"

    def get_competency_enhanced(self, description: str, aws_services: str) -> str:
        """Enhanced competency detection based on AWS services"""
        text = f"{description} {aws_services}".lower()
        
        if any(service in text for service in ['sagemaker', 'bedrock', 'comprehend', 'rekognition']):
            return "AI/ML"
        elif any(service in text for service in ['iam', 'cognito', 'kms', 'waf']):
            return "Security"
        elif any(service in text for service in ['kinesis', 'athena', 'glue', 'redshift']):
            return "Analytics"
        elif any(service in text for service in ['cloudformation', 'cdk', 'codebuild']):
            return "DevOps"
        else:
            return "General Development"

    def get_solution_marketing_enhanced(self, repo: Dict, description: str) -> str:
        """Enhanced solution marketing categorization"""
        text = f"{repo.get('name', '')} {description}".lower()
        
        if any(word in text for word in ['starter', 'template', 'example']):
            return "starter"
        elif any(word in text for word in ['setup', 'bootstrap', 'getting-started']):
            return "setup"
        elif any(word in text for word in ['security', 'compliance']):
            return "compliance"
        elif any(word in text for word in ['monitor', 'observ', 'dashboard']):
            return "visibility"
        else:
            return "foundation"

    def is_genai_agentic_enhanced(self, repo: Dict, description: str) -> str:
        """Enhanced GenAI/Agentic detection"""
        text = f"{repo.get('name', '')} {description}".lower()
        
        if any(word in text for word in ['agent', 'bedrock', 'langchain', 'llm', 'chatbot']):
            return "Yes"
        else:
            return "No"

    def process_top_repositories(self, limit: int = 500, batch_size: int = 5):
        """Process top N repositories by star count"""
        print(f"🚀 Starting Enhanced Classification V2 for top {limit} repositories")
        
        # Load all repositories
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.master_index_key)
            all_repos = json.loads(response['Body'].read())['repositories']
        except Exception as e:
            print(f"❌ Failed to load repositories: {e}")
            return
        
        # Sort by stars and take top N
        top_repos = sorted(all_repos, key=lambda x: x.get('stargazers_count', 0), reverse=True)[:limit]
        
        print(f"📊 Processing top {len(top_repos)} repositories (sorted by stars)")
        print(f"⭐ Star range: {top_repos[0].get('stargazers_count', 0)} to {top_repos[-1].get('stargazers_count', 0)}")
        
        # Process in batches
        results = []
        for i in range(0, len(top_repos), batch_size):
            batch = top_repos[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            print(f"\n📦 Processing batch {batch_num}/{(len(top_repos)-1)//batch_size + 1} (repos {i+1}-{min(i+batch_size, len(top_repos))})")
            
            for repo in batch:
                print(f"  🔍 Analyzing: {repo['full_name']} (⭐{repo.get('stargazers_count', 0)})")
                
                classification = self.classify_repository_enhanced(repo)
                if classification:
                    results.append(classification)
                    print(f"    ✅ AWS Services: {classification['aws_services']}")
                    print(f"    📝 Description: {classification['description'][:100]}...")
                else:
                    print(f"    ❌ Classification failed")
            
            # Save progress every batch
            if results:
                self.save_enhanced_results(results, f"enhanced_top{limit}_batch{batch_num}")
            
            # Rate limiting delay
            time.sleep(2)
        
        print(f"\n🎉 Enhanced classification complete!")
        print(f"✅ Successfully processed: {len(results)}/{len(top_repos)} repositories")
        
        # Save final results
        if results:
            self.save_enhanced_results(results, f"enhanced_top{limit}_final")

    def save_enhanced_results(self, results: List[Dict], filename_suffix: str):
        """Save enhanced results to CSV"""
        if not results:
            return
        
        # Generate CSV content
        headers = list(results[0].keys())
        csv_content = ','.join(headers) + '\n'
        
        for result in results:
            row = []
            for header in headers:
                value = str(result.get(header, '')).replace(',', ';').replace('\n', ' ')
                row.append(f'"{value}"')
            csv_content += ','.join(row) + '\n'
        
        # Save to S3
        csv_key = f'results/{filename_suffix}.csv'
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=csv_key,
                Body=csv_content,
                ContentType='text/csv'
            )
            print(f"💾 Saved results: s3://{self.bucket_name}/{csv_key}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

def main():
    parser = argparse.ArgumentParser(description='Enhanced AWS Repository Classifier V2')
    parser.add_argument('org_name', help='GitHub organization name')
    parser.add_argument('--github-token', help='GitHub personal access token')
    parser.add_argument('--limit', type=int, default=500, help='Number of top repositories to process')
    parser.add_argument('--batch-size', type=int, default=5, help='Batch size for processing')
    
    args = parser.parse_args()
    
    classifier = EnhancedClassifierV2(args.org_name)
    if args.github_token:
        classifier.github_token = args.github_token
        print("🔑 Using GitHub token for higher rate limits")
    
    classifier.process_top_repositories(args.limit, args.batch_size)

if __name__ == "__main__":
    main()
