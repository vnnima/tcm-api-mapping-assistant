The General Parameters within each API call (filled within screeningParameters) are the following ones:

The parameter `clientIdentCode` is a mandatory field. A client clusters different users into a group that share the same data, organizational unit, and so on. The Client has to be provided by AEB. The client with value "APITEST" is available in the AEB API test environment.

The parameter `profileIdentCode` is a mandatory field. A Compliance profile contains a set of settings, such as the restricted party lists to use for address screening or activated jurisdictions for export controls. Every client can have multiple profiles for different scenarios. A profile with value "DEFAULT" is typically available to most clients, especially in the AEB API test environment.

The parameter `clientSystemId` is an optional but recommended field. The unique ID of the host system or partner system that is sending the API calls can be transferred to identify the system within functional logs. The client with value "APITEST" is available in the AEB API test environment. A possible value could be "SAP S4HANA", "Oracle Fusion Cloud", "Microsoft Dynamics" or the name of any other IT System.

The parameter `userIdentification` is an optional but recommended field. The user name to be used for functional logs. It should be the user that initiates des Compliance check e.g. by the creation or changing of a business partner in the host system.  

The parameter `addressTypeVersion` is a mandatory field. Possible values are "0" and "1" This parameter determines the address typ version used in an Compliance Screening address check to identify whether an address belongs to a person, company or a means of transport. The current standard is value "1". If the value "1" is transferred you can use "entity" for a company, "individual" for persons, "meansOfTransport" for vessels and aircrafts and "unknwon" for not specified business partners. The value "0" for the parameter `addressTypeVersion` is currently only supported to ensure backward compatibility and should not be used for new API integrations. If the value "0" is transferred you can use "company" for a company, "individual" for persons, "vessel" for vessels and aircrafts and "bank" for banks.

The parameter `suppressLogging` is an optional and not recommended field. If omitted or value "false" is sent the Compliance Screening check will be logged and a match handling is possible. If the value "true" is sent than the Compliance Screening check will not be logged, thus match handling in Trade Compliance Management will not be possible. The value "true" should only be used for periodic queries to remove the block on a previously checked and blocked business partner or transactional business object (e.g. order, delivery) in a partner system based on a Good Guy definition.     

The parameter `addressTypeVersion` determines the address typ version used in a Compliance Screening address check to identify the . The current standard is `ADDRESS_TYPE_VERSION_1`. This version corresponds to the typical qualification of sanction list addresses and should always be used. `ADDRESS_TYPE_VERSION_0` is currently only supported to ensure backward compatibility and should not be used for new API integrations.

The parameter `organisationUnitHost` is an optional but recommended field. It can be a sales or purchasing organizations that represents a specific business unit or division in the partner system that belongs to the checked address of the business partner. 

The parameter `considerGoodGuys` is an optional and not recommended field. With this parameter you can control whether good guys are used or not. If this parameter is set to value "false" Good Guys will be ignored. If omitted or set to "true", Good Guys will be considered.

REST example in JSON: 
```json
"screeningParameters": {
    "clientIdentCode": "APITEST",
    "profileIdentCode": "DEFAULT",
    "clientSystemId": "SAP S4HANA",
    "userIdentification": "User 0815",
    "addressTypeVersion": "1",
    "organisationUnitHost": "German Sales"
  }
```

SOAP example in XML:
```xml
<parms>
        <clientIdentCode>APITEST</clientIdentCode>
        <profileIdentCode>DEFAULT</profileIdentCode>
        <clientSystemId>SAP S4HANA</clientSystemId>
        <userIdentification>User 0815</userIdentification>
        <addressTypeVersion>1</addressTypeVersion>
	<organisationUnitHost>German Sales</organisationUnitHost>
</parms>
```