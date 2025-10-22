def get_screen_addresses_spec() -> str:
    """Get the specification for the screen_addresses tool."""
    return """
# Address screening - API Specification

POST https://rz3.aeb.de/test4ce/rest/ComplianceScreening/screenAddresses

Screens addresses against restricted party lists.

```json
{
  "/ComplianceScreening/screenAddresses": {
    "post": {
      "tags": ["Compliance Screening"],
      "summary": "Address screening",
      "description": "Screens addresses against restricted party lists.",
      "operationId": "screenAddresses",
      "requestBody": {
        "content": {
          "application/json": {
            "schema": {
              "description": "Request object for screening addresses against restricted party lists.",
              "properties": {
                "addresses": {
                  "type": "array",
                  "description": "The addresses to be screened.",
                  "items": {
                    "description": "Data transfer object for an address to be screened against restricted party lists.",
                    "properties": {
                      "addressType": {
                        "type": "string",
                        "description": "The addressTypeVersion of MatchParametersDTO defines the result behavior of this field when calling /ComplianceScreening/findMatchingAddresses. If addressTypeVersion 0 is used, the possible return values are: company, individual, bank, vessel. If addressTypeVersion 1 is used, the possible return values are: entity, individual, meansOfTransport, unknown. Depending on the profile settings, this field might be relevant for the address check.",
                        "enum": [
                          "company",
                          "individual",
                          "bank",
                          "vessel",
                          "entity",
                          "meansOfTransport",
                          "unknown"
                        ],
                        "example": "entity"
                      },
                      "name": {
                        "type": "string",
                        "description": "Full name of the address, e.g. name of the company (address line 1 - 4) or prename and surname of an individual. Depending on the profile settings, this field might be relevant for the address check.",
                        "example": "Abu Ahmed Group Inc.",
                        "maxLength": 200
                      },
                      "street": {
                        "type": "string",
                        "description": "Street of the address, including house number. This field is relevant for the address check.",
                        "example": "Fuller street 5",
                        "maxLength": 100
                      },
                      "pc": {
                        "type": "string",
                        "description": "Postal code of the city. This field is relevant for the address check.",
                        "example": "MK7 6AJ",
                        "maxLength": 40
                      },
                      "city": {
                        "type": "string",
                        "description": "City of the address. This field is relevant for the address check.",
                        "example": "Manchester",
                        "maxLength": 100
                      },
                      "district": {
                        "type": "string",
                        "description": "District of the address, resp. line 2 of the city (in German: Ortsteil).",
                        "example": "North",
                        "maxLength": 50
                      },
                      "countryISO": {
                        "type": "string",
                        "description": "Two character ISO code of the country. This field is relevant for the address check.",
                        "example": "DE",
                        "maxLength": 2
                      },
                      "telNo": {
                        "type": "string",
                        "description": "Telephone number.",
                        "example": "+4413859-489548",
                        "maxLength": 40
                      },
                      "postbox": {
                        "type": "string",
                        "description": "The P.O. box of the address. Depending on the profile settings, this field might be relevant for the address check.",
                        "example": 12345,
                        "maxLength": 20
                      },
                      "pcPostbox": {
                        "type": "string",
                        "description": "The postal code of the P.O. box, if the postal code of the P.O. box differs from the postal code of the street address.",
                        "example": "MK7 6AJ",
                        "maxLength": 40
                      },
                      "cityPostbox": {
                        "type": "string",
                        "description": "The city of the P.O. box, if the city of the P.O. box differs from the city of the street address.",
                        "example": "Manchester",
                        "maxLength": 100
                      },
                      "email": {
                        "type": "string",
                        "description": "Email address.",
                        "example": "abu.ahmed@example.com",
                        "maxLength": 256
                      },
                      "fax": {
                        "type": "string",
                        "description": "Fax number.",
                        "example": "+4413859-4895497",
                        "maxLength": 40
                      },
                      "name1": {
                        "type": "string",
                        "description": "Additional information only for companies: The first line of the addresses name. Depending on the profile settings, this field might be relevant for the address check.",
                        "example": "Abu Ahmed",
                        "maxLength": 50
                      },
                      "name2": {
                        "type": "string",
                        "description": "Additional information only for companies: The second line of the addresses name. Depending on the profile settings, this field might be relevant for the address check.",
                        "example": "Group Inc.",
                        "maxLength": 50
                      },
                      "name3": {
                        "type": "string",
                        "description": "Additional information only for companies: The third line of the addresses name. Depending on the profile settings, this field might be relevant for the address check.",
                        "example": "Factory for sweets of all kind",
                        "maxLength": 50
                      },
                      "name4": {
                        "type": "string",
                        "description": "Additional information only for companies: The fourth line of the addresses name. Depending on the profile settings, this field might be relevant for the address check.",
                        "example": "Manchester",
                        "maxLength": 50
                      },
                      "title": {
                        "type": "string",
                        "description": "Additional information only for individuals: The title of a person.",
                        "example": "Haji",
                        "maxLength": 20
                      },
                      "surname": {
                        "type": "string",
                        "description": "Additional information only for individuals: The surname of a person.",
                        "example": "Ahmed",
                        "maxLength": 50
                      },
                      "prenames": {
                        "type": "string",
                        "description": "Additional information only for individuals: The prenames of a person.",
                        "example": "Abu",
                        "maxLength": 50
                      },
                      "dateOfBirth": {
                        "type": "string",
                        "description": "The date of birth in textual representation, e.g. 1962-08-20 or just 1962 or other date formats. (Only human-readable.)",
                        "example": 1962,
                        "maxLength": 20
                      },
                      "passportData": {
                        "type": "string",
                        "description": "Additional information only for individuals: Textual information about the passport, e.g. passport no. and date of issue.",
                        "example": "ID 385948495849",
                        "maxLength": 200
                      },
                      "cityOfBirth": {
                        "type": "string",
                        "description": "Additional information only for individuals: City of birth.",
                        "example": "Dublin",
                        "maxLength": 50
                      },
                      "countryOfBirthISO": {
                        "type": "string",
                        "description": "Additional information only for individuals: Two-letter ISO code for the country of birth.",
                        "example": "IR",
                        "maxLength": 2
                      },
                      "nationalityISO": {
                        "type": "string",
                        "description": "Additional information only for individuals: Two-letter ISO code for the nationality.",
                        "example": "IR"
                      },
                      "position": {
                        "type": "string",
                        "description": "Additional information only for individuals: Textual information about the position of the individual.",
                        "example": "Senior official of the Islamic State in Iraq and the Levant (ISIL)",
                        "maxLength": 200
                      },
                      "niNumber": {
                        "type": "string",
                        "description": "Additional identification tokens or numbers of individuals.",
                        "example": "Italian fiscal code SSYBLK62T26Z336L",
                        "maxLength": 50
                      },
                      "info": {
                        "type": "string",
                        "description": "Summary additional information, e.g. alias names or information composed of other field like position, passportData, dateOfBirth.",
                        "example": "UN Ref QDi.401",
                        "maxLength": 1000
                      },
                      "aliasGroupNo": {
                        "type": "string",
                        "description": "Number or name of the group under which all addresses are summarized describing the same person or organization.",
                        "example": 12345,
                        "maxLength": 20
                      },
                      "free1": {
                        "type": "string",
                        "description": "Additional field for future use.",
                        "example": "free1",
                        "maxLength": 50
                      },
                      "free2": {
                        "type": "string",
                        "description": "Additional field for future use.",
                        "example": "free2",
                        "maxLength": 50
                      },
                      "free3": {
                        "type": "string",
                        "description": "Additional field for future use.",
                        "example": "free3",
                        "maxLength": 50
                      },
                      "free4": {
                        "type": "string",
                        "description": "Additional field for future use.",
                        "example": "free4",
                        "maxLength": 50
                      },
                      "free5": {
                        "type": "string",
                        "description": "Additional field for future use.",
                        "example": "free5",
                        "maxLength": 50
                      },
                      "free6": {
                        "type": "string",
                        "description": "Additional field for future use.",
                        "example": "free6",
                        "maxLength": 50
                      },
                      "free7": {
                        "type": "string",
                        "description": "Additional field for future use.",
                        "example": "free7",
                        "maxLength": 50
                      },
                      "ids": {
                        "type": "array",
                        "description": "Optional IDs of the address, e.g. like DUNS number or passport number.",
                        "items": {
                          "description": "Data transfer object for encoding of IDs of addresses, e.g. like DUNS number or passport number.",
                          "properties": {
                            "idType": {
                              "type": "string",
                              "description": "Type of an address ID. Depending on settings in the profile, is may also be allowed to let this field empty, in which case the idValue is matched against any id type.",
                              "enum": [
                                "DUNS_NO",
                                "TAX_NO",
                                "BIC",
                                "IMO_NO",
                                "PASSPORT_NO",
                                "DOMAIN_NAME"
                              ],
                              "example": "DUNS_NO"
                            },
                            "idValue": {
                              "type": "string",
                              "description": "Value of an ID, e.g. a concrete DUNS number or tax number.",
                              "example": "15-048-3782"
                            }
                          },
                          "required": ["idValue"]
                        }
                      },
                      "referenceId": {
                        "type": "string",
                        "description": "Reference key for match results and logs, e.g. current user, client, pc, delivery note number or debitor number. This field is for internal technical use to build references between the compliance logs and the client system.",
                        "example": "CUSNO=4711;CLIENT=800;USER=BEN003;PC=PC-PHILIPP",
                        "maxLength": 255
                      },
                      "referenceComment": {
                        "type": "string",
                        "description": "User readable reference comment for logs, e.g. current user, current pc, delivery note number or or debitor number.",
                        "example": "Customer no.: 4711, Client: 800, User: BEN003, Pc: PC-PHILIPP",
                        "maxLength": 3000
                      },
                      "organisationUnitHost": {
                        "type": "string",
                        "description": "Address specific ident code of the organizational unit. If not specified, the organizational unit from MatchParametersDTO is used.",
                        "example": "Sales Unit 0711",
                        "maxLength": 255
                      },
                      "condition": {
                        "description": "An optional condition used for screening of this address. If present, only Good Guys that either have no condition or that meet the condition given here are considered.",
                        "properties": {
                          "value": {
                            "type": "string",
                            "description": "The condition value to be unique per unique condition. Only Good Guys with exactly the same condition are considered during the address checks.",
                            "example": "ORDER_12345",
                            "maxLength": 1000
                          },
                          "description": {
                            "type": "string",
                            "description": "A short, human-readable description of the condition specified by the value.",
                            "example": "Order no. 12345",
                            "maxLength": 255
                          }
                        },
                        "required": ["value"]
                      }
                    }
                  }
                },
                "screeningParameters": {
                  "description": "Parameters for the screening process.",
                  "properties": {
                    "clientIdentCode": {
                      "type": "string",
                      "description": "Ident code of the client to use for screening. The value must be a valid ident code of a client the authorized user has access to (usually the same client used for authentication).",
                      "example": "APITEST",
                      "maxLength": 10
                    },
                    "profileIdentCode": {
                      "type": "string",
                      "description": "Ident code of a Compliance profile. The value must be a valid ident code for the client specified by the clientIdentCode.",
                      "example": "DEFAULT",
                      "maxLength": 20
                    },
                    "threshold": {
                      "type": "integer",
                      "format": "int32",
                      "description": "Define the similarity threshold in percentage which should be used for screening checks. Optionally overrides the value from the Compliance profile used. In most cases, this value should be left empty. When no value is submitted or the submitted value equals zero, the value from the Compliance profile will be used. Valid values are: 1 to 100. It is recommended to choose a value between 75 and 85. Values below this range can have negative effects on performance and on the result quality.",
                      "example": 84,
                      "maxLength": 3,
                      "maximum": 100,
                      "minimum": 1
                    },
                    "addressTranslateThreshold": {
                      "type": "integer",
                      "format": "int32",
                      "description": "Defines an optional similarity threshold in percentage which should be used for screening checks that were translated. This value is only used if the translation feature is enabled for the profile. This overrides the value from the Compliance profile used. When no value is submitted or the submitted value equals zero, the value from the Compliance profile will be used. Valid values are: 1 to 100. It is recommended to choose a value between 75 and 85. Values below this range can have negative effects on performance and on the result quality. Since: 2020/10",
                      "example": 78,
                      "maxLength": 3,
                      "maximum": 100,
                      "minimum": 1
                    },
                    "addrMatchWithoutNameThreshold": {
                      "type": "integer",
                      "format": "int32",
                      "description": "Defines an optional similarity threshold in percentage which should be used for address screening without name. This overrides the value from the Compliance profile used. When no value is submitted or the submitted value equals zero, the value from the Compliance profile will be used. Valid values are: 1 to 100. It is recommended to choose a value between 75 and 85. Values below this range can have negative effects on performance and on the result quality. Since: 2020/10",
                      "example": 84,
                      "maxLength": 3,
                      "maximum": 100,
                      "minimum": 1
                    },
                    "clientSystemId": {
                      "type": "string",
                      "description": "The unique ID of the host system calling this API. Used when logging the address screening results.",
                      "example": "SAP_[SAP system]_[SAP client]",
                      "maxLength": 20
                    },
                    "organisationUnitHost": {
                      "type": "string",
                      "description": "Ident code of the organizational unit. May be null. An address specific organizational unit can be specified via AddressPatternDTO. If an organizational unit is specified there, it is used instead of the organizational unit specified here.",
                      "example": "Sales Unit 0711",
                      "maxLength": 255
                    },
                    "suppressLogging": {
                      "type": "boolean",
                      "default": "false",
                      "description": "If true, the address screening operation will not be logged, thus match handling in Trade Compliance Management will not be possible. If omitted or false, the address screening operation will be logged.",
                      "example": false
                    },
                    "considerGoodGuys": {
                      "type": "boolean",
                      "default": "true",
                      "description": "If false Good Guys will be ignored. If omitted or true, Good Guys will be considered. Should only be used if Good Guys should be ignored specifically, i.e. to specifically check a Good Guy similar to the Good Guy screening batch.",
                      "example": true
                    },
                    "userIdentification": {
                      "type": "string",
                      "description": "The user name to be used for logging. Purely informational.",
                      "example": "BEN003",
                      "maxLength": 100
                    },
                    "addressTypeVersion": {
                      "type": "string",
                      "default": "0",
                      "description": "The addressTypeVersion defines the result behavior of addressType in AddressDTO when calling /ComplianceScreening/findMatchingAddresses. Possible values: 0, 1. If addressTypeVersion 0 is used, the possible return values of addressType are: company, individual, bank, vessel. If addressTypeVersion 1 is used, the possible return values of addressType are: entity, individual, meansOfTransport, unknown.",
                      "enum": ["0", "1"],
                      "example": 1
                    }
                  },
                  "required": ["clientIdentCode", "profileIdentCode"]
                }
              }
            }
          },
        }
      },
      "responses": {
        "200": {
          "description": "OK. The screening results.",
          "content": {
            "application/json": {
              "schema": {
                "items": {
                  "description": "Data transfer object for the results of address screening.",
                  "properties": {
                    "matchFound": {
                      "type": "boolean",
                      "description": "The result of the screening. `true` if one or more matching restricted party addresses were found, `false` if not.",
                      "example": true
                    },
                    "wasGoodGuy": {
                      "type": "boolean",
                      "description": "`true`, if a Good Guy was defined for this address. Otherwise `false` is returned.",
                      "example": false
                    },
                    "referenceId": {
                      "type": "string",
                      "description": "Copied from the corresponding field in the request, allowing to correlate the results to the request.",
                      "example": "CUSNO=4711;CLIENT=800;USER=BEN003;PC=PC-PHILIPP",
                      "maxLength": 255
                    },
                    "referenceComment": {
                      "type": "string",
                      "description": "Copied from the corresponding field in in the request, allowing to correlate the results to the request.",
                      "example": "Customer no.: 4711, Client: 800, User: BEN003, Pc: PC-PHILIPP",
                      "maxLength": 3000
                    }
                  }
                }
              }
            },
          }
        },
        "401": {
          "description": "Unauthorized. Missing or invalid authorization token.",
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ErrorData"
              }
            },
          }
        },
        "405": {
          "description": "Method not allowed. Use POST.",
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ErrorData"
              }
            },
          }
        },
        "406": {
          "description": "Not Acceptable. This resource produces application/json or application/xml.",
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ErrorData"
              }
            },
          }
        },
        "415": {
          "description": "Unsupported Media Type. This resource accepts application/json or application/xml.",
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ErrorData"
              }
            },
          }
        },
        "500": {
          "description": "Other errors, like a malformed request or internal server error. See errorMessage for details.",
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/ErrorData"
              }
            },
          }
        }
      }
    }
  }
}
```
    """


def get_general_information_about_screening_api() -> str:
    """Get general information about the screening API."""
    return """

    
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

**Client**: One basic parameter for all requests in Trade Compliance Management APIs is a client identification and a technical communication user. A client clusters different users into a group that share the same data, organizational unit, and so on. Typically your company gets assigned to one client in Trade Compliance Management, when contracting with AEB. The Client has to be filled within the API as clientIdentCode within screeningParameters.  

**Compliance profile**: Most of the requests requires the identification if a Compliance profile. A Compliance profile is a set of settings, such as the restricted party lists to use for address screening or activated jurisdictions for export controls. Every client can have multiple profiles for different scenarios. The profile "DEFAULT" is typically available to most clients, especially in the API test environment. The Compliance profile has to be filled within the API as profileIdentCode within screeningParameters.

**Partersystem identification**: The unique ID of the host system (partner system) calling the API is stored in functional logs to identify the IT System (e.g. ERP).  The Partersystem identification has to be filled within the API as clientSystemId within screeningParameters.

**Organizational unit**: In IT systems (e.g., ERP), business units or divisions are typically represented as organizational units. These can be sales or purchasing organizations, for example. An address specific organizational unit can be transferred as part of the compliance check for specific business partners in order to achieve separation or accountability when processing the check results. The organizational unit has to be filled within the API as organisationUnitHost within screeningParameters.

**Restricted Party Lists**: Restricted party lists are lists of companies and persons, which need special attention when trading with them or making any contracts with them. Compliance Screening offers a lot of restricted party lists of different governments and other organizations as a data service. Additionally, your company can maintain its own restricted party lists for special use cases (e.g., cash residue of some customers). The Compliance Screening API requests do not allow to specify directly which restricted party lists should be used for screening. Instead, you will specify this in the configuration of a Compliance profile.

**Good Guy**: If the Compliance Screening check has returned a match, i.e., the checked business partner is similar to a restricted Party list entry according to the selected threshold value, then follow-up processing of a match is required. As a result of false positives (there is no identity between your checked business partner and the entry on the restricted party list), a good guy can be defined (with or without conditions). Good Guys are stored in Trade Compliance Management so that no new matches are reported during a follow-up check with the same business partner (identical name and address). With the parameter considerGoodGuys you can control whether good guys are used or not. If this Parameter is set to value false Good Guys will be ignored. If omitted or true, Good Guys will be considered. This parameter is optional and usually not needed as good guys should be reflected to avoid recurring efforts.
    """


def get_api_examples() -> str:
    return """
    # API Examples

## REST examples

### 1. Person

Example Request:

```
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
```

Example Response:

```
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "CUS_4711",
    "referenceComment": "Customer 4711"
  }

]
```

### 2. Entity / Company

Example Request:

```
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
```

Example Response:

```
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "CUS_4712",
    "referenceComment": "Customer 4712"
  }
]
```

### 3. Means of Transport

Example Request:

```
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
```

Example Response:

```
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "CAR_4713",
    "referenceComment": "Carrier 4713"
  }
]
```

### 4. Unknown Type

Example Request:

```
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
```

Example Response:

```
[
  {
    "matchFound": true,
    "wasGoodGuy": false,
    "referenceId": "VEN_4714",
    "referenceComment": "Vendor 4714"
  }
]
```

### 4. Transactional movement data (e.g order, deliveries, purchase orders)

Example Request:

```
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
```

Example Response:

```
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
"""
