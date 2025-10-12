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
