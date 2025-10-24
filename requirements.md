# AWS GitHub Repository Classification System - Requirements

## Overview
A comprehensive classification system for AWS official GitHub repositories (aws, awslabs, aws-samples, etc.) to enable intelligent filtering, categorization, and sales enablement for solution packaging.

## Classification Dimensions

### 1. Date Filters
**Purpose**: Track repository freshness and activity
- **Repository Created Date**: When the repo was first created
- **Last Modified Date**: When it was last pushed to or updated
- **Implementation**: GitHub API fields `created_at` and `pushed_at`

### 2. Solution Types (Customer-Facing Sales Categories)
**Purpose**: Map repositories to customer buying patterns and sales cycles

1. **Quick Wins** (30-90 days)
   - Cost optimization audits, security assessments, performance monitoring
   - Sales angle: Fast ROI, low risk, builds trust

2. **Foundation Builders** (3-6 months)
   - Landing zone setup, multi-account governance, CI/CD pipelines
   - Sales angle: Strategic infrastructure, enables future growth

3. **Compliance Accelerators** (1-3 months)
   - SOC2/HIPAA/PCI frameworks, security baselines, audit automation
   - Sales angle: Risk mitigation, regulatory requirements

4. **Migration Enablers** (6-12 months)
   - Cloud migration frameworks, application modernization, database migration
   - Sales angle: Digital transformation, competitive advantage

5. **Innovation Catalysts** (3-9 months)
   - ML/AI frameworks, serverless templates, data analytics platforms
   - Sales angle: Business differentiation, new revenue streams

6. **Operational Excellence** (Ongoing)
   - Monitoring, cost management, performance optimization, incident response
   - Sales angle: Operational efficiency, reduced overhead

### 3. AWS Partner Network (APN) Competencies
**Purpose**: Map repositories to AWS partner expertise areas

#### Technical Competencies:
1. Migration
2. Modern Application Development
3. Data & Analytics
4. Machine Learning
5. IoT
6. Security
7. Networking
8. Storage
9. DevOps
10. Database

#### Solution Competencies (Industry Verticals):
1. Financial Services
2. Healthcare & Life Sciences
3. Government
4. Education
5. Retail & eCommerce
6. Manufacturing
7. Media & Entertainment
8. Energy & Utilities
9. Automotive
10. Travel & Hospitality

**Note**: Repositories can map to multiple competencies with confidence scoring

### 4. Deployment Readiness
**Purpose**: Identify out-of-the-box deployment tools supported

#### Build Tools:
- Make (Makefile presence)
- npm/yarn (package.json)
- Maven/Gradle (Java build tools)
- Docker (Dockerfile, docker-compose)

#### AWS Deployment Tools:
- CodeDeploy (appspec.yml)
- CloudFormation (.yaml/.json templates)
- SAM (template.yaml, sam commands)
- CDK (cdk.json, CDK code files)
- Terraform (.tf files)
- Serverless Framework (serverless.yml)

#### Readiness Levels:
- **Production-Ready**: Complete deployment documentation
- **Basic Setup**: Has files but minimal docs
- **Development Only**: No deployment instructions

### 5. Programming Languages
**Purpose**: Identify primary and secondary programming languages used
- Detection via GitHub API language statistics
- Include both programming and configuration languages
- Support multi-language repositories with primary/secondary classification

### 6. Frameworks Used
**Purpose**: Identify technical frameworks and libraries
- Web frameworks (React, Angular, Django, Flask)
- Cloud frameworks (CDK, Serverless Framework)
- Detection via package files and code analysis
- Support multiple frameworks per repository

### 7. AWS Services Used
**Purpose**: Identify AWS services utilized by the solution
- Service level detection (S3, Lambda, RDS, etc.)
- Detection sources: Code imports, CloudFormation resources, documentation
- Support multiple services with primary/secondary classification
- Group by service categories (Compute, Storage, Database, etc.)

### 8. Prerequisites
**Purpose**: Identify AWS account and technical prerequisites

#### AWS Account Prerequisites:
- Identity Center (IDC) enabled
- Organizations enabled
- Trusted Advisor enabled (Business/Enterprise support)
- Security Hub enabled
- Config enabled
- CloudTrail enabled
- GuardDuty enabled
- Control Tower enabled

#### Technical Prerequisites:
- VPC setup
- IAM roles/policies
- KMS keys
- Route 53
- Certificate Manager
- Third-party licenses

### 9. License & Copyright
**Purpose**: Legal compliance and commercial use assessment

#### License Types:
- Open Source (MIT, Apache 2.0, BSD, GPL, etc.)
- Proprietary/Commercial
- No License/All Rights Reserved

#### Copyright Information:
- Copyright holders (AWS, individuals, third parties)
- Copyright years and currency
- Commercial use permissions
- Modification rights
- Attribution requirements

### 10. Implementation Time & Running Costs
**Purpose**: Customer planning and budget assessment

#### Setup Time Categories:
- Quick Setup (< 1 hour)
- Half-day Setup (1-4 hours)
- Full-day Setup (4-8 hours)
- Multi-day Setup (1-5 days)
- Project-level (1+ weeks)

#### Cost Categories:
- Minimal (< $10/month)
- Low ($10-100/month)
- Medium ($100-1000/month)
- High ($1000+/month)

### 11. Customer Problems Solved
**Purpose**: Map to customer pain points for sales conversations

#### Business Problems:
- Cost Management (high bills, resource waste)
- Security & Compliance (breaches, regulatory requirements)
- Performance & Reliability (downtime, scalability)
- Operational Efficiency (manual processes, automation gaps)

#### Technical Problems:
- Migration Challenges (legacy modernization)
- Development Velocity (slow deployments)
- Data & Analytics (silos, insights gaps)

### 12. Unique Selling Points (USP)
**Purpose**: Competitive differentiation and sales messaging

#### Differentiation Categories:
- Speed/Time Advantage
- Cost Advantage
- Technical Innovation
- AWS-Native Benefits
- Ease of Use
- Enterprise Features
- Proven Track Record

### 13. Repository Freshness
**Purpose**: Solution viability and maintenance status assessment

#### Freshness Categories:
- **Active** (< 3 months): High confidence, regular updates
- **Maintained** (3-12 months): Medium confidence, occasional updates
- **Stale** (1-2 years): Low confidence, minimal activity
- **Abandoned** (> 2 years): Avoid, no maintenance
- **Legacy/Archived**: Historical reference only

#### Activity Indicators:
- Last commit date
- Last release date
- Issue activity (open/closed rates)
- Pull request activity
- Maintainer responsiveness
- Dependency currency

## Implementation Strategy

### Data Sources
1. **GitHub API**: Repository metadata, languages, topics, activity
2. **Repository Files**: README, LICENSE, configuration files
3. **Documentation Analysis**: Setup instructions, prerequisites, use cases
4. **Code Analysis**: Imports, dependencies, infrastructure definitions

### Classification Approach
1. **Automated Detection**: Keyword matching, file pattern recognition
2. **Confidence Scoring**: Multiple indicators with weighted scoring
3. **Multi-dimensional Mapping**: Repositories can belong to multiple categories
4. **Manual Override**: Allow corrections and refinements

### Output Format
```json
{
  "repository": "aws-samples/example-repo",
  "classifications": {
    "dates": {
      "created": "2023-01-15",
      "last_modified": "2024-10-20"
    },
    "solution_type": {
      "primary": "Quick Wins",
      "confidence": 0.85
    },
    "apn_competencies": {
      "technical": ["Security", "DevOps"],
      "solution": ["Financial Services"],
      "confidence": [0.90, 0.75, 0.65]
    },
    "deployment_readiness": {
      "tools": ["CDK", "CloudFormation"],
      "level": "Production-Ready"
    },
    "languages": ["Python", "TypeScript"],
    "frameworks": ["CDK", "Flask"],
    "aws_services": ["Lambda", "S3", "DynamoDB"],
    "prerequisites": ["IAM", "VPC"],
    "license": {
      "type": "Apache License 2.0",
      "commercial_use": true
    },
    "implementation": {
      "time": "Half-day Setup",
      "cost": "Low ($10-100/month)"
    },
    "problems_solved": ["Security & Compliance", "Operational Efficiency"],
    "usp": "Zero-downtime deployment with automated rollback",
    "freshness": {
      "status": "Active",
      "last_activity": "2024-10-20",
      "confidence": "High"
    }
  }
}
```

## Success Criteria
1. **Accuracy**: >85% classification accuracy across all dimensions
2. **Coverage**: Process all repositories from target AWS organizations
3. **Performance**: Classify 1000+ repositories within reasonable time
4. **Usability**: Enable effective filtering and discovery for sales teams
5. **Maintainability**: Support ongoing updates as repositories evolve

## Future Enhancements
- Machine learning models for improved classification accuracy
- Real-time updates via GitHub webhooks
- Integration with AWS Partner Portal
- Customer feedback loop for classification refinement
- Analytics dashboard for repository trends and insights
