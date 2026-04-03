from fastapi import APIRouter, HTTPException, Query, Request

from core.reports.service import ComplianceReportService


class ReportsAPIRouter:
    def __init__(self, report_service: ComplianceReportService):
        self.report_service = report_service

        # Initialize api router
        self.router = APIRouter()

        # Register routes
        self.router.add_api_route(
            "/{tenant_id}/{framework}",
            self.get_report,
            methods=["GET"],
        )

    async def get_report(
        self,
        request: Request,
        tenant_id: str,
        framework: str,
        start_date: str | None = Query(default=None),
        end_date: str | None = Query(default=None),
    ):
        """
        Generate a compliance report. framework ∈ {soc2, gdpr, pci}
        """

        match framework.lower():
            case "soc2":
                soc2_report = await self.report_service.generate_soc2_report(
                    tenant_id=tenant_id,
                    start_date=start_date,
                    end_date=end_date,
                )
                return soc2_report
            case "gdpr":
                gdpr_report = await self.report_service.generate_gdpr_report(
                    tenant_id=tenant_id
                )
                return gdpr_report
            case "pci":
                pci_report = await self.report_service.generate_pci_report(
                    tenant_id=tenant_id
                )
                return pci_report
            case _:
                raise HTTPException(
                    status_code=400,
                    detail={"message": "Invalid framework. Use: soc2 | gdpr | pci"},
                )
