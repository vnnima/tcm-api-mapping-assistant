### Find Matching Adresses

Trade Compliance Management offers REST API findMatchingAddresses (or SOAP API RexBF-getMatchingAddresses)**.** This request finds all restricted party addresses matching a given address.

In most cases, this request is used for handling matches found via Bulk address Screening . It is used to display matching restricted party addresses of a checked address to the user in the partner system who needs to decide if the addresses found are real matches or not. This API is only needed if you plan to implement the Match handling directly from your software. Please check the API for defining a Good Guy as well.

Example Request:

```
curl --request POST \
    --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/findMatchingAddresses \
    --header 'accept: application/json' \
    --header 'content-type: application/json' \
    --data '
{
  "address": {
    "addressType": "entity",
    "name": "Abu Ahmed Group Inc. Factory for sweets of all kind",
    "street": "Fuller street 5",
    "pc": "MK7 6AJ",
    "city": "Manchester",
    "district": "North",
    "countryISO": "GB",
    "telNo": "+4413859-489548",
    "postbox": "12345",
    "pcPostbox": "MK7 6AJ",
    "cityPostbox": "Manchester",
    "email": "abu.ahmed@google.com",
    "fax": "+4413859-4895497",
    "name1": "Abu Ahmed",
    "name2": "Group Inc.",
    "name3": "Factory for sweets of all kind",
    "referenceId": "CUS\_4711",
    "referenceComment": "Customer 4711",
    "condition": {
      "value": "CUS\_4711",
      "description": "Customer 471"
    }
  },
  "screeningParameters": {
    "suppressLogging": true,
    "addressTypeVersion": "1",
    "clientIdentCode": "APITEST",
    "clientSystemId": "Oracle Cloud ERP",
    "profileIdentCode": "DEFAULT",
    "userIdentification": "Oracle User 0815"
  }
}
```
Example Response:

```
[
  {
    "addressType": "entity",
    "name": "Abu Ahmed Group Inc. Factory for sweets of all kind",
    "street": "Fuller street 5",
    "pc": "MK7 6AJ",
    "city": "Manchester",
    "district": "North",
    "countryISO": "GB",
    "telNo": "+4413859-489548",
    "postbox": "12345",
    "pcPostbox": "MK7 6AJ",
    "cityPostbox": "Manchester",
    "email": "abu.ahmed@google.com",
    "fax": "+4413859-4895497",
    "name1": "Abu Ahmed",
    "name2": "Group Inc.",
    "name3": "Factory for sweets of all kind",
    "similarity": 85,
    "listAbbreviation": "FRNL",
    "listName": "UK - Consolidated List of Financial Sanctions Targets in the UK",
    "listGroupName": "BOE",
    "internalAddressId": "12345678901234567890",
    "restrictionType": "EU-CR",
    "restrictionSource": "Terrorism and Terrorist Financing",
    "restrictionDate": "2020-09-16T15:00:25.566Z",
    "sourceWebLink": "www.youm7.com/story/2017/6/9/",
    "hasMoreDetails": true,
    "matchType": "ADDRESS\_AND\_NAME",
    "embargoArea": "someAreaName"
  }
]
```

### Embedding the AEB GUI into your software - Open the match handling of a specific address match

Besides business facades (BF), which allow the use of Compliance Screening functionality in your own program code, the AEB Compliance Screening API also offers application facades (AF) to embed the GUI of Compliance Screening in your own software.

An application facade call is technically a normal API call - the authentication process is the same, request parameters are transmitted as HTTP body. But an application facade returns a link in the response, which the caller of the application facade can open in a new browser window or in an embedded frame of the web application, so the desired application of Compliance Screening opens for the user.

There are several application facades available which can be found here: https://trade-compliance.docs.developers.aeb.com/reference/screeninglogentry-1.

The API screeningLogEntry can be used to open the match handling for one critical address e.g. one specific business partner. Integrating this API is useful if the response from the screenAddresses API is evaluated in the partner system and the user is shown the compliance block reason additional to a standard block status. This allows a compliance officer to jump directly to match handling for blocked business objects in order to release them. 


Example Request:



```
curl --request POST \\
     --url https://rz3.aeb.de/test4ce/rest/ComplianceScreeningApplications/screeningLogEntry \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --data '

{
     "generalParms": {
          "client": "APITEST",
          "user": "Oracle User 0815",
          "language": "en",
          "isACEmbedded": true,
    		"displayFullWorkplace": false,
    		"displayStatusbar": false,
    		"displayTitlebar": false
     },
     "specificParms": {
          "clientSystemId": "Oracle Cloud ERP",
          "clientIdentCode": "APITEST",
          "referenceId": "CUS_4711"
     }
}
```

Example Response:

```
{
   "sessionid": "AFCall-Invoke8174187571760108876414",
   "httpUrl": "https://rz3.aeb.de/test4ce/servlet/LazyStartAF?call=Invoke8174187571760108876414",
   "urlCloseToken": "goodbypage"
}
```

### Embedding the AEB GUI into your software - Open the match handling overview for all open matches


The API matchHandlingView can be used to open the match handling overview, which displays all open matches from the latest Compliance Screening checks. Integrating this API is useful if the response from the screenAddresses API is evaluated in the partner system and a user is to be offered a central tile or function that allows them to access the match handling. This allows a compliance officer to jump directly to match handling without a parallel browser login to Trade Compliance Management.  

The API request supports transmitting a stored view in the field storedViewName of the specificParms. Individual views can be configured in the match handling UI before the API is used (e.g., if a separate query is to be made for the address matches or good guy alert event, or if a specific partner system or specific compliance profile and/or organizational unit are is be retrieved). The parameter for the filter name to be transferred corresponds to the abbreviation of the view. If no individual filter is passed in the specificParms, then a default view is used.

The documentation of that can be found here: https://trade-compliance.docs.developers.aeb.com/reference/matchhandlingview

Example Request:
```
curl --request POST \
     --url https://rz3.aeb.de/test4ce/rest/ComplianceScreeningApplications/matchHandlingView \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --data '
{
  "generalParms": {
    "client": "APITEST",
    "user": "SNR",
    "language": "en",
    "isACEmbedded": false,
    "displayTitlebar": false,
    "displayFullWorkplace": false,
    "displayStatusbar": false
  },
  "specificParms": {
    "storedViewName": "OPEN_MATCHES"
  }
}
```

Example Response:
```
{
   "sessionid": "AFCall-Invoke565511061768235996285",
   "httpUrl": "https://rz3.aeb.de/test4ce/servlet/LazyStartAF?call=Invoke565511061768235996285",
   "urlCloseToken": "goodbypage"
}
```


### Count the number of open matches 


The API countMatchHandlingMatches returns the number of matches for the requested match handling view. 

This API can be used to query the number of open address matches or good-guy alerts from Compliance Screening. This is useful if access or entry into the match handling takes place from a partner system and a user needs to be shown whether and how many open matches are currently to be processed. To ensure that the displayed number in the partner system is as up-to-date as possible, the API should be called at regular intervals of about 5 minutes. If time-critical processing is to be supported, the API can also be called every minute.

The API request is made by transmitting a stored view in the field storedViewName of the filterParms. Individual views can be configured in the match handling UI before the API is used (e.g., if a separate query is to be made for the address matches or good guy alert event, or if a specific partner system or specific compliance profile and/or organizational unit are is be retrieved). The parameter for the filter name to be transferred corresponds to the abbreviation of the view. If no individual filter is passed in the filterParms, then a default view is used.

The countMatchHandlingMatches API is usually implemented in combination with the matchHandlingView API so that the user knows when open matches need to be processed and therefore needs to open the hit overview. Both APIs can use the same views.  

The documentation of that can be found here: https://rz3.aeb.de/test4ce/rest/ComplianceScreening/countMatchHandlingMatches

Example Request:

```
curl --request POST \
     --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/countMatchHandlingMatches \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --data '
{
  "resultLanguageIsoCodes": [
    "en"
  ],
  "filterParms": {
    "storedViewName": "OPEN_MATCHES"
  },
  "clientIdentCode": "APITEST",
  "clientSystemId": "SOAPUI",
  "userName": "SNR"
}
```

Example Response:

```
{
   "hasErrors": false,
   "hasOnlyRetryableErrors": false,
   "hasWarnings": false,
   "messages": [],
   "countOfMatches": 67
}
```


### Define a Good Guy

This request creates a Good Guy in all Good Guy lists defined in the given Compliance profile (profileIdentCode). If a Good Guy with exactly the same address fields already exists in at least one relevant Good Guy list, the Good Guy will not be created again for a second time.

When match handling reveals that a screened address should be defined as a Good Guy, the partner system should make the request Define a Good Guy. Therefor the REST API goodGuy (or SOAP API RexBF-defineGoodGuyWithResult) can be used. In this request, the address data provided by the host system is transferred to the Good Guy that will be saved in the Trade Compliance Management system. If an address that has been defined as a Good guy is checked again, no matches will be found for this address anymore.

In the field "info", the processing comment of a user could be transferred to document the decision why the given address has been found to be a Good Guy.

It is possible to define a Good Guy that only applies to a special context. This context is defined via the condition. A condition could be an order number, for example. A Good Guy without condition will always apply to all future checks of the address for which this Good Guy was defined. A Good Guy with condition “ORDER\_12560” will only apply in the context of this order. Technically, this means that future checks with Bulk address screening or Find matching addresses of the address for which the Good Guy with condition was defined, should provide the same condition as in the Good Guy in an appropriate parameter of the request in order for this Good Guy to be applied.

Example Request:

```
curl --request POST \\
&nbsp;    --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/goodGuy \\
&nbsp;    --header 'accept: application/json' \\
&nbsp;    --header 'content-type: application/json' \\
&nbsp;    --data '
{
  "addressType": "entity",
  "name": "Abu Ahmed Group Inc.",
  "street": "Fuller street 5",
  "pc": "MK7 6AJ",
  "city": "Manchester",
  "district": "North",
  "countryISO": "GB",
  "telNo": "+4413859-489548",
  "postbox": "12345",
  "pcPostbox": "MK7 6AJ",
  "cityPostbox": "Manchester",
  "email": "abu.ahmed@google.com",
  "fax": "+4413859-4895497",
  "name1": "Abu Ahmed Group Inc.",
  "info": "Just name similarity with person Abu Ahmed but our business partner is a company.",
  "clientIdentCode": "APITEST",
  "profileIdentCode": "DEFAULT",
  "clientSystemId": "Oracle Cloud ERP",
  "referenceId": "Order\_12560\_Consignee\_4712",
  "referenceComment": "Order 12560, Consignee 4712",
  "isActive": true,
  "userIdentification": "Oracle User 0815",
  "condition": {
    "value": "Order\_12560\_Consignee\_4712",
    "description": "Order 12560, Consignee 4712"
  }
}
```

Example Response:

```
{"definitionResult": 2}
```

### Get Compliance Profiles

Returns all Compliance profiles of a client. You can use REST API profiles (or SOAP API RexBF-getAllProfilesForClient).

This API can be used to check which Compliance profile are configured in Trade Compliance Management before an address check is performed. This API is typically only needed for the initial implementation of the Compliance Screening checks if more than one profile is used.

Example Request:

```
curl --request GET \
     --url 'https://rz3.aeb.de/test4ce/rest/ComplianceScreening/profiles?clientIdentCode=APITEST' \
     --header 'accept: application/json'
```

Example Response:

```
\[
      {
      "identCode": "DEFAULT",
      "name": "Default-Profil"
   },
      {
      "identCode": "EC\_RA\_PROFILE",
      "name": "Profile for EC checks with RA"
   }
]
```

### Create a Log Entry

You can create log entries in Compliance Screening logs. Please use REST API logEntry (or SOAP API RexBF-protocolClientSystemEvent) for this use case.
This API allows you to use AEB Trade Compliance Management as a central storage for logging data to have one central application that serves as an audit trail.

Check results of address screening are typically logged there by the AEB application. It could make sense to write additional logs about processes in the partner system like blocking or unblocking of checked business partners or orders.

Example Request:

```
curl --request POST \\
&nbsp;    --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/logEntry \\
&nbsp;    --header 'accept: application/json' \\
&nbsp;    --header 'content-type: application/json' \\
&nbsp;    --data '
{
  "level": "INFO",
  "clientIdentCode": "APITEST",
  "profileIdentCode": "DEFAULT",
  "clientSystemId": "Oracle Cloud ERP",
  "referenceId": "Order\_12560\_Consignee\_4712",
  "referenceComment": "Order 12560, Consignee 4712",
  "info": "The compliance block for order 12560 was removed in Oracle.",
  "userIdentification": "Oracle User 0815",
  "module": "ComplianceScreening",
  "happendAtDate": {
    "dateInTimezone": "2025-10-10 17:40:36",
    "timezone": "GMT+01:00"
  }
}
```

### Get Statistic Data

Returns statistic data such as number of address matches, address matches processed, address matches via file checks, or Good Guys defined. You can filter by client system, client, client group, and time frame, but the time frame may not exceed three months. You can use REST API screeningStatisticData (or SOAP API RexBF-getScreeningStatisticData) for this use case.

Example Request:

```
curl --request POST \
    --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/screeningStatisticData \
    --header 'accept: application/json' \
    --header 'content-type: application/json' \
    --data '
{
  "clientSystemId": "Oracle Cloud ERP",
  "clientIdentCode": "APITEST",
  "userName": "Oracle User 0815",
  "resultLanguageIsoCodes": \[
    "en",
    "de"
  ],
  "clientIdentCodeToGet": "APITEST",
  "dateFrom": "2025-10-01",
  "dateTo": "2025-10-10",
  "getDataOfAllClientSystems": false
}
```

Example Response:

```
{
   "hasErrors": false,
   "hasOnlyRetryableErrors": false,
   "hasWarnings": false,
   "messages": \[],
   "statisticDataRecords":    \[
            {
         "clientIdentCode": "APITEST",
         "clientSystemId": "Oracle Cloud ERP",
         "profileIdentCode": "DEFAULT",
         "date": "2025-10-02",
         "numAddressesChecked": 6,
         "numAddressesCheckedFile": 0,
         "numAddressesCheckedBF": 6,
         "numMatchesFound": 6,
         "numMaxSimilarity95to100": 5,
         "numMaxSimilarity90to94": 1,
         "numMaxSimilarity85to89": 0,
         "numMaxSimilarity80to84": 0,
         "numMaxSimilarity75to79": 0,
         "numMatchesCreated": 6,
         "numProcessed": 0,
         "numDefinedAsGoodGuy": 0,
         "numGoodGuysChecked": 0,
         "numGoodGuyAlarmsFound": 0,
         "numGoodGuyAlarmsCreated": 0,
         "numGoodGuyAlarmsProcessed": 0,
         "numClientSystemErrors": 0,
         "numFileChecksChecked": 0,
         "numFileChecksWithErrors": 0
      },
            {
         "clientIdentCode": "APITEST",
         "clientSystemId": "Oracle Cloud ERP",
         "profileIdentCode": "DEFAULT",
         "date": "2025-10-10",
         "numAddressesChecked": 10,
         "numAddressesCheckedFile": 0,
         "numAddressesCheckedBF": 10,
         "numMatchesFound": 7,
         "numMaxSimilarity95to100": 7,
         "numMaxSimilarity90to94": 0,
         "numMaxSimilarity85to89": 0,
         "numMaxSimilarity80to84": 0,
         "numMaxSimilarity75to79": 0,
         "numMatchesCreated": 7,
         "numProcessed": 0,
         "numDefinedAsGoodGuy": 0,
         "numGoodGuysChecked": 0,
         "numGoodGuyAlarmsFound": 0,
         "numGoodGuyAlarmsCreated": 0,
         "numGoodGuyAlarmsProcessed": 0,
         "numClientSystemErrors": 0,
         "numFileChecksChecked": 0,
         "numFileChecksWithErrors": 0
      }
   ]
}
```

### Data subscriptions

You can create so-called data extracts from Trade Compliance Management for specific compliance logs (matches, non-matches in order to import them into your reporting systems and generate your own statistics or evaluations. Please note that before periodically retrieving the data subscription from a partner system, a data extract definition and data subscription must be configured in Trade Compliance Management.

In addition, a partner system subscription must be configured for an API connection in TCM (Administration - Synchronization - Partner system subscription). The ID of the requesting partner system (clientSystemId from the screeningParameters of the previously used APIs) must be stored in the “Installation ID” field and the “Subscription File” object must be configured!

Please use the following REST APIs in the order described below.

1\. Queries/polling to check whether there is a new data feed:

* REST API getpublisheddatafeedparts (or SOAP API getPublishedDataFeedParts)
* API always returns the retrieval information for the next 10 published data feed files. The response contains a Sync-ID and dataFeedPartId.
* you can find further API information here: https://trade-compliance.docs.developers.aeb.com/reference/getpublisheddatafeedparts

Example Request:

```
curl --request POST \
    --url https://rz3.aeb.de/test4ce/rest/DataFeedBFBean/getPublishedDataFeedParts \
    --header 'accept: application/json' \
    --header 'content-type: application/json' \
    --data '
{
  "clientSystemId": "Oracle Cloud Analytics",
  "clientIdentCode": "APITEST",
  "userName": "Oracle User 0815",
  "resultLanguageIsoCodes": \[
    "en"
  ]
}
```

Example Response:



```
{
  "hasErrors": false,
  "hasOnlyRetryableErrors": false,
  "hasWarnings": false,
  "messages": \[],
  "publishedFeedParts":    \[
           {
        "dataFeedDefinitionIdentCode": "MONTHLY\_REPORT\_MATCHES\_API",
        "sequenceNumber": 2,
        "partNumberInPeriod": 1,
        "numberOfPartsOfPeriod": 1,
        "periodStartDate": "2025-08-01",
        "periodEndDate": "2025-08-31",
        "numberOfRecords": 9,
        "dataFeedPartId": "E3D16111C5B543E88DC0AC4CD5C2FA7E",
        "fileExtension": ".csv"
     },
           {
        "dataFeedDefinitionIdentCode": "MONTHLY\_REPORT\_MATCHES\_API",
        "sequenceNumber": 3,
        "partNumberInPeriod": 1,
        "numberOfPartsOfPeriod": 1,
        "periodStartDate": "2025-09-01",
        "periodEndDate": "2025-09-30",
        "numberOfRecords": 17,
        "dataFeedPartId": "F6015EDF3C4343FA8C7DE44E9645C8AB",
        "fileExtension": ".csv"
     }
  ],
  "syncId": "220",
  "isComplete": true
}
```

2\. Retrieving the data records from the data extraction:
* REST API dataFeedParts (or SOAP API getDataFeedPartContent)
* As “id,” the dataFeedPartId(s) must be transferred

```
curl --request GET \
     --url 'https://rz3.aeb.de/test4ce/rest/DataFeedBFBean/dataFeedParts/APITEST/E3D16111C5B543E88DC0AC4CD5C2FA7E' \
     --header 'accept: application/json'
```

Example Response:

```
HTTP/1.1 200 OK
date: Wed, 22 Oct 2025 07:00:45 GMT
x-content-type-options: nosniff
content-security-policy: frame-ancestors  No
cache-control: no-store
content-type: text/plain;charset=UTF-8
vary: Accept-Encoding
strict-transport-security: max-age=63072000
x-robots-tag: none, noindex, nofollow, noarchive, nosnippet, noodp, notranslate, noimageindex, unavailable\_after: 01 Jan 1999 00:00:00 GMT
x-request-id: 51eef9b6-077d-4e2e-9951-c3c54aeda658
ï»¿Datum / Uhrzeit;AdressprÃ¼f-Detail / Ist Treffer;AdressprÃ¼f-Detail / Ist Good Guy;Als Good Guy def.;AdressprÃ¼f-Detail / Adresse / Namensblock;AdressprÃ¼f-Detail / Adresse / StraÃŸe;AdressprÃ¼f-Detail / Adresse / Postleitzahl;AdressprÃ¼f-Detail / Adresse / Ort;AdressprÃ¼f-Detail / Adresse / Land;AdressprÃ¼f-Detail / Anzahl Treffer;Bearbeitet;Bearbeitet von;Compliance-Profil
04.08.2025T17:01:56;1;0;1;Fatima Group;E-110 Khayaban-e-Jinnah;54000;Lahore;PK;457;1;ADMIN;DEFAULT
04.08.2025T17:07:51;1;0;1;G C Baars (Pty) Ltd;42 Rand Rd.;1401;Germiston;ZA;9;1;ADMIN;DEFAULT
04.08.2025T17:10:41;1;0;0;BOXON AS;Knud Schartums gate 7;3045;Drammen;NO;2;1;ADMIN;DEFAULT
23.08.2025T00:04:46;1;0;0;Orion Metal Enterprises;53 Philip Engelbrecht Street;2021;Bryanston;ZA;28;0;;DEFAULT
26.08.2025T10:30:35;1;0;0;å°¼ç½—æ–¯ç§‘æŠ€å…¬å¸;;;;;1;0;;DEFAULT
26.08.2025T10:30:44;1;0;0;ç½—æ–¯ç§‘æŠ€å…¬å¸;;;;;1;0;;DEFAULT
26.08.2025T10:30:50;1;0;0;å°¼ç½—ç§‘æŠ€å…¬å¸;;;;;1;0;;DEFAULT
26.08.2025T10:31:02;1;0;0;å°¼ç½—æ–¯ç§‘æŠ€ç½—å…¬å¸;;;;;1;0;;DEFAULT
29.08.2025T00:04:59;1;0;0;SATURN Corporation LLC;493 Hudson Street;L9V 3P4;Shelburne Ontario;CA;21;0;;DEFAULT
```

3\. Confirm that the data record has been retrieved:

* REST API acknowledgePublishedDataFeedParts (or SOAP API acknowledgePublishedDataFeedParts)
* The sync ID obtained previously via API must be confirmed as retrieved here
* you can find further API information here: https://trade-compliance.docs.developers.aeb.com/reference/acknowledgepublisheddatafeedparts





Example Request:



```
curl --request POST \
    --url https://rz3.aeb.de/test4ce/rest/DataFeedBFBean/acknowledgePublishedDataFeedParts \
    --header 'accept: application/json' \
    --header 'content-type: application/json' \
    --data '
{
  "clientSystemId": "Oracle Cloud Analytics",
  "clientIdentCode": "APITEST",
  "userName": "Oracle User 0815",
  "resultLanguageIsoCodes": \["en"],
  "syncId": "194"
}
```

Example Response:

```
{
  "hasErrors": false,
  "hasOnlyRetryableErrors": false,
  "hasWarnings": false,
  "messages": \[]
}
```



