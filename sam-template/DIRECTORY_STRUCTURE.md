# Atlas Engine - SAM Project Directory Structure

## 📁 Recommended Structure

```
atlas-engine/
│
├── sam-template/
│   ├── template.yaml                    # Main SAM template
│   ├── samconfig.toml                   # SAM CLI configuration
│   ├── README.md                        # Deployment guide
│   └── DIRECTORY_STRUCTURE.md           # This file
│
├── lambda/                              # Lambda function source code
│   ├── CreateLeadHandler_code/
│   │   ├── lambda_function.py           # Main handler
│   │   ├── requirements.txt             # Python dependencies
│   │   └── tests/                       # Unit tests
│   │       └── test_handler.py
│   │
│   ├── GenerateDynamicScenarioHandler_code/
│   │   ├── lambda_function.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │
│   ├── InvokeOutboundCallHandler_code/
│   │   ├── lambda_function.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │
│   ├── LexFulfillmentHandler_code/
│   │   ├── lambda_function.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │
│   └── UpdateLeadHandler_code/
│       ├── lambda_function.py
│       ├── requirements.txt
│       └── tests/
│
├── layers/                              # Lambda layers
│   ├── python-libraries/
│   │   ├── python/                      # Layer content (auto-created)
│   │   │   └── lib/
│   │   │       └── python3.13/
│   │   │           └── site-packages/
│   │   ├── requirements.txt             # Layer dependencies
│   │   └── build.sh                     # Build script
│   │
│   └── salesforce-libraries/
│       ├── python/
│       ├── requirements.txt
│       └── build.sh
│
├── stepfunctions/                       # Step Functions definitions
│   ├── workflow-definition.asl.json     # State machine definition
│   └── README.md                        # Workflow documentation
│
├── events/                              # Test events for local testing
│   ├── create-lead-event.json
│   ├── lex-event.json
│   └── step-functions-event.json
│
├── tests/                               # Integration tests
│   ├── integration/
│   │   ├── test_workflow.py
│   │   └── test_lex_integration.py
│   └── unit/
│       └── test_helpers.py
│
├── scripts/                             # Utility scripts
│   ├── deploy.sh                        # Deployment script
│   ├── setup-secrets.sh                 # Secret setup script
│   ├── build-layers.sh                  # Layer build script
│   └── cleanup.sh                       # Cleanup script
│
├── docs/                                # Documentation
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── API.md
│   └── TROUBLESHOOTING.md
│
├── .github/                             # GitHub workflows
│   └── workflows/
│       ├── deploy-dev.yml
│       ├── deploy-prod.yml
│       └── test.yml
│
├── .gitignore                           # Git ignore file
├── LICENSE                              # License file
├── README.md                            # Project README
└── CHANGELOG.md                         # Version history
```

## 📝 File Descriptions

### Root Level

- **sam-template/** - SAM templates and configuration
- **lambda/** - All Lambda function source code
- **layers/** - Shared Lambda layers
- **stepfunctions/** - Step Functions state machine definitions
- **events/** - Sample events for testing
- **tests/** - Test suites
- **scripts/** - Automation scripts
- **docs/** - Project documentation

### Lambda Functions

Each Lambda function directory should contain:
- `lambda_function.py` - Main handler code
- `requirements.txt` - Python dependencies
- `tests/` - Unit tests for the function
- `README.md` (optional) - Function-specific documentation

### Lambda Layers

Each layer directory should contain:
- `python/` - Layer content (created during build)
- `requirements.txt` - Dependencies to install
- `build.sh` - Script to build the layer

### Step Functions

- `workflow-definition.asl.json` - State machine definition in ASL format
- Use `DefinitionSubstitutions` in SAM template for dynamic ARNs

## 🔨 Build Scripts

### layers/python-libraries/build.sh

```bash
#!/bin/bash
set -e

LAYER_DIR="python"
rm -rf $LAYER_DIR
mkdir -p $LAYER_DIR

pip install -r requirements.txt -t $LAYER_DIR/
```

### layers/salesforce-libraries/build.sh

```bash
#!/bin/bash
set -e

LAYER_DIR="python"
rm -rf $LAYER_DIR
mkdir -p $LAYER_DIR

pip install simple-salesforce PyJWT -t $LAYER_DIR/
```

## 🧪 Test Event Examples

### events/create-lead-event.json

```json
{
  "firstName": "John",
  "lastName": "Doe",
  "phone": "+15555551234"
}
```

### events/lex-event.json

```json
{
  "sessionState": {
    "intent": {
      "name": "ScheduleCallIntent",
      "slots": {
        "FullName": {"value": {"interpretedValue": "John Doe"}},
        "PhoneNumber": {"value": {"interpretedValue": "+15555551234"}}
      }
    }
  },
  "inputTranscript": "I want to schedule a call"
}
```

## 🚀 Deployment Scripts

### scripts/deploy.sh

```bash
#!/bin/bash
set -e

ENV=${1:-dev}

echo "Building application..."
sam build --parallel

echo "Deploying to $ENV..."
sam deploy --config-env $ENV --no-confirm-changeset

echo "Deployment complete!"
```

### scripts/build-layers.sh

```bash
#!/bin/bash
set -e

echo "Building Lambda layers..."

cd layers/python-libraries
bash build.sh
cd ../..

cd layers/salesforce-libraries
bash build.sh
cd ../..

echo "Layers built successfully!"
```

## 📦 .gitignore

```
# SAM
.aws-sam/
samconfig.toml.bak
packaged.yaml

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/

# Lambda Layers
layers/*/python/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Secrets
*.pem
*.key
secrets.json
salesforce-creds.json

# Logs
*.log

# Build artifacts
*.zip
build/
dist/
```

## 🔄 Migration from Current Structure

### Step 1: Reorganize Files

```bash
# Create new structure
mkdir -p atlas-engine-sam/{lambda,layers,stepfunctions,events,tests,scripts,docs}

# Copy Lambda functions
cp -r lambda/*_code atlas-engine-sam/lambda/

# Create layer directories
mkdir -p atlas-engine-sam/layers/{python-libraries,salesforce-libraries}

# Copy Step Functions definition
cp stepfunctions/AtlasEngineWorkflow.json atlas-engine-sam/stepfunctions/workflow-definition.asl.json
```

### Step 2: Create Layer Requirements

```bash
# Python libraries layer
cat > atlas-engine-sam/layers/python-libraries/requirements.txt << EOF
requests==2.31.0
phonenumbers==8.13.0
wrapt==1.16.0
EOF

# Salesforce libraries layer
cat > atlas-engine-sam/layers/salesforce-libraries/requirements.txt << EOF
simple-salesforce==1.12.0
PyJWT==2.8.0
cryptography==41.0.0
EOF
```

### Step 3: Build Layers

```bash
cd atlas-engine-sam/layers/python-libraries
pip install -r requirements.txt -t python/
cd ../../..

cd atlas-engine-sam/layers/salesforce-libraries
pip install -r requirements.txt -t python/
cd ../../..
```

### Step 4: Deploy

```bash
cd atlas-engine-sam/sam-template
sam build
sam deploy --guided
```

## 📊 Size Considerations

### Lambda Function Sizes
- CreateLeadHandler: ~2 KB (code only)
- GenerateDynamicScenarioHandler: ~3 KB
- LexFulfillmentHandler: ~8 KB
- Total: ~20 KB (without layers)

### Lambda Layer Sizes
- python-libraries: ~3 MB
- salesforce-libraries: ~14 MB
- Total: ~17 MB

### Deployment Package
- Total deployment size: ~17 MB
- Well within Lambda limits (250 MB unzipped)

## 🎯 Best Practices

1. **Keep functions small** - Use layers for shared dependencies
2. **Separate concerns** - One function per responsibility
3. **Version layers** - Use semantic versioning
4. **Test locally** - Use `sam local` before deploying
5. **Use parameters** - Make templates reusable
6. **Document everything** - README in each directory
7. **Automate builds** - Use CI/CD pipelines
8. **Monitor costs** - Tag all resources

## 🔗 Related Files

- [Main SAM Template](template.yaml)
- [SAM Configuration](samconfig.toml)
- [Deployment Guide](README.md)
- [Architecture Documentation](../DEPLOYMENT_ARCHITECTURE.md)
