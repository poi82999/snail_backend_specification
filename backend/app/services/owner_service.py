from http import HTTPStatus
from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.models.accounts import BusinessVerification, Owner
from app.models.enums import ActorType, UploadTargetType, VerificationStatus
from app.models.ops import UploadObject
from app.schemas.owners import BusinessVerificationSubmit, OwnerUpdate
from app.utils.storage import upload_public_url


async def get_me(session: AsyncSession, owner_id: UUID) -> Owner:
    owner = await session.get(Owner, owner_id)
    if owner is None or not owner.is_active:
        raise AppError("OWNER_NOT_FOUND", "사장님 계정을 찾을 수 없습니다.", HTTPStatus.NOT_FOUND)
    return owner


async def update_me(session: AsyncSession, owner_id: UUID, payload: OwnerUpdate) -> Owner:
    owner = await get_me(session, owner_id)
    if payload.representative_name is not None:
        owner.representative_name = payload.representative_name
    if payload.phone_number is not None:
        owner.phone_number = payload.phone_number
    await session.flush()
    return owner


async def submit_business_verification(
    session: AsyncSession, owner_id: UUID, payload: BusinessVerificationSubmit
) -> BusinessVerification:
    await get_me(session, owner_id)
    upload = await session.scalar(
        select(UploadObject).where(
            UploadObject.object_key == payload.document_object_key,
            UploadObject.owner_actor_type == ActorType.OWNER.value,
            UploadObject.owner_actor_id == owner_id,
            UploadObject.target_type == UploadTargetType.BUSINESS_LICENSE,
        )
    )
    if upload is None:
        raise AppError(
            "UPLOAD_NOT_FOUND",
            "사업자등록증 업로드 파일을 찾을 수 없습니다.",
            HTTPStatus.NOT_FOUND,
        )

    document_url = upload_public_url(upload)
    verification = BusinessVerification(
        id=uuid4(),
        owner_id=owner_id,
        business_registration_number=payload.business_registration_number,
        document_url=document_url,
        status=VerificationStatus.PENDING,
    )
    session.add(verification)
    await session.flush()
    await session.refresh(verification)
    return verification


async def get_latest_business_verification(
    session: AsyncSession, owner_id: UUID
) -> BusinessVerification:
    await get_me(session, owner_id)
    verification = await session.scalar(
        select(BusinessVerification)
        .where(BusinessVerification.owner_id == owner_id)
        .order_by(desc(BusinessVerification.created_at), desc(BusinessVerification.id))
        .limit(1)
    )
    if verification is None:
        raise AppError(
            "BUSINESS_VERIFICATION_NOT_FOUND",
            "사업자 인증 제출 내역이 없습니다.",
            HTTPStatus.NOT_FOUND,
        )
    return verification
