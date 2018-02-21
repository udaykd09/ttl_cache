# ttl_cache
A key value store with time to live, using Flask (web application)

**Add** key value: POST /v1/keys

Request body:

    {
    "key": "k",
    "value": "v",
    "lifeTime": 1
    }
    
NOTE : "lifeTime" is minutes

**Get** key value: GET /v1/keys/<key>

Response body:

    {
        "Message": "Found key value",
        "Data": {
            "k": {
                "lifeTime": 1,
                "value": "v",
                "key": "k",
                "createTime": 1519175431.230737
            }
        },
        "StatusCode": 200
    }
    
**Update** key value: PUT /v1/keys/<key>
    
**Delete** key value: DELETE /v1/keys/<key>

**Get** all key value: GET /v1/keys


**Expiration thread:** 

Randomly picks 25% of keys in keys_to_expire set and checks their lifetime

**Start Expiration thread**: PUT /v1/expire/start

**Stop Expiration thread**: PUT /v1/expire/stop