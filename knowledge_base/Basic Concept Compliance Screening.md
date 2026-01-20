# Basic Concept Compliance Screening

## Recommended Options for API Usage

### 1. One-Way Transfer Without Rechecks

In the first option, data is transferred from a partner system to **Trade Compliance Management** on a one-way basis only. The API request can contain certain relevant business partners (customers, suppliers, employees, etc.) or transactional data (e.g., orders with multiple business partners). The data set should include the name, address information, a unique reference, IDs, conditions, and the address type.

A business partner check is then performed and logged in TCM. The result of the check can be a match or non-match, which is reported directly in the API Response message. If necessary, the object can be blocked or stopped in the partner system or a notification can be displayed directly to a user if a potential match is detected (`"matchFound": true, "wasGoodGuy": false`).

In the event of a match, an email is also sent to an email recipient configured in TCM (company's compliance officer), who then processes the matches in TCM (defines a **good guy** for false positives or marks them as true matches). This procedure only requires the REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`) that must be called once per business object (master data record or transactional data). The object must be released in the partner system or finally stopped or deleted manually by a user after the match handling in **Trade Compliance Management**.

### 2. Transfer with Response Evaluation and Periodic Rechecks

In the second variant, data is transferred from the partner system and, in addition, open matches are regularly checked so that they can not only be blocked but also unblocked in the partner system. The API request can contain certain relevant business partners (customers, suppliers, employees, etc.) or transactional data (e.g., orders with multiple business partners). The data set should include the name, address information, a unique reference, IDs, conditions, and the address type.

A business partner check is then performed, which is logged in TCM. The result of the check can be a match or a non-match, which is reported directly in the response. If necessary, the object can be blocked or stopped in the partner system or a notification can be displayed directly to a user if a potential match is detected (`"matchFound": true, "wasGoodGuy": false`).

In the event of a match, an email is also sent to an email recipient configured in TCM (company's compliance officer), who then processes the matches in **Trade Compliance Management** (defines a **good guy** for false positives or marks them as true matches). This procedure requires the REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`) that have to be used several times.

- First, the initial check must be performed.
- For business objects that received a match during the initial check (`"matchFound": true, "wasGoodGuy": false`), a periodic recheck must be performed so that a subsequent noncritical check result can be determined in the partner system after the match processing in TCM.
- This recheck must be done until the check result gets uncritical (`"matchFound": false, "wasGoodGuy": true`).

This enables an automatic unblocking of the business object in the partner system after the **good guy** definition. The partner system must save the critical check results for address matches. The suggested frequency for the recheck is every 60 minutes. In addition, the parameter `suppressLogging` of the REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`) should be sent with the value `true` for periodic rechecks so that the periodic checks are not counted in addition to the invoiceable check volume.

### 3. Transfer with Direct Access to Match Handling

The third option can be implemented as a supplement to the first or second variant. After a compliance screening check of a business objects with the REST API screenAddresses (or SOAP API `RexBF-batchMatch`), the response can be evaluated in the partner system if there are potential matches (`"matchFound": true, "wasGoodGuy": false`). This use case assumes that a user accesses the match handling directly from the partner system. In the partner system, the user should not only be shown the match, but there should also be a button or menu function to call up the match handling in Trade Compliance Management. 

There are two ways to embed the match handling UI of Trade Compliance Management so that users can open it from partner systems:

The first option is to open the match handling UI for a specific address match if users want to access a specific business object in order to process or define the Good Guy just for this one address.  Therefore the screeningLogEntry API can be used to generate and open a web link to the match handling UI for one specific address match. Since the web link is only valid temporarily, the API should only be called when the user wants to start the match handling by clicking on the function introduced in the partner system.

The second option is to open the match handling UI which displays an overview of all open matches (worklist). This integration is ideal for making a central function or tile available to users in the partner system. Two APIs are available for integrating the match handling overview. The countMatchHandlingMatches API can be used to determine the number of open matches. Therefore, the API should be called periodically (e.g., once per minute). This allows the partner system to display whether and how many open matches need to be processed. In addition, the matchHandlingView API can then be used to open the match handling overview, which displays all open matches from the last compliance screening checks.  That API API can be used to generate and open a web link to the access the match handling UI. Since the web link is only valid temporarily, the matchHandlingView API should only be called when the user wants to start the match handling by clicking on the function introduced in the partner system. Both APIs (countMatchHandlingMatches and matchHandlingView) supports transmitting a stored view as parameter. Individual views can be configured in the match handling UI before the API is used (e.g., if a separation of address matches and good guy alert events is preferred or if specific compliance profiles or organizational units shall be enabled). 

## Basic Concept

The main request of Compliance Screening API is bulk address screening via REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`). This works for single addresses (just one check of a business partner) as well as with larger amounts of addresses (master data check for many business partners).

Usually, it is necessary to periodically screen all addresses which are part of the master data (e.g., customers, suppliers, or employees), e.g., once every night or once a week. You may have several thousand of business partners, so performance is important. For this reason, there is a bulk screening request which allows you to screen multiple addresses with one call. The screening of transactional data (e.g., orders, deliveries, purchase orders) can also contain typically more than one address (e.g., customer, consignee, forwarder, payer). Therefore, the bulk address screening can be used as well.

Processing too large amounts of addresses with one call can lead to timeouts, depending on the server and system configuration. A typical batch size could be 100 addresses. However, if you plan to use very big restricted party lists (e.g., from Dow Jones), we recommend smaller block sizes of 20 addresses to get acceptable response times.

The response of a bulk address screening request contains the overall result of the address check for each address (if there were any matches found or not). Address checks also create log entries in **Trade Compliance Management** which can be accessed there. Logs include further details about matches like all the matching restricted party addresses found. The logs are also used for the match handling of address matches in **Trade Compliance Management**, i.e., definition of **good guys**, etc.

The Bulk address screening processes several addresses at once and returns a simple result (match or non-match and additional if the address is already defined as **Good Guy**). In contrast, the API `findMatchingAddresses` can only check one address but provides further match information of all matching restricted party addresses. The API `findMatchingAddresses` will typically only be used if you plan to implement a match handling in the partner system or if you want to store and display the details of the found restricted party addresses. AEB does not recommend processing matches outside of **Trade Compliance Management**.

Due to the complexity of identity matching and the often incomplete data provided by restricted party lists, the address screening can only provide a list of possible matches. Deciding whether the matches found really correspond with the entity screened often requires additional investigation by a user. This is called **match handling**.

When **match handling** reveals that all the restricted party addresses found for the screened entity are mere name similarities and no real matches, the originally checked address can be defined as a **Good Guy**. If an address that has already been defined as a **Good Guy** is checked again, no matches will be found anymore. However, the Bulk address screening will report that the checked address is known as a **Good Guy**. **Good guys** are also organized in lists (**Good Guy** lists). The **Good Guy** lists to be considered in address screening can be configured in the Compliance profile. The Compliance profile is part of the `screeningParameters` as field `profileIdentCode`.

In our experience, the following events involving business objects are reasonable triggers for a Compliance Screening check:

- New creation of a business partner master data record (customer, vendor)
- Periodic batch checks of all active business partners once a week, month, or quarter (inactive or not used business partners shall be excluded)
- Relevant change to a business partner master data record (change of names or address details)
- New creation of a transactional object (order, delivery, purchase order, shipment)
- Relevant change to a business partner within a transactional object (change of name or address details or adding a new business partner)

### Match Handling and Good Guy Definition in Trade Compliance Management

The entire process of **match handling** and **good guy** definition can be handled directly in the **Trade Compliance Management** web application.

So how could it work with address screening from host system and **match handling** in **Trade Compliance Management**? For example: If a business partner has been checked from within your host system and been returned as critical, you might set a block in this business partner or the affected order in the host system to prevent that business is done with them for a while. A user or compliance officer will process this match in the special "Match handling" view in **Trade Compliance Management**. In this view, it is possible to define a **Good Guy** for the investigated match after an appropriate analysis or to mark this match as processed without a **Good Guy** definition.

The second option means that the checked address really corresponds with the restricted party addresses found and the block for the checked business partner or affected order should be kept in the host system (the next screening of this business partner will again return a critical result). If a **Good Guy** has been defined for the match, this means that the checked address is only similar to the restricted party addresses found and should be evaluated as uncritical in the next address screening. When the business partner is checked once again in the host system, it will be recognized as a **Good Guy** and the check result will be uncritical and the business partner or affected order in the host system could be unblocked.

If this workflow fulfills the needs of your company, the process of **match handling** in the partner system will not be needed at all. Only the blocking logic should be implemented if needed and repeated calls for address screening. You only have to implement the REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`).

### Match Handling and Good Guy Definition in Partner System

You can also develop the views and logic to allow users to do **match handling** and **Good Guy** definition within your software. There are several API requests which can support users with **match handling** in the partner system.

First, the REST API `screenAddresses` (or SOAP API `RexBF-batchMatch`) have to be implemented. Afterwards, the REST API `findMatchingAddresses` (or SOAP API `RexBF-getMatchingAddresses`) is required. The request "Find matching addresses" could be used to get the matching restricted party addresses for a checked address. These matching addresses could be displayed to the user in such a way that the user can compare the checked address with the restricted party addresses found and then decide if the found addresses are real matches or not.

If the user needs more details on a specific matching restricted party address, an API request can be used, which returns a URL for displaying details about that address, see [Embedded AEB GUI](https://trade-compliance.docs.developers.aeb.com/docs/embeded-aeb-gui-into-your-software). The URL could be opened in a browser window or could be embedded in a frame in the web application.

When **match handling** reveals that a screened address should be defined as a **good guy**, the host system should make the request to define a **good guy**. Therefore, the REST API `goodGuy` (or SOAP API `RexBF-defineGoodGuyWithResult`) can be implemented. In this request, the address data provided by the host system is transferred to the **good guy** that will be saved in **Trade Compliance Management**. If an address that has been defined as a **good guy** is checked again, no matches will be found for this address anymore.

AEB does not recommend processing matches outside of **Trade Compliance Management** as the effort for the implementation of all required APIs is very high and not really needed as TCM offers many comfort functions.

The Compliance Screening API requests do not allow to specify directly which restricted party lists should be used for screening. Instead, you will specify this in the configuration of a Compliance profile. Then you can pass the `profileIdentCode` in the API.
