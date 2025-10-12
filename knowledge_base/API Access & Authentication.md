
# API Access & Authentication

## Credentials

Before you can start using the API, you need credentials for the authentication. Each API call requires a client, user and password.
If you do not have your own client yet, you can use the following credentials to test the API:

### Test Credentials

- **Client**: `APITEST`
- **User**: `API_TEST`
- **Password**: `API_TEST_007`

The client "APITEST" is intended for basic connectivity testing and is used by different users. Don't use it with sensitive data. For real tests and productive usage you will have to use the credentials that you receive from AEB employees.

In case you have a dedicated client for your Trade Compliance Management web service, you should use a client-specific API-user that should either be created by AEB or by your TCM administrator.

## Base URL

To access the REST or SOAP webservices, you will need a base URL as an entry point to the AEB Compliance Screening API. Your company will be assigned a base URL when signing a contract with AEB. For our API test environment, the base URL (endpoints) is as follows:

- **REST**:	https://rz3.aeb.de/test4ce/rest
- **SOAP**:	https://rz3.aeb.de:443/test4ce/servlet/bf

The API is only available via HTTPS.

## Authentication

Depending on the technology (REST or SOAP) different authentication methods could be used:

### 1. HTTP Basic Authentication

This can be used with REST and SOAP and requires authentication data to be provided with each call.

### 2. Token Authentication

This can only be used with REST and requires an additional call to request a token, that can then be used for subsequent calls for a limited time.

### HTTP Basic Authentication

With this method, authentication data must be provided for every API call. It works for REST and SOAP. It is expected as HTTP authentication (HTTP Basic Authentication according to RFC 2617).The user and client login data is transmitted in the format user@client:password. The login data must be base 64–encoded. Before the conversion, the login data should use ISO-8859-1 character coding. If no umlauts or other diacritics are included, this corresponds to ASCII coding. It is also possible to use Windows character coding (CP-1252) if no euro sign is included.


Base 64 encoding is no encryption in cryptographic terms, but still plain text. This is why we require using HTTPS encryption so the data cannot be intercepted by unauthorized parties. Example for the coding of login data:

- **User** : `API_TEST`
- **Client** : `APITEST`
- **Password** : `API_TEST_007`

The string `API_TEST@APITEST:API_TEST_007`, when encoded in base 64, yields “QVBJX1RFU1RAQVBJVEVTVDpBUElfVEVTVF8wMDc=". The following line would therefore be added to the HTTP header:

Authorization: Basic QVBJX1RFU1RAQVBJVEVTVDpBUElfVEVTVF8wMDc=

#### Token Authentication

This method works for REST only. First you have to request an authentication token by using the URL https://rz3.aeb.de/test4ce/rest/logon/user:

```json
{
 	"clientName": "APITEST",
 	"userName": "API_TEST",
 	"password": "API_TEST_007",
 	"localeName": "en",
 	"isExternalLogon": "true"
}
```

You will then get a token back, which you have to use as request header in subsequent requests

(the header is X-XNSG_WEB_TOKEN). The token is valid for a maximum of twelve hours and can be reused for several calls. A good approach is to request a new token every hour or/and if an authentication error is given (e.g. token is expired or not valid anymore after application restart). Each following request should then contain the retrieved token in the request header:

```
POST /test4ce/rest/ComplianceFoundation/getMasterdataIdentifiers HTTP/1.1

Host: rz3.aeb.de
Connection: keep-alive
accept: application/json

...

X-XNSG_WEB_TOKEN: eyJlbmdpbmVJZCI6IjUwMzE2OTEwNF9XbVZ3VGV4YWVGIiwiaWQiOiJVU0VSX0NMSUVOVCJ9.eyJ1c2VyTmFtZSI6IldTTSIsImNsaWVudElkZW50Q29kZSI6IlVOSVRFREIifQ==.AwgakGOMN0IRJo6cGkVS1DXpbGOozG7o8vQD3DEalYb2oE0qRUmifyh9vfms1NWeMwTJUpelRo9fLy5eSm92k+vull2q3GJfhkVT7Oqa9HUobIZFSDVPL4z5++ovnemuyuz2qZdTXHP6qPepk+DV2WTitam0zgNGAJidGBUK/Q4=
```



### API Test Possibilities

The following website explains the REST API, including all fields:
https://trade-compliance.docs.developers.aeb.com/reference/screenaddresses-1

You can also manually click together your example field by field on this website and view both the request and the response.

