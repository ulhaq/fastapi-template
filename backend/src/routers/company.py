from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import authenticate
from src.routers.query_options import (
    FiltersQuery,
    PageNumberQuery,
    PageSizeQuery,
    SortQuery,
)
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.company import CompanyBase, CompanyOut
from src.services.company import CompanyService

router = APIRouter()


@router.get(
    "/companies", dependencies=[Depends(authenticate)], status_code=status.HTTP_200_OK
)
async def get_all_companies(
    service: Annotated[CompanyService, Depends()],
    sort: SortQuery,
    filters: FiltersQuery,
    page_size: PageSizeQuery = 10,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[CompanyOut]:
    return await service.paginate(
        CompanyOut,
        PageQueryParams(
            sort=sort,
            filters=filters,
            page_size=page_size,
            page_number=page_number,
        ),
    )


@router.post(
    "/companies",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_201_CREATED,
)
async def create_a_company(
    service: Annotated[CompanyService, Depends()], company_in: CompanyBase
) -> CompanyOut:
    return await service.create_company(company_in)


@router.put(
    "/companies/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_200_OK,
)
async def update_a_company(
    service: Annotated[CompanyService, Depends()],
    identifier: Annotated[int, Path()],
    company_in: CompanyBase,
) -> CompanyOut:
    return await service.update_company(identifier, company_in)


@router.get(
    "/companies/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_200_OK,
)
async def retrieve_a_company(
    service: Annotated[CompanyService, Depends()], identifier: Annotated[int, Path()]
) -> CompanyOut:
    return await service.get_company(identifier)


@router.delete(
    "/companies/{identifier}",
    dependencies=[Depends(authenticate)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_a_company(
    service: Annotated[CompanyService, Depends()], identifier: Annotated[int, Path()]
) -> None:
    await service.delete_company(identifier)
