# n8n Execution Error Inspection (Compressed Data Format)

n8n compresses execution data as a JSON array with string interning. Direct `.data.data` is a JSON string. Parse it:

```python
import json

# Get /rest/executions/{ID}?includeData=true
exec_data = d.get('data', {})
raw_data = exec_data.get('data')
if isinstance(raw_data, str):
    raw = json.loads(raw_data)
```

## Array Index Reference

| Index | Content |
|-------|---------|
| 0 | Header (version, startData/resultData/executionData/resumeToken → indices) |
| 1 | startData (often empty `{}`) |
| 2 | resultData: {error→N, runData→N, lastNodeExecuted→N} |
| 3 | executionData: {contextData→N, nodeExecutionStack→N, metadata→N} |
| 4 | Resume token string (opaque) |
| 5 | Error object: {level→N, tags→N, description→N, timestamp, context→N, ...} |
| 6 | runData: dict of {node_name: list_of_execution_entries} |
| 7 | lastNodeExecuted (string: node name) |
| 8-35+ | String interning entries (dereferenced by numeric indices) |

## Node Parameters

Find node parameters in `raw[35]` (or scan for dict with `method`, `url`, `contentType` keys):

```python
for i, item in enumerate(raw):
    if isinstance(item, dict) and 'contentType' in item and 'url' in item:
        params = item  # this is the node's parameters dict
        # Dereference string values
        for k, v in params.items():
            if isinstance(v, str) and v.isdigit() and int(v) < len(raw):
                params[k] = raw[int(v)]
```

## Error Context (The Actual HTTP Request)

```python
result_idx = int(raw[0]['resultData'])
result = raw[result_idx]                       # index 2
err_idx = int(result['error'])
err_obj = raw[err_idx]                         # index 5 (error object)
context_ref = err_obj.get('context')           # points to context data
```

The error context contains the failed HTTP request:

```python
err_obj = raw[5]                               # error object
context = raw[int(err_obj['context'])]
request = raw[int(context['request'])]         # {body→N, headers→N, method→N, uri→N, ...}
body = raw[int(request['body'])]               # dict of form fields
headers = raw[int(request['headers'])]         # dict of headers
method = raw[int(request['method'])]            # "POST"
uri = raw[int(request['uri'])]                  # "http://..."
```

## Common Error Patterns

| HTTP Code | Likely Cause |
|-----------|-------------|
| 422 | contentType mismatch — n8n sends JSON but API expects form-urlencoded (or vice versa) |
| 401 | Token expired, authentication missing, or Bearer token not forwarded |
| 404 | URL wrong, webhook not registered yet, or node ID mismatch |

The 422 error's detail field lists which body fields are missing. If it says `"field required"` for `username`/`password`, the body format is wrong — check the request body + headers in the context to see what n8n actually sent.

## Workflow ID from Execution

```python
execution_data = d.get('data', {})
print(f"Workflow: {execution_data.get('workflowId')}")
```

The `workflowId` filter on `/rest/executions` may not filter correctly (n8n bug). Always verify the workflow ID from the individual execution rather than trusting the filtered list.
