from langchain_core.tools import tool


@tool
def get_tcm_api_documentation_url(keyword: str = "") -> str:
    """
    Get the appropriate TCM API documentation URL based on the keyword.

    Args:
        keyword: The keyword to determine which documentation is most relevant
        These are the possible keys:
        - compliance_screening_rest
        - export_controls_rest
        - license_management_rest
        - risk_assessment_rest
        - compliance_screening_soap
        - export_controls_soap
        - license_management_soap
        - risk_assessment_soap

    Returns:
        The most appropriate documentation URL with a brief description
    """

    keyword_lower = keyword.lower()

    url_mappings = {
        # REST API URLs
        "compliance_screening_getting_started": "https://trade-compliance.docs.developers.aeb.com/docs/getting-started-1",
        "compliance_screening_rest": "https://trade-compliance.docs.developers.aeb.com/reference/screenaddresses-1",
        "export_controls_rest":  "https://trade-compliance.docs.developers.aeb.com/reference/checktransaction-1",
        "license_management_rest":  "https://trade-compliance.docs.developers.aeb.com/reference/gettransactionapprovalscustomsdata",
        "risk_assessment_rest":
        "https://trade-compliance.docs.developers.aeb.com/reference/getquestionnairesummary-1",
        "compliance_screening_soap":
        "https://rz3.aeb.de/test4ce/servlet/bf/doc/RexBF/de/aeb/xnsg/rex/bf/IRexBF.html",
        "export_controls_soap":
        "https://rz3.aeb.de/test4ce/servlet/bf/doc/ExportControl40V2BF/de/aeb/xnsg/expctrl/bf/v40/IExportControl40V2BF.html",
        "license_management_soap":
        "https://rz3.aeb.de/test4ce/servlet/bf/doc/LicenseManagementBF/de/aeb/xnsg/licmgmt/bf/lm/ILicenseManagementBF.html",
        "risk_assessment_soap":
        "https://rz3.aeb.de/test4ce/servlet/bf/doc/RiskAssessmentBF/de/aeb/xnsg/riskasmt/bf/IRiskAssessmentBF.html",
    }

    return url_mappings[keyword_lower]
