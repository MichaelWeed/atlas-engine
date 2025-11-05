# Getting Started with JWT Setup for Salesforce Integration from AWS Lambda

This guide provides a straightforward introduction to setting up JSON Web Token (JWT) authentication for connecting an AWS Lambda function to your Salesforce org. JWT enables secure, server-to-server communication without user interaction, ideal for automating tasks like finding, creating, updating, or deleting Leads or Cases.

**Key Assumptions:**
- You have admin access to your Salesforce org (e.g., Enterprise Edition or higher).
- You're familiar with basic AWS concepts; we'll focus on the Salesforce side here.
- This setup uses the OAuth 2.0 JWT Bearer Token Flow for secure access.
- You'll need a digital certificate (e.g., self-signed) for signing JWTs—generate one using tools like OpenSSL if you don't have it (e.g., `openssl req -x509 -nodes -newkey rsa:2048 -keyout server.key -out server.crt -days 365`).

This isn't a complete end-to-end tutorial. For full details, refer to Salesforce's official documentation on [Connected Apps](https://help.salesforce.com/s/articleView?id=xcloud.connected_app_create_basics.htm&type=5) and [JWT Authorization](https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_auth_connected_app.htm). Once set up, implement the JWT generation and API calls in your Lambda code (e.g., using Node.js or Python libraries like `jsforce` or `simple-salesforce`).

## Step 1: Enable Connected App Creation in Salesforce

Before creating the app, ensure your org allows it.

1. Log in to your Salesforce org as an admin.
2. Go to **Setup** (gear icon in the top right).
3. In the Quick Find box, search for "External Client Apps" and select **External Client App Settings**.
4. Turn on **Allow creation of connected apps**.
5. Save changes if prompted.

**Permissions Needed:** You need "Customize Application" plus "Modify All Data" or "Manage Connected Apps". If you lack these, contact your Salesforce admin.

## Step 2: Create a New Connected App

A Connected App defines how your AWS Lambda will authenticate with Salesforce.

1. In Setup, Quick Find for "App Manager" and select **App Manager**.
2. Click **New Connected App**.
3. Fill in the basics:
   - **Connected App Name:** Something descriptive, e.g., "AWS Lambda Salesforce Integration".
   - **API Name:** Auto-fills; edit if needed (letters, numbers, underscores only).
   - **Contact Email:** Your email or a support team's for Salesforce to reach you.
   - **Contact Phone:** Optional, but add for support.
   - **Logo Image URL:** Optional; upload a small image (GIF/JPG/PNG, <100KB) via "Upload logo image" for branding.
   - **Description:** Brief note, e.g., "Enables AWS Lambda to manage Leads and Cases via API".
4. Under **API (Enable OAuth Settings)**, check **Enable OAuth Settings**.
5. **Callback URL:** Enter a placeholder like `http://localhost:1717/OauthRedirect` (not used in JWT flow, but required).
6. **Use digital signatures:** Check this (critical for JWT).
7. Upload your digital certificate (e.g., `server.crt`) via "Choose File".
8. Add OAuth Scopes (permissions for your Lambda):
   - Manage user data via APIs (`api`).
   - Manage user data via Web browsers (`web`).
   - Perform requests at any time (`refresh_token, offline_access`).
   Move these to the Selected OAuth Scopes list.
9. Click **Save**, then **Continue**.

After saving, note the **Consumer Key** (Client ID) and **Consumer Secret** (Client Secret)—you'll need them in your Lambda code. Click **Manage Consumer Details** to copy them (verify your identity if prompted).

## Step 3: Configure Policies and Access

Set policies to secure the app and pre-authorize users.

1. From the Connected App detail page, click **Manage**.
2. Click **Edit Policies**.
3. Under **OAuth Policies**:
   - **Permitted Users:** Select "Admin approved users are pre-authorized".
   - **Refresh Token Policy:** Set to expire after 90 days or less (e.g., "Expire refresh token after: 90 days") for security.
4. Under **Session Policies**, set **Timeout Value** to 15 minutes (access tokens expire quickly; refresh tokens handle renewal).
5. Save changes.
6. Click **Manage Profiles** and select profiles (e.g., System Administrator) allowed to use this app.
7. Click **Manage Permission Sets** and assign or create sets with needed permissions (e.g., API access to Leads and Cases).

For the JWT flow, optionally enable **Client Credentials Flow** if blending flows, but it's not required for pure JWT. If enabling:
- Under API settings, check **Enable Client Credentials Flow**.
- Accept the security warning.
- Set a "Run As" user (e.g., an API-only user) under Client Credentials Flow.

## Step 4: Test and Integrate with AWS Lambda

With the Connected App ready:

1. In your AWS Lambda function:
   - Use the Consumer Key, private key (from your certificate), and Salesforce username (e.g., integration user).
   - Generate a JWT assertion signed with your private key.
   - Exchange it for an access token via Salesforce's `/services/oauth2/token` endpoint.
   - Use the token to call Salesforce APIs (e.g., `/services/data/vXX.0/sobjects/Lead` for CRUD).

Example Python snippet (using `simple-salesforce` library—install via Lambda layers):
```python
import jwt
from simple_salesforce import Salesforce

# Your details
private_key = '''-----BEGIN PRIVATE KEY-----...-----END PRIVATE KEY-----'''
consumer_key = 'YOUR_CONSUMER_KEY'
username = 'integration@user.com'
login_url = 'https://login.salesforce.com'  # or test.salesforce.com for sandbox

# Generate JWT
claims = {
    'iss': consumer_key,
    'sub': username,
    'aud': login_url,
    'exp': int(time.time()) + 300  # 5 min expiration
}
assertion = jwt.encode(claims, private_key, algorithm='RS256')

# Get access token
sf = Salesforce(username=username, consumer_key=consumer_key, privatekey=assertion, domain='login')  # Adjust domain as needed

# Example: Query Leads
leads = sf.query("SELECT Id, Name FROM Lead LIMIT 10")
print(leads)
```

**Pitfalls to Avoid:**
- Certificate mismatches: Ensure the uploaded cert matches your private key.
- Permissions: The "Run As" or integration user must have CRUD access to Leads/Cases.
- Token expiration: Handle refresh logic in code.
- Security: Rotate Consumer Secret periodically; store keys securely in AWS Secrets Manager.
- Rate limits: Salesforce APIs have limits—monitor usage.

If issues arise (e.g., invalid token), check Salesforce logs or debug your JWT claims. For advanced setups, consult Salesforce devs or AWS docs on Lambda integrations. This should point you in the right direction—iterate as needed.