### API Examples

#### REST Examples

##### Person

###### Example Request

```bash
curl --request POST \
  --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/screenAddresses \
  --header 'accept: application/json' \
  --header 'authorization: Basic QVBJX1RFU1RAQVBJVEVTVDpBUElfVEVTVF8wMDc=' \
  --header 'content-type: application/json' \
  --data '
{
  "screeningParameters": {
    "suppressLogging": false,
    "addressTypeVersion": "1",
    "clientIdentCode": "APITEST",
    "clientSystemId": "Oracle Cloud ERP",
    "profileIdentCode": "DEFAULT",
    "userIdentification": "Oracle User 0815"
  },
  "addresses": [
    {
      "condition": {
        "description": "Master data record 4711",
        "value": "CUSTOMER_4711"
      },
      "referenceId": "CUS_4711",
      "referenceComment": "Customer 4711",
      "organisationUnitHost": "Sales DE",
      "addressType": "individual",
      "name": "Abu Ahmed",
      "street": "Newton street 5",
      "pc": "M1 2AW",
      "city": "Manchester",
      "countryISO": "GB",
      "district": "North West",
      "telNo": "+4413859-489548",
      "email": "abu.ahmed@example.com",
      "postbox": "12345",
      "pcPostbox": "MK7 6AJ",
      "cityPostbox": "Manchester",
      "surname": "Ahmed",
      "prenames": "Abu",
      "dateOfBirth": "1962",
      "cityOfBirth": "Dublin",
      "countryOfBirthISO": "IR",
      "nationalityISO": "IR",
      "position": "Senior Manager",
      "info": "https://aebse.oracle.com/link/Customer/0012p00002topdCAAQ/view",
      "ids": [
        {
          "idType": "PASSPORT_NO",
          "idValue": "385948495849"
        },
        {
          "idType": "DOMAIN_NAME",
          "idValue": "abu.ahmed@example.com"
        }
      ],
      "title": "Dr."
    }
  ]
}
'
```

###### Example Response

```json
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "CUS_4711",
    "referenceComment": "Customer 4711"
  }
]
```

##### Entity / Company

###### Example Request

```bash
curl --request POST \
  --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/screenAddresses \
  --header 'accept: application/json' \
  --header 'authorization: Basic QVBJX1RFU1RAQVBJVEVTVDpBUElfVEVTVF8wMDc=' \
  --header 'content-type: application/json' \
  --data '
{
  "screeningParameters": {
    "suppressLogging": false,
    "addressTypeVersion": "1",
    "clientIdentCode": "APITEST",
    "clientSystemId": "Oracle Cloud ERP",
    "profileIdentCode": "DEFAULT",
    "userIdentification": "Oracle User 0815"
  },
  "addresses": [
    {
      "condition": {
        "description": "Master data record 4712",
        "value": "CUSTOMER_4712"
      },
      "referenceId": "CUS_4712",
      "referenceComment": "Customer 4712",
      "organisationUnitHost": "Sales DE",
      "addressType": "entity",
      "name": "Abu Ahmed Ltd.",
      "street": "Newton street 5",
      "pc": "M1 2AW",
      "city": "Manchester",
      "countryISO": "GB",
      "district": "North West",
      "telNo": "+4413859-489548",
      "email": "abu.ahmed@example.com",
      "postbox": "12345",
      "pcPostbox": "MK7 6AJ",
      "cityPostbox": "Manchester",
      "name1": "Abu Ahmed",
      "info": "https://aebse.oracle.com/link/Account/0012p00002topdCAAQ/view",
      "ids": [
        {
          "idType": "DUNS_NO",
          "idValue": "936078708"
        },
        {
          "idType": "TAX_NO",
          "idValue": "GB925485058"
        }
      ],
      "name2": "Ltd."
    }
  ]
}
'
```

###### Example Response

```json
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "CUS_4712",
    "referenceComment": "Customer 4712"
  }
]
```

##### Means of Transport

###### Example Request

```bash
curl --request POST \
  --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/screenAddresses \
  --header 'accept: application/json' \
  --header 'authorization: Basic QVBJX1RFU1RAQVBJVEVTVDpBUElfVEVTVF8wMDc=' \
  --header 'content-type: application/json' \
  --data '
{
  "screeningParameters": {
    "suppressLogging": false,
    "addressTypeVersion": "1",
    "clientIdentCode": "APITEST",
    "clientSystemId": "Oracle Cloud ERP",
    "profileIdentCode": "DEFAULT",
    "userIdentification": "Oracle User 0815"
  },
  "addresses": [
    {
      "condition": {
        "description": "Master data record 4713",
        "value": "CARRIER_4713"
      },
      "referenceId": "CAR_4713",
      "referenceComment": "Carrier 4713",
      "organisationUnitHost": "Sales DE",
      "addressType": "meansOfTransport",
      "name": "Andromeda",
      "street": "18A pom. 7, ul. Pobedy",
      "pc": "694620",
      "city": "Kholmsk",
      "countryISO": "RU",
      "telNo": "+713859-489548",
      "email": "info@carrier-ute.com",
      "name1": "Andromeda",
      "nationalityISO": "RU",
      "info": "https://aebse.oracle.com/link/Carrier/0012p00002topdCAAQ/view",
      "ids": [
        {
          "idType": "IMO_NO",
          "idValue": "9118355"
        },
        {
          "idType": "DOMAIN_NAME",
          "idValue": "info@carrier-ute.com"
        }
      ]
    }
  ]
}
'
```

###### Example Response

```json
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "CAR_4713",
    "referenceComment": "Carrier 4713"
  }
]
```

##### Unknown Type

###### Example Request

```bash
curl --request POST \
  --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/screenAddresses \
  --header 'accept: application/json' \
  --header 'authorization: Basic QVBJX1RFU1RAQVBJVEVTVDpBUElfVEVTVF8wMDc=' \
  --header 'content-type: application/json' \
  --data '
{
  "screeningParameters": {
    "suppressLogging": false,
    "addressTypeVersion": "1",
    "clientIdentCode": "APITEST",
    "clientSystemId": "Oracle Cloud ERP",
    "profileIdentCode": "DEFAULT",
    "userIdentification": "Oracle User 0815"
  },
  "addresses": [
    {
      "condition": {
        "description": "Master data record 4714",
        "value": "VENDOR_4714"
      },
      "referenceId": "VEN_4714",
      "referenceComment": "Vendor 4714",
      "organisationUnitHost": "Sales DE",
      "addressType": "unknown",
      "name": "Plant Zvezda - Scientific and Production Center of Automation and Instrumentation named after academician N.A. Pilyugin",
      "street": "Vvedenskogo street 1",
      "pc": "117342",
      "city": "Moscow",
      "countryISO": "RU",
      "district": "North",
      "telNo": "+713859-489548",
      "email": "info@Plant-Zvezda.ru",
      "postbox": "12345",
      "pcPostbox": "117342",
      "cityPostbox": "Moscow",
      "name1": "Plant Zvezda",
      "info": "https://aebse.oracle.com/link/Vendor/0012p00002topdCAAQ/view",
      "ids": [
        {
          "idType": "BIC",
          "idValue": "CBGURUMM"
        },
        {
          "idType": "DOMAIN_NAME",
          "idValue": "info@Plant-Zvezda.ru"
        }
      ],
      "name2": "Scientific and Production Center of Automation and Instrumentation",
      "name3": "named after academician N.A.",
      "name4": "Pilyugin"
    }
  ]
}
'
```

###### Example Response

```json
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "VEN_4714",
    "referenceComment": "Vendor 4714"
  }
]
```

##### Transactional Objects (e.g., Order, Deliveries, Purchase Orders)

###### Example Request

```bash
curl --request POST \
  --url https://rz3.aeb.de/test4ce/rest/ComplianceScreening/screenAddresses \
  --header 'accept: application/json' \
  --header 'authorization: Basic QVBJX1RFU1RAQVBJVEVTVDpBUElfVEVTVF8wMDc=' \
  --header 'content-type: application/json' \
  --data '
{
  "screeningParameters": {
    "suppressLogging": false,
    "addressTypeVersion": "1",
    "clientIdentCode": "APITEST",
    "clientSystemId": "Oracle Cloud ERP",
    "profileIdentCode": "DEFAULT",
    "userIdentification": "Oracle User 0815"
  },
  "addresses": [
    {
      "condition": {
        "description": "Order 12560",
        "value": "Order_12560"
      },
      "referenceId": "Order_12560_Consignee_4712",
      "referenceComment": "Order 12560, Consignee 4712",
      "organisationUnitHost": "Sales DE",
      "addressType": "entity",
      "name": "Abu Ahmed Ltd.",
      "street": "Newton street 5",
      "pc": "M1 2AW",
      "city": "Manchester",
      "countryISO": "GB",
      "district": "North West",
      "telNo": "+4413859-489548",
      "postbox": "12345",
      "pcPostbox": "MK7 6AJ",
      "cityPostbox": "Manchester",
      "name1": "Abu Ahmed",
      "info": "https://aebse.oracle.com/link/Order/0012p00002topdCAAQ/view",
      "ids": [
        {
          "idType": "DUNS_NO",
          "idValue": "936078708"
        },
        {
          "idType": "TAX_NO",
          "idValue": "GB925485058"
        }
      ],
      "name2": "Ltd."
    },
    {
      "condition": {
        "value": "Order_12560",
        "description": "Order 12560"
      },
      "referenceComment": "Order 12560, Payer 4715",
      "referenceId": "Order_12560_Payer_4715",
      "organisationUnitHost": "Sales DE",
      "addressType": "entity",
      "name": "Ascotec GmbH - AHWAZ STEEL Commercial & Technical Service",
      "street": "Tersteegenstr. 10",
      "pc": "40474",
      "city": "Düsseldorf",
      "countryISO": "DE",
      "name2": "AHWAZ STEEL Commercial & Technical Service",
      "name1": "Ascotec GmbH",
      "ids": [
        {
          "idType": "DUNS_NO",
          "idValue": "329918122"
        },
        {
          "idType": "TAX_NO",
          "idValue": "DE119371067"
        },
        {
          "idType": "DOMAIN_NAME",
          "idValue": "inbfo@ascotec.com"
        }
      ],
      "telNo": "+49211-470520",
      "info": "https://aebse.oracle.com/link/Order/0012p00002topdCAAQ/view"
    },
    {
      "condition": {
        "value": "Order_12560",
        "description": "Order 12560"
      },
      "referenceComment": "Order 12560, Carrier 4716",
      "referenceId": "Order_12560_Carrier_4716",
      "addressType": "entity",
      "organisationUnitHost": "Sales DE",
      "name": "KARA Shipping and Chartering GmbH & Co. KG Special Road Transports International Division",
      "name1": "KARA Shipping and Chartering GmbH",
      "name2": "& Co. KG",
      "name3": "Special Road Transports",
      "name4": "International Division",
      "street": "Schottweg 7",
      "pc": "22087",
      "city": "Hamburg",
      "ids": [
        {
          "idType": "DUNS_NO",
          "idValue": "507105000"
        }
      ],
      "countryISO": "DE",
      "info": "https://aebse.oracle.com/link/Order/0012p00002topdCAAQ/view"
    }
  ]
}
'
```

###### Example Response

```json
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "Order_12560_Consignee_4712",
    "referenceComment": "Order 12560, Consignee 4712"
  },
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "Order_12560_Payer_4715",
    "referenceComment": "Order 12560, Payer 4715"
  },
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "Order_12560_Carrier_4716",
    "referenceComment": "Order 12560, Carrier 4716"
  }
]
```

#### SOAP examples

##### Person

Example Request:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:de.aeb.xnsg.rex.bf">
  <soapenv:Header/>
  <soapenv:Body>
    <urn:batchMatch>
      <patterns>
        <addressType>individual</addressType>
        <referenceComment>Customer 4711</referenceComment>
        <referenceId>CUS_4711</referenceId>
        <organisationUnitHost>Sales DE</organisationUnitHost>
        <city>Manchester</city>
        <cityOfBirth>Dublin</cityOfBirth>
        <cityPostbox>Manchester</cityPostbox>
        <countryISO>GB</countryISO>
        <countryOfBirthISO>IR</countryOfBirthISO>
        <dateOfBirth>1962</dateOfBirth>
        <district>North West</district>
        <email>abu.ahmed@example.com</email>
        <info>https://aebse.oracle.com/link/Customer/0012p00002topdCAAQ/view</info>
        <name>Abu Ahmed</name>
        <nationalityISO>IR</nationalityISO>
        <passportData>ID 385948495849</passportData>
        <pc>M1 2AW</pc>
        <pcPostbox>MK7 6AJ</pcPostbox>
        <position>Senior Manager</position>
        <postbox>12345</postbox>
        <prenames>Abu</prenames>
        <street>Newton street 5</street>
        <surname>Ahmed</surname>
        <telNo>+4413859-489548</telNo>
        <title>Dr.</title>
        <condition>
          <value>CUSTOMER_4711</value>
          <description>Master data record 4711</description>
        </condition>
        <ids>
          <idType>PASSPORT_NO</idType>
          <idValue>385948495849</idValue>
        </ids>
        <ids>
          <idType>DOMAIN_NAME</idType>
          <idValue>abu.ahmed@example.com</idValue>
        </ids>
      </patterns>
      <parms>
        <clientIdentCode>APITEST</clientIdentCode>
        <clientSystemId>Oracle Cloud ERP</clientSystemId>
        <profileIdentCode>DEFAULT</profileIdentCode>
        <suppressLogging>false</suppressLogging>
        <userIdentification>Oracle User 0815</userIdentification>
        <addressTypeVersion>1</addressTypeVersion>
      </parms>
    </urn:batchMatch>
  </soapenv:Body>
</soapenv:Envelope>
```

Example Response:

```xml
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
  <S:Body>
    <ns2:batchMatchResponse xmlns:ns2="urn:de.aeb.xnsg.rex.bf">
      <result>
        <matchFound>true</matchFound>
        <referenceComment>Customer 4711</referenceComment>
        <referenceId>CUS_4711</referenceId>
        <wasGoodGuy>false</wasGoodGuy>
      </result>
    </ns2:batchMatchResponse>
  </S:Body>
</S:Envelope>
```

##### Entity / Company

Example Request:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:de.aeb.xnsg.rex.bf">
  <soapenv:Header/>
  <soapenv:Body>
    <urn:batchMatch>
      <patterns>
        <addressType>entity</addressType>
        <referenceComment>Customer 4712</referenceComment>
        <referenceId>CUS_4712</referenceId>
        <organisationUnitHost>Sales DE</organisationUnitHost>
        <city>Manchester</city>
        <cityPostbox>Manchester</cityPostbox>
        <countryISO>GB</countryISO>
        <district>North West</district>
        <email>abu.ahmed@example.com</email>
        <info>https://aebse.oracle.com/link/Account/0012p00002topdCAAQ/view</info>
        <name>Abu Ahmed Ltd.</name>
        <pc>M1 2AW</pc>
        <pcPostbox>MK7 6AJ</pcPostbox>
        <postbox>12345</postbox>
        <street>Newton street 5</street>
        <telNo>+4413859-489548</telNo>
        <condition>
          <value>CUSTOMER_4712</value>
          <description>Master data record 4712</description>
        </condition>
        <ids>
          <idType>DUNS_NO</idType>
          <idValue>936078708</idValue>
        </ids>
        <ids>
          <idType>TAX_NO</idType>
          <idValue>GB925485058</idValue>
        </ids>
      </patterns>
      <parms>
        <clientIdentCode>APITEST</clientIdentCode>
        <clientSystemId>Oracle Cloud ERP</clientSystemId>
        <profileIdentCode>DEFAULT</profileIdentCode>
        <suppressLogging>false</suppressLogging>
        <userIdentification>Oracle User 0815</userIdentification>
        <addressTypeVersion>1</addressTypeVersion>
      </parms>
    </urn:batchMatch>
  </soapenv:Body>
</soapenv:Envelope>
```

Example Response:

```xml
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
  <S:Body>
    <ns2:batchMatchResponse xmlns:ns2="urn:de.aeb.xnsg.rex.bf">
      <result>
        <matchFound>true</matchFound>
        <referenceComment>Customer 4712</referenceComment>
        <referenceId>CUS_4712</referenceId>
        <wasGoodGuy>false</wasGoodGuy>
      </result>
    </ns2:batchMatchResponse>
  </S:Body>
</S:Envelope>
```

##### Means of Transport

Example Request:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:de.aeb.xnsg.rex.bf">
  <soapenv:Header/>
  <soapenv:Body>
    <urn:batchMatch>
      <patterns>
        <addressType>meansOfTransport</addressType>
        <referenceComment>Carrier 4713</referenceComment>
        <referenceId>CAR_4713</referenceId>
        <organisationUnitHost>Sales DE</organisationUnitHost>
        <city>Kholmsk</city>
        <countryISO>RU</countryISO>
        <email>info@carrier-ute.com</email>
        <info>https://aebse.oracle.com/link/Carrier/0012p00002topdCAAQ/view</info>
        <name>Andromeda</name>
        <pc>694620</pc>
        <street>18A pom. 7, ul. Pobedy</street>
        <telNo>+713859-489548</telNo>
        <condition>
          <value>CARRIER_4713</value>
          <description>Master data record 4713</description>
        </condition>
        <ids>
          <idType>IMO_NO</idType>
          <idValue>9118355</idValue>
        </ids>
        <ids>
          <idType>DOMAIN_NAME</idType>
          <idValue>info@carrier-ute.com</idValue>
        </ids>
      </patterns>
      <parms>
        <clientIdentCode>APITEST</clientIdentCode>
        <clientSystemId>Oracle Cloud ERP</clientSystemId>
        <profileIdentCode>DEFAULT</profileIdentCode>
        <suppressLogging>false</suppressLogging>
        <userIdentification>Oracle User 0815</userIdentification>
        <addressTypeVersion>1</addressTypeVersion>
      </parms>
    </urn:batchMatch>
  </soapenv:Body>
</soapenv:Envelope>
```

Example Response:

```xml
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
  <S:Body>
    <ns2:batchMatchResponse xmlns:ns2="urn:de.aeb.xnsg.rex.bf">
      <result>
        <matchFound>true</matchFound>
        <referenceComment>Carrier 4713</referenceComment>
        <referenceId>CAR_4713</referenceId>
        <wasGoodGuy>false</wasGoodGuy>
      </result>
    </ns2:batchMatchResponse>
  </S:Body>
</S:Envelope>
```

##### Unknown Type

Example Request:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:de.aeb.xnsg.rex.bf">
  <soapenv:Header/>
  <soapenv:Body>
    <urn:batchMatch>
      <patterns>
        <addressType>unknown</addressType>
        <referenceComment>Vendor 4714</referenceComment>
        <referenceId>VEN_4714</referenceId>
        <organisationUnitHost>Sales DE</organisationUnitHost>
        <city>Moscow</city>
        <cityPostbox>Moscow</cityPostbox>
        <countryISO>RU</countryISO>
        <district>North</district>
        <email>info@Plant-Zvezda.ru</email>
        <info>https://aebse.oracle.com/link/Vendor/0012p00002topdCAAQ/view</info>
        <name>Plant Zvezda - Scientific and Production Center of Automation and Instrumentation named after academician N.A. Pilyugin</name>
        <name1>Plant Zvezda</name1>
        <name2>Scientific and Production Center of Automation and Instrumentation</name2>
        <name3>named after academician N.A.</name3>
        <name4>Pilyugin</name4>
        <pc>117342</pc>
        <pcPostbox>117342</pcPostbox>
        <postbox>12345</postbox>
        <street>Vvedenskogo street 1</street>
        <telNo>+713859-489548</telNo>
        <condition>
          <value>CUSTOMER_4711</value>
          <description>Master data record 4711</description>
        </condition>
        <ids>
          <idType>BIC</idType>
          <idValue>CBGURUMM</idValue>
        </ids>
        <ids>
          <idType>DOMAIN_NAME</idType>
          <idValue>info@Plant-Zvezda.ru</idValue>
        </ids>
      </patterns>
      <parms>
        <clientIdentCode>APITEST</clientIdentCode>
        <clientSystemId>Oracle Cloud ERP</clientSystemId>
        <profileIdentCode>DEFAULT</profileIdentCode>
        <suppressLogging>false</suppressLogging>
        <userIdentification>Oracle User 0815</userIdentification>
        <addressTypeVersion>1</addressTypeVersion>
      </parms>
    </urn:batchMatch>
  </soapenv:Body>
</soapenv:Envelope>
```

Example Response:

```xml
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
  <S:Body>
    <ns2:batchMatchResponse xmlns:ns2="urn:de.aeb.xnsg.rex.bf">
      <result>
        <matchFound>true</matchFound>
        <referenceComment>Vendor 4714</referenceComment>
        <referenceId>VEN_4714</referenceId>
        <wasGoodGuy>false</wasGoodGuy>
      </result>
    </ns2:batchMatchResponse>
  </S:Body>
</S:Envelope>
```

##### Transactional objects (e.g order, deliveries, purchase orders)

Example Request:

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:de.aeb.xnsg.rex.bf">
  <soapenv:Header/>
  <soapenv:Body>
    <urn:batchMatch>
      <patterns>
        <addressType>entity</addressType>
        <referenceComment>Order 12560, Consignee 4712</referenceComment>
        <referenceId>Order_12560_Consignee_4712</referenceId>
        <organisationUnitHost>Sales DE</organisationUnitHost>
        <city>Manchester</city>
        <cityPostbox>Manchester</cityPostbox>
        <countryISO>GB</countryISO>
        <district>North West</district>
        <info>https://aebse.oracle.com/link/Order/0012p00002topdCAAQ/view</info>
        <name>Abu Ahmed Ltd.</name>
        <name1>Abu Ahmed</name1>
        <name2>Ltd.</name2>
        <pc>M1 2AW</pc>
        <pcPostbox>MK7 6AJ</pcPostbox>
        <postbox>12345</postbox>
        <street>Newton street 5</street>
        <telNo>+4413859-489548</telNo>
        <condition>
          <value>Order_12560</value>
          <description>Order 12560</description>
        </condition>
        <ids>
          <idType>DUNS_NO</idType>
          <idValue>936078708</idValue>
        </ids>
        <ids>
          <idType>TAX_NO</idType>
          <idValue>GB925485058</idValue>
        </ids>
      </patterns>
      <patterns>
        <addressType>entity</addressType>
        <referenceComment>Order 12560, Payer 4715</referenceComment>
        <referenceId>Order_12560_Payer_4715</referenceId>
        <organisationUnitHost>Sales DE</organisationUnitHost>
        <city>Düsseldorf</city>
        <cityPostbox>Düsseldorf</cityPostbox>
        <countryISO>DE</countryISO>
        <info>https://aebse.oracle.com/link/Order/0012p00002topdCAAQ/view</info>
        <name>Ascotec GmbH - AHWAZ STEEL Commercial and Technical Service</name>
        <name1>Ascotec GmbH</name1>
        <name2>AHWAZ STEEL Commercial and Technical Service</name2>
        <pc>40474</pc>
        <pcPostbox>40474</pcPostbox>
        <postbox>12345</postbox>
        <email>info@ascotec.com</email>
        <street>Tersteegenstr. 10</street>
        <telNo>+49211-470520</telNo>
        <condition>
          <value>Order_12560</value>
          <description>Order 12560</description>
        </condition>
        <ids>
          <idType>DUNS_NO</idType>
          <idValue>329918122</idValue>
        </ids>
        <ids>
          <idType>TAX_NO</idType>
          <idValue>DE119371067</idValue>
        </ids>
        <ids>
          <idType>DOMAIN_NAME</idType>
          <idValue>info@ascotec.com</idValue>
        </ids>
      </patterns>
      <patterns>
        <addressType>entity</addressType>
        <referenceComment>Order 12560, Carrier 4716</referenceComment>
        <referenceId>Order_12560_Carrier_4716</referenceId>
        <organisationUnitHost>Sales DE</organisationUnitHost>
        <city>Hamburg</city>
        <cityPostbox>Hamburg</cityPostbox>
        <countryISO>DE</countryISO>
        <info>https://aebse.oracle.com/link/Order/0012p00002topdCAAQ/view</info>
        <name>KARA Shipping and Chartering GmbH &amp; Co. KG Special Road Transports International Devision</name>
        <name1>KARA Shipping and Chartering GmbH</name1>
        <name2>&amp; Co. KG</name2>
        <name3>Special Road Transports</name3>
        <name4>Special Road Transports</name4>
        <pc>40474</pc>
        <pcPostbox>22087</pcPostbox>
        <postbox>12345</postbox>
        <street>Schottweg 7</street>
        <telNo>+49211-230520</telNo>
        <condition>
          <value>Order_12560</value>
          <description>Order 12560</description>
        </condition>
        <ids>
          <idType>DUNS_NO</idType>
          <idValue>507105000</idValue>
        </ids>
      </patterns>
      <parms>
        <clientIdentCode>APITEST</clientIdentCode>
        <clientSystemId>Oracle Cloud ERP</clientSystemId>
        <profileIdentCode>DEFAULT</profileIdentCode>
        <suppressLogging>false</suppressLogging>
        <userIdentification>Oracle User 0815</userIdentification>
        <addressTypeVersion>1</addressTypeVersion>
      </parms>
    </urn:batchMatch>
  </soapenv:Body>
</soapenv:Envelope>
```

Example Response:

```xml
<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
  <S:Body>
    <ns2:batchMatchResponse xmlns:ns2="urn:de.aeb.xnsg.rex.bf">
      <result>
        <matchFound>true</matchFound>
        <referenceComment>Order 12560, Consignee 4712</referenceComment>
        <referenceId>Order_12560_Consignee_4712</referenceId>
        <wasGoodGuy>false</wasGoodGuy>
      </result>
      <result>
        <matchFound>true</matchFound>
        <referenceComment>Order 12560, Payer 4715</referenceComment>
        <referenceId>Order_12560_Payer_4715</referenceId>
        <wasGoodGuy>false</wasGoodGuy>
      </result>
      <result>
        <matchFound>false</matchFound>
        <referenceComment>Order 12560, Carrier 4716</referenceComment>
        <referenceId>Order_12560_Carrier_4716</referenceId>
        <wasGoodGuy>false</wasGoodGuy>
      </result>
    </ns2:batchMatchResponse>
  </S:Body>
</S:Envelope>
```

### Address fields

######

#### Mandatory fields

- `name`: string length ≤ 200; Full name of the address, e.g. name of the company (name1, name2, name3, name4) or of an individual (prename and surname).

#### Check relevant fields

- `name`: string length ≤ 200; Full name of the address, e.g. name of the company (name1, name2, name3, name4) or of an individual (prename and surname).
- `name1`: string length ≤ 50; Additional information only for entities: The first line of the name.
- `name2`: string length ≤ 50; Additional information only for entities: The second line of the name.
- `name3`: string length ≤ 50; Additional information only for entities: The third line of the name.
- `name4`: string length ≤ 50; Additional information only for entities: The fourth line of the name.
- `addressType`: string enum; The address type determines whether a person, company, or means of transport is the origin of the business partner being checked. If addressTypeVersion 1 is used, the possible values are entity, individual, meansOfTransport and unknown.
- `street`: string length ≤ 100; Street of the address, including house number.
- `pc`: string length ≤ 40; Postal code of the city.
- `city`: string length ≤ 100; City of the address.
- `countryISO`: string length ≤ 2; Two character ISO code of the country of the address.
- `postbox`: string length ≤ 20; The P.O. box of the address.
- `pcPostbox`: string length ≤ 40; The postal code of the P.O. box, if the postal code of the P.O. box differs from the postal code of the street address.
- `condition`: "value": string length ≤ 1000; The condition value to be unique per unique condition. Only good guys with exactly the same condition are considered during the address checks. Should be used to identify a specific business object (e.g. master data records or transactional orders, delivieres and so on).
- `condition`: "description": string length ≤ 255; A short human-readable description of the condition specified by the value. The textual description refers to the value of the conditions.
- `ids`: "idType": string enum; Identification numbers can help verify and identify a person or company regardless of their name. The possible values are DUNS_NO (for DUNS numbers of companies), TAX_NO (for national tax numbers of companies), BIC (SWIFT code for banks and financial institutions), IMO_NO (IMO's globally unique, 7-digit identification number for vessels), PASSPORT_NO (Passport number of a passport belonging to individuals), DOMAIN_NAME (refers to either an email address or the URL of a website).
- `ids`: "idValue": string length ≤ 50;The value of the identification number must contain the specific number relating to the type (DUNS_NO, TAX_NO, BIC, IMO_NO, PASSPORT_NO, DOMAIN_NAME).
#### Recommended reference fields

- `referenceId`: string length ≤ 255; Reference identification number for match results and logs. It should contain a technical identification number. Should be used to identify a specific business object from the sending partner system and to build references between the compliance logs and the business object. For transactional movement data (e.g. order, deliveries), the reference ID should be composed of the transaional object number and the business partner number.
- `referenceComment`: string length ≤ 3000; Human readable reference comment for logs. It should contain a user readable reference identifcation number. Should be used to identify a specific business object from the sending partner system. For transactional movement data (e.g. order, deliveries), the referenceComment should be composed of the transaional object number and the business partner number.
- `info`: string length ≤ 1000; Can be used to provide additional information to the checked business partner. However, it can also be used to provide a URL link that allows the checked object to be accessed in the partner system. This allows users to conduct research there or initiate follow-up processes.
#### Optional fields

- `district`: string length ≤ 50; District of the address, a specific area within a city or town, which can refer to an administrative division, a postal zone, or a more general locality.
- `telNo`: string length ≤ 40; Telephone number.
- `cityPostbox`: string length ≤ 100; The city of the P.O. box, if the city of the P.O. box differs from the city of the street address.
- `email`: string length ≤ 256; Email address.
- `fax`: string length ≤ 40; Fax number.
- `surname`: string length ≤ 50; The surname of an individual.
- `prenames`: string length ≤ 50; The prenames of an individual.
- `dateOfBirth`: string length ≤ 20; The known date of birth of an individual in a human-readable format , e.g. 1962-08-20 or just 1962.
- `passportData`: string length ≤ 200; Textual information about the passport of an individual, e.g. passport number and date of issue.
- `cityOfBirth`: string length ≤ 50; The city of birth of an individual.
- `countryOfBirthISO`: string length ≤ 2; Two-letter ISO code for the country of birth of an individual.
- `nationalityISO`: string length ≤ 2; Two-letter ISO code for the nationality of an individual.
- `position`: string length ≤ 200; Textual information about the job position of an individual.
- `niNumber`: string length ≤ 50; Additional identification tokens or numbers of individuals.

### Response Scenarios

#### Scenario 1: Potential Match Detected

The following response message describes the scenario where a potential address match has been detected. A match handling in Trade Compliance Management is required and the object in the partner system should be blocked:

```json
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "VEN_4714",
    "referenceComment": "Vendor 4714"
  }
]
```

#### Scenario 2: No Match Found

The following scenario detects an uncritical address where no further action in Trade Compliance Management is required and where the business object in the partner system can be further processed and used:

```json
[
  {
    "matchFound": false,
    "wasGoodGuy": false,
    "referenceId": "VEN_4715",
    "referenceComment": "Vendor 4715"
  }
]
```

#### Scenario 3: Good Guy Definition

The third scenario detects an uncritical address due to a previous good guy definition in Trade Compliance Management. The business object in the partner system can be further processed and used:

```json
[
  {
    "matchFound": false,
    "wasGoodGuy": true,
    "referenceId": "VEN_4716",
    "referenceComment": "Vendor 4716"
  }
]
```
