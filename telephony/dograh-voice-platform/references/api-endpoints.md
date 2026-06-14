# Dograh API Endpoints (v1.32.0 — 120 total)

Grouped by domain. Base URL: `http://10.0.60.167:8000`

## 🔑 Auth (3)
```
POST   /api/v1/auth/login                Login
GET    /api/v1/auth/me                   Get Current User
POST   /api/v1/auth/signup               Signup
```

## 🧠 Knowledge Base (6)
```
GET    /api/v1/knowledge-base/documents                         List documents
GET    /api/v1/knowledge-base/documents/{document_uuid}         Get document details
DELETE /api/v1/knowledge-base/documents/{document_uuid}         Delete document
POST   /api/v1/knowledge-base/process-document                  Trigger document processing
POST   /api/v1/knowledge-base/search                            Search for similar chunks
POST   /api/v1/knowledge-base/upload-url                        Get presigned URL for document upload
```

## 📦 S3 (3)
```
GET    /api/v1/s3/file-metadata                                 Get file metadata for debugging
POST   /api/v1/s3/presigned-upload-url                          Generate a presigned URL for direct CSV upload
GET    /api/v1/s3/signed-url                                    Generate a signed S3 URL
```

## 🌐 Embed (4)
```
GET    /api/v1/public/embed/config/{token}                      Get Embed Config
OPTIONS /api/v1/public/embed/config/{token}                     Options Config
POST   /api/v1/public/embed/init                                Initialize Embed Session
GET    /api/v1/public/embed/turn-credentials/{session_token}    Get Public TURN Credentials
```

## 🎯 Campaigns (10)
```
GET    /api/v1/campaign/                                        Get Campaigns
POST   /api/v1/campaign/create                                  Create Campaign
GET    /api/v1/campaign/{campaign_id}                           Get Campaign
PATCH  /api/v1/campaign/{campaign_id}                           Update Campaign
POST   /api/v1/campaign/{campaign_id}/pause                     Pause Campaign
GET    /api/v1/campaign/{campaign_id}/progress                  Get Campaign Progress
POST   /api/v1/campaign/{campaign_id}/redial                    Redial Campaign
POST   /api/v1/campaign/{campaign_id}/resume                    Resume Campaign
GET    /api/v1/campaign/{campaign_id}/runs                      Get Campaign Runs
POST   /api/v1/campaign/{campaign_id}/start                     Start Campaign
GET    /api/v1/campaign/{campaign_id}/report                    Download Campaign Report
```

## 📞 Telephony (15+)
```
POST   /api/v1/telephony/initiate-call                          Initiate Call
POST   /api/v1/telephony/inbound/fallback                       Handle Inbound Fallback
POST   /api/v1/telephony/inbound/run                            Handle Inbound Run
POST   /api/v1/telephony/inbound/{workflow_id}                  Handle Inbound Telephony
POST   /api/v1/telephony/cloudonix/cdr                          Handle Cloudonix CDR
POST   /api/v1/telephony/cloudonix/status-callback/{run_id}     Handle Cloudonix Status Callback
POST   /api/v1/telephony/plivo/hangup-callback/{run_id}         Handle Plivo Hangup
POST   /api/v1/telephony/plivo/ring-callback/{run_id}           Handle Plivo Ring
POST   /api/v1/telephony/telnyx/events/{run_id}                 Handle Telnyx Events
POST   /api/v1/telephony/telnyx/transfer-result/{transfer_id}   Handle Telnyx Transfer
POST   /api/v1/telephony/transfer-result/{transfer_id}          Complete Transfer
POST   /api/v1/telephony/twilio/status-callback/{run_id}        Handle Twilio Status
POST   /api/v1/telephony/vobiz/hangup-callback/{workflow_id}    Handle Vobiz Hangup (by workflow)
POST   /api/v1/telephony/vobiz/hangup-callback/{run_id}         Handle Vobiz Hangup (by run)
POST   /api/v1/telephony/vobiz/ring-callback/{run_id}           Handle Vobiz Ring
POST   /api/v1/telephony/vonage/events/{run_id}                 Handle Vonage Events
```

## 📍 Public Agent (6)
```
POST   /api/v1/public/agent/test/{uuid}                         Initiate Call Test
POST   /api/v1/public/agent/test/workflow/{workflow_uuid}       Initiate Call Test by Workflow UUID
POST   /api/v1/public/agent/workflow/{workflow_uuid}            Initiate Call by Workflow UUID
POST   /api/v1/public/agent/{uuid}                              Initiate Call
GET    /api/v1/public/download/workflow/{token}/{artifact_type}  Download Workflow Artifact
```

## 🛠️ Tools (8)
```
GET    /api/v1/tools/                                           List Tools
POST   /api/v1/tools/                                           Create Tool
GET    /api/v1/tools/{tool_uuid}                                Get Tool
PUT    /api/v1/tools/{tool_uuid}                                Update Tool
DELETE /api/v1/tools/{tool_uuid}                                Delete Tool
POST   /api/v1/tools/{tool_uuid}/mcp/refresh                    Refresh MCP Tools
POST   /api/v1/tools/{tool_uuid}/unarchive                      Unarchive Tool
```

## 🧩 Workflows (25+)
```
POST   /api/v1/workflow/create/definition                       Create Workflow
POST   /api/v1/workflow/create/template                         Create Workflow from Template
GET    /api/v1/workflow/fetch                                   Get Workflows
GET    /api/v1/workflow/fetch/{workflow_id}                     Get Workflow
GET    /api/v1/workflow/summary                                 Get Workflows Summary
GET    /api/v1/workflow/templates                               Get Workflow Templates
POST   /api/v1/workflow/templates/duplicate                     Duplicate Template
PUT    /api/v1/workflow/{workflow_id}                           Update Workflow
POST   /api/v1/workflow/{workflow_id}/create-draft              Create Draft
POST   /api/v1/workflow/{workflow_id}/duplicate                 Duplicate
POST   /api/v1/workflow/{workflow_id}/embed-token               Create/Update Embed Token
GET    /api/v1/workflow/{workflow_id}/embed-token               Get Embed Token
DELETE /api/v1/workflow/{workflow_id}/embed-token               Deactivate Embed Token
PUT    /api/v1/workflow/{workflow_id}/folder                    Move to Folder
POST   /api/v1/workflow/{workflow_id}/publish                   Publish
GET    /api/v1/workflow/{workflow_id}/report                    Download Report
POST   /api/v1/workflow/{workflow_id}/runs                      Create Run
GET    /api/v1/workflow/{workflow_id}/runs                      Get Runs
GET    /api/v1/workflow/{workflow_id}/runs/{run_id}             Get Run
PUT    /api/v1/workflow/{workflow_id}/status                    Update Status
POST   /api/v1/workflow/{workflow_id}/validate                  Validate
GET    /api/v1/workflow/{workflow_id}/versions                  Get Versions
GET    /api/v1/workflow/count                                   Get Count
```

## 💬 Text Chat (4)
```
POST   /api/v1/workflow/{id}/text-chat/sessions                 Create Session
GET    /api/v1/workflow/{id}/text-chat/sessions/{run_id}        Get Session
POST   /api/v1/workflow/{id}/text-chat/sessions/{run_id}/messages Append Message
POST   /api/v1/workflow/{id}/text-chat/sessions/{run_id}/rewind Rewind
```

## 🎤 Recordings (6)
```
POST   /api/v1/workflow-recordings/                             Create recording records
GET    /api/v1/workflow-recordings/                             List recordings
POST   /api/v1/workflow-recordings/transcribe                   Transcribe audio file
POST   /api/v1/workflow-recordings/upload-url                   Get presigned upload URLs
PATCH  /api/v1/workflow-recordings/{id}                         Update recording ID
DELETE /api/v1/workflow-recordings/{recording_id}               Delete recording
```

## 🏢 Organizations (20)
```
GET    /api/v1/organizations/campaign-defaults                  Get Campaign Defaults
GET    /api/v1/organizations/langfuse-credentials               Get Langfuse Credentials
POST   /api/v1/organizations/langfuse-credentials               Save Langfuse Credentials
DELETE /api/v1/organizations/langfuse-credentials               Delete Langfuse Credentials
GET    /api/v1/organizations/reports/daily                      Get Daily Report
GET    /api/v1/organizations/reports/daily/runs                 Get Daily Runs Detail
GET    /api/v1/organizations/reports/workflows                  Get Workflow Options
GET    /api/v1/organizations/telephony-config                   Get Config
POST   /api/v1/organizations/telephony-config                   Save Config
GET    /api/v1/organizations/telephony-config-warnings          Get Config Warnings
GET    /api/v1/organizations/telephony-configs                  List Configs
POST   /api/v1/organizations/telephony-configs                  Create Config
GET    /api/v1/organizations/telephony-configs/{config_id}      Get Config By ID
PUT    /api/v1/organizations/telephony-configs/{config_id}      Update Config
DELETE /api/v1/organizations/telephony-configs/{config_id}      Delete Config
GET    /api/v1/organizations/telephony-configs/{config_id}/phone-numbers List Phone Numbers
POST   /api/v1/organizations/telephony-configs/{config_id}/phone-numbers Create Phone Number
GET    /api/v1/organizations/telephony-configs/{config_id}/phone-numbers/{id} Get Phone Number
PUT    /api/v1/organizations/telephony-configs/{config_id}/phone-numbers/{id} Update Phone Number
DELETE /api/v1/organizations/telephony-configs/{config_id}/phone-numbers/{id} Delete Phone Number
POST   /api/v1/organizations/telephony-configs/{config_id}/phone-numbers/{id}/set-default-caller Set Default Caller ID
POST   /api/v1/organizations/telephony-configs/{config_id}/set-default-outbound Set Default Outbound
GET    /api/v1/organizations/telephony-providers/metadata       Get Provider Metadata
GET    /api/v1/organizations/usage/current-period               Get Current Period Usage
GET    /api/v1/organizations/usage/daily-breakdown              Get Daily Usage Breakdown
GET    /api/v1/organizations/usage/runs                         Get Usage History
GET    /api/v1/organizations/usage/runs/report                  Download Usage Runs Report
```

## 👤 User/Config (10+)
```
GET    /api/v1/user/api-keys                                    Get API Keys
POST   /api/v1/user/api-keys                                    Create API Key
DELETE /api/v1/user/api-keys/{api_key_id}                       Archive API Key
PUT    /api/v1/user/api-keys/{api_key_id}/reactivate            Reactivate API Key
GET    /api/v1/user/configurations/defaults                     Get Default Configs
GET    /api/v1/user/configurations/user                         Get User Configs
PUT    /api/v1/user/configurations/user                         Update User Configs
GET    /api/v1/user/configurations/user/validate                Validate Configs
GET    /api/v1/user/configurations/voices/{provider}            Get Voices
GET    /api/v1/user/service-keys                                Get Service Keys
POST   /api/v1/user/service-keys                                Create Service Key
DELETE /api/v1/user/service-keys/{service_key_id}               Archive Service Key
PUT    /api/v1/user/service-keys/{service_key_id}/reactivate    Reactivate Service Key
```

## 🎛️ Misc (5)
```
GET    /api/v1/node-types                                       List Node Types
GET    /api/v1/node-types/{name}                                Get Node Type
GET    /api/v1/folder/                                          List Folders
POST   /api/v1/folder/                                          Create Folder
PUT    /api/v1/folder/{folder_id}                               Rename Folder
DELETE /api/v1/folder/{folder_id}                               Delete Folder
GET    /api/v1/health                                           Health
POST   /api/v1/superuser/impersonate                            Impersonate
GET    /api/v1/superuser/workflow-runs                          Get Workflow Runs
GET    /api/v1/turn/credentials                                 Get TURN Credentials
GET    /api/v1/credentials/                                     List Credentials
POST   /api/v1/credentials/                                     Create Credential
GET    /api/v1/credentials/{credential_uuid}                    Get Credential
PUT    /api/v1/credentials/{credential_uuid}                    Update Credential
DELETE /api/v1/credentials/{credential_uuid}                    Delete Credential
```

## Key Usage Patterns

### Login (JWT)
```bash
TOKEN=$(curl -s -X POST /api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"...","password":"..."}' | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])")
```

### Initiate Call
```bash
curl -s -X POST /api/v1/telephony/initiate-call \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"workflow_id":"...","to_number":"+41...","from_number":"0796459743"}'
```

### Create Workflow
```bash
curl -s -X POST /api/v1/workflow/create/definition \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"My Bot","description":"...","type":"outbound"}'
```
