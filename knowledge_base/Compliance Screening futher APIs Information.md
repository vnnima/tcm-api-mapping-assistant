### Find Matching Addresses

Trade Compliance Management offers REST API `findMatchingAddresses` (or SOAP API RexBF-getMatchingAddresses). This request finds all restricted party addresses matching a given address.

In most cases, this request is used for handling matches found via Bulk address Screening . It is used to display matching restricted party addresses of a checked address to the user in the partner system who needs to decide if the addresses found are real matches or not. This API is only needed if you plan to implement the Match handling directly from your software. Please check the API for defining a Good Guy as well.

#### Example Request

```json
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
    "referenceId": "CUS_4711",
    "referenceComment": "Customer 4711",
    "condition": {
      "value": "CUS_4711",
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

#### Example Response

```json
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
    "matchType": "ADDRESS_AND_NAME",
    "embargoArea": "someAreaName"
  }
]
```

### Embedding the AEB GUI into your Software

Besides business facades (BF), which allow the use of Compliance Screening functionality in your own program code, the AEB Compliance Screening API also offers application facades (AF) to embed the GUI of Compliance Screening in your own software.

An application facade call is technically a normal business facade call - the authentication process is the same, request parameters are transmitted as HTTP body. But an application facade returns a link in the response, which the caller of the application facade can open in a new browser window or in an embedded frame of the web application, so the desired application of Compliance Screening opens for the user.

There are several application facades available which can be found here: https://trade-compliance.docs.developers.aeb.com/reference/screeninglogentry-1.

The following example shows the REST API `screeningLogEntry` to open the match handling for one critical address.

#### Example Request

```json
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

#### Example Response

```json
{
  "sessionid": "AFCall-Invoke8174187571760108876414",
  "httpUrl": "https://rz3.aeb.de/test4ce/servlet/LazyStartAF?call=Invoke8174187571760108876414",
  "urlCloseToken": "goodbypage"
}
```

### Define a Good Guy

This request creates a Good Guy in all Good Guy lists defined in the given Compliance profile (`profileIdentCode`). If a Good Guy with exactly the same address fields already exists in at least one relevant Good Guy list, the Good Guy will not be created again for a second time.

When match handling reveals that a screened address should be defined as a Good Guy, the partner system should make the request "Define a Good Guy". Therefore, the REST API `goodGuy` (or SOAP API `RexBF-defineGoodGuyWithResult`) can be used. In this request, the address data provided by the host system is transferred to the Good Guy that will be saved in the Trade Compliance Management system. If an address that has been defined as a Good Guy is checked again, no matches will be found for this address anymore.

In the field "info", the processing comment of a user could be transferred to document the decision why the given address has been found to be a Good Guy.

It is possible to define a Good Guy that only applies to a special context. This context is defined via the condition. A condition could be an order number, for example. A Good Guy without condition will always apply to all future checks of the address for which this Good Guy was defined. A Good Guy with condition "ORDER_12560" will only apply in the context of this order. Technically, this means that future checks with Bulk address screening or Find matching addresses of the address for which the Good Guy with condition was defined, should provide the same condition as in the Good Guy in an appropriate parameter of the request in order for this Good Guy to be applied.

#### Example Request

```json
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
  "referenceId": "Order_12560_Consignee_4712",
  "referenceComment": "Order 12560, Consignee 4712",
  "isActive": true,
  "userIdentification": "Oracle User 0815",
  "condition": {
    "value": "Order_12560_Consignee_4712",
    "description": "Order 12560, Consignee 4712"
  }
}
```

#### Example Response

```json
{ "definitionResult": 2 }
```

### Get Compliance Profiles

Returns all Compliance profiles of a client. You can use REST API `profiles` (or SOAP API `RexBF-getAllProfilesForClient`).

This API can be used to check which Compliance profiles are configured in Trade Compliance Management before an address check is performed. This API is typically only needed for the initial implementation of the Compliance Screening checks if more than one profile is used.

#### Example Request

```bash
curl --request GET \
  --url 'https://rz3.aeb.de/test4ce/rest/ComplianceScreening/profiles?clientIdentCode=APITEST' \
  --header 'accept: application/json'
```

#### Example Response

```json
[
  {
    "identCode": "DEFAULT",
    "name": "Default-Profil"
  },
  {
    "identCode": "EC_RA_PROFILE",
    "name": "Profile for EC checks with RA"
  }
]
```

### Create a Log Entry

You can create log entries in Compliance Screening logs. Please use REST API `logEntry` (or SOAP API `RexBF-protocolClientSystemEvent`) for this use case.

This API allows you to use AEB Trade Compliance Management as a central storage for logging data to have one central application that serves as an audit trail.

Check results of address screening are typically logged there by the AEB application. It could make sense to write additional logs about processes in the partner system like blocking or unblocking of checked business partners or orders.

#### Example Request

```json
{
  "level": "INFO",
  "clientIdentCode": "APITEST",
  "profileIdentCode": "DEFAULT",
  "clientSystemId": "Oracle Cloud ERP",
  "referenceId": "Order_12560_Consignee_4712",
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

Returns statistic data such as number of address matches, address matches processed, address matches via file checks, or Good Guys defined. You can filter by client system, client, client group, and time frame, but the time frame may not exceed three months. You can use REST API `screeningStatisticData` (or SOAP API `RexBF-getScreeningStatisticData`) for this use case.

#### Example Request

```json
{
  "clientSystemId": "Oracle Cloud ERP",
  "clientIdentCode": "APITEST",
  "userName": "Oracle User 0815",
  "resultLanguageIsoCodes": ["en", "de"],
  "clientIdentCodeToGet": "APITEST",
  "dateFrom": "2025-10-01",
  "dateTo": "2025-10-10",
  "getDataOfAllClientSystems": false
}
```

#### Example Response

```json
{
  "hasErrors": false,
  "hasOnlyRetryableErrors": false,
  "hasWarnings": false,
  "messages": [],
  "statisticDataRecords": [
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

### Data Subscriptions

You can create so-called data extracts from Trade Compliance Management for specific compliance logs (matches, non-matches) in order to import them into your reporting systems and generate your own statistics or evaluations. Please note that before periodically retrieving the data subscription from a partner system, a data extract definition and data subscription must be configured in Trade Compliance Management.

In addition, a partner system subscription must be configured for an API connection in TCM (Administration - Synchronization - Partner system subscription). The ID of the requesting partner system (`clientSystemId` from the `screeningParameters` of the previously used APIs) must be stored in the "Installation ID" field and the "Subscription File" object must be configured!

Please use the following REST APIs in the order described below.

1. Queries/polling to check whether there is a new data feed:

   - REST API `getpublisheddatafeedparts` (or SOAP API `getPublishedDataFeedParts`)
   - API always returns the retrieval information for the next 10 published data feed files. The response contains a Sync-ID and `dataFeedPartId`.
   - You can find further API information here: https://trade-compliance.docs.developers.aeb.com/reference/getpublisheddatafeedparts

   #### Example Request

   ```json
   {
     "clientSystemId": "Oracle Cloud Analytics",
     "clientIdentCode": "APITEST",
     "userName": "Oracle User 0815",
     "resultLanguageIsoCodes": ["en"]
   }
   ```

2. Retrieving the data records from the data extraction:

   - REST API `dataFeedParts` (or SOAP API `getDataFeedPartContent`)
   - As "client," the `clientIdentCode` of the `screeningParameters` must be transferred
   - As "id," the `dataFeedPartId`(s) must be transferred
   - You can find further API information here: https://trade-compliance.docs.developers.aeb.com/reference/getdatafeedpartcontentforrest

   #### Example Request

   ```bash
   curl --request GET \
     --url 'https://rz3.aeb.de/test4ce/rest/DataFeedBFBean/dataFeedParts/APITEST/D75980ADD2954586BBDC3F1297A9CFFB' \
     --header 'accept: application/json'
   ```

3. Confirm that the data record has been retrieved:

   - REST API `acknowledgePublishedDataFeedParts` (or SOAP API `acknowledgePublishedDataFeedParts`)
   - The sync ID obtained previously via API must be confirmed as retrieved here
   - You can find further API information here: https://trade-compliance.docs.developers.aeb.com/reference/acknowledgepublisheddatafeedparts

   #### Example Request

   ```json
   {
     "clientSystemId": "Oracle Cloud Analytics",
     "clientIdentCode": "APITEST",
     "userName": "Oracle User 0815",
     "resultLanguageIsoCodes": ["en"],
     "syncId": "194"
   }
   ```
