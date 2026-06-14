# Nextcloud Talk — REST API Quick Reference

Merged from the former `nextcloud-talk` skill.

## Roominfo

- **Name**: Hermes-Lab
- **Token**: `iytt2n7g`
- **ID**: 1
- **Participants**: michel, Hermes, Nova, Apollo (all owners)
- **Type**: 3 = public group

## ⚠️ CRITICAL: API Versions

| Function | API | Path |
|----------|-----|------|
| **Chat send** | **v1** | `.../api/v1/chat/{token}` |
| **Chat receive** | **v1** | `.../api/v1/chat/{token}` |
| **Room management** | **v4** | `.../api/v4/room` |

Chat works ONLY on v1! v2/v3/v4 return 998 "Invalid query".

## API Calls (tested)

### Send message
```bash
curl -u "USER:PASS" \
  -H "OCS-APIRequest: true" \
  -H "Accept: application/json" \
  -X POST \
  -d 'message=TEXT' \
  "http://10.0.60.201:10081/ocs/v2.php/apps/spreed/api/v1/chat/TOKEN?format=json"
```
Response: HTTP 201 = OK

### Receive messages
```bash
curl -u "USER:PASS" \
  -H "OCS-APIRequest: true" \
  -H "Accept: application/json" \
  "http://10.0.60.201:10081/ocs/v2.php/apps/spreed/api/v1/chat/TOKEN?format=json&lookIntoFuture=0&limit=50"
```

- `lookIntoFuture=0` — current messages immediately
- `lookIntoFuture=1` — long-polling (blocks until new message)

### Room list
```bash
curl -s -u "USER:PASS" -H "OCS-APIRequest: true" -H "Accept: application/json" \
  "http://10.0.60.121:8080/ocs/v2.php/apps/spreed/api/v4/room?format=json"
```

## Docker commands
```bash
docker exec code-nextcloud-1 php occ talk:room:list
docker exec code-nextcloud-1 php occ talk:room:delete <TOKEN>
```

## Performance
- Nextcloud PHP is slow — API calls need 30-60s timeout
- Polling: 30s interval recommended

## Key Lessons
1. `Content-Type: application/x-www-form-urlencoded` + `OCS-APIRequest: true` MUST be set
2. JSON body also works for POST chat (Content-Type: application/json)
3. User creation only via `occ user:add` — not via SQL
