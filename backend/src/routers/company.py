from typing import Annotated

from fastapi import APIRouter, Depends, Path, status

from src.core.dependencies import authenticate
from src.core.security import Auth
from src.routers.query_options import (
    FiltersQuery,
    PageNumberQuery,
    PageSizeQuery,
    SortQuery,
)
from src.schemas.common import PageQueryParams, PaginatedResponse
from src.schemas.company import CompanyBase, CompanyOut, CompanyPatch
from src.services.company import CompanyService

# pylint: disable=too-many-arguments

router = APIRouter(prefix="/companies")


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_companies(
    *,
    service: Annotated[CompanyService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    sort: SortQuery,
    filters: FiltersQuery,
    page_size: PageSizeQuery = 10,
    page_number: PageNumberQuery = 1,
) -> PaginatedResponse[CompanyOut]:
    current_user.authorize("read_company")
    return await service.paginate(
        CompanyOut,
        PageQueryParams(
            sort=sort,
            filters=filters,
            page_size=page_size,
            page_number=page_number,
        ),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_a_company(
    service: Annotated[CompanyService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    company_in: CompanyBase,
) -> CompanyOut:
    current_user.authorize("create_company")
    return await service.create_company(company_in)


@router.put("/{identifier}", status_code=status.HTTP_200_OK)
async def update_a_company(
    service: Annotated[CompanyService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
    company_in: CompanyBase,
) -> CompanyOut:
    current_user.authorize("update_company")
    return await service.update_company(identifier, company_in)


@router.patch("/{identifier}", status_code=status.HTTP_200_OK)
async def patch_a_company(
    service: Annotated[CompanyService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
    company_in: CompanyPatch,
) -> CompanyOut:
    current_user.authorize("update_company")
    return await service.patch_company(identifier, company_in)


@router.get("/{identifier}", status_code=status.HTTP_200_OK)
async def retrieve_a_company(
    service: Annotated[CompanyService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
) -> CompanyOut:
    current_user.authorize("read_company")
    return await service.get_company(identifier)


@router.delete("/{identifier}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_a_company(
    service: Annotated[CompanyService, Depends()],
    current_user: Annotated[Auth, Depends(authenticate)],
    identifier: Annotated[int, Path()],
) -> None:
    current_user.authorize("delete_company")
    await service.delete_company(identifier)
