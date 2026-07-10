from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..dependencies import get_session, require_read, require_write
from ..models import (
    ApiCredential,
    ApiPlan,
    ApiRequestLog,
    DeveloperApplication,
    WebhookDelivery,
    WebhookEvent,
    WebhookSubscription,
)
from ..schemas import (
    ApiCredentialIssue,
    ApiCredentialIssued,
    ApiCredentialRead,
    CredentialRevoke,
    DeveloperApplicationCreate,
    DeveloperApplicationRead,
    DeveloperApplicationUpdate,
    DeveloperPlatformStats,
    WebhookDispatchResult,
    WebhookEventCreate,
    WebhookEventRead,
)
from ..services.developers import (
    create_application,
    dispatch_pending_webhooks,
    get_application_or_404,
    issue_credential,
    publish_webhook_event,
    revoke_credential,
    update_application,
    usage_summary,
)

router = APIRouter(prefix="/v1/developer", tags=["Developer Platform Administration"])


@router.get(
    "/plans",
    dependencies=[Depends(require_read)],
)
def get_api_plans(
    include_internal: bool = False,
    db: Session = Depends(get_session),
):
    filters = [ApiPlan.active.is_(True)]
    if not include_internal:
        filters.append(ApiPlan.public.is_(True))
    return list(
        db.scalars(
            select(ApiPlan)
            .where(*filters)
            .order_by(ApiPlan.sort_order, ApiPlan.name)
        ).all()
    )


@router.get(
    "/applications",
    response_model=list[DeveloperApplicationRead],
    dependencies=[Depends(require_write)],
)
def get_developer_applications(
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_session),
):
    filters = []
    if status_value:
        filters.append(DeveloperApplication.status == status_value)
    return list(
        db.scalars(
            select(DeveloperApplication)
            .where(*filters)
            .order_by(DeveloperApplication.created_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/applications",
    response_model=DeveloperApplicationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_developer_application(
    payload: DeveloperApplicationCreate,
    db: Session = Depends(get_session),
):
    return create_application(db, payload)


@router.get(
    "/applications/{application_id}",
    response_model=DeveloperApplicationRead,
    dependencies=[Depends(require_write)],
)
def get_developer_application(
    application_id: str,
    db: Session = Depends(get_session),
):
    return get_application_or_404(db, application_id)


@router.patch(
    "/applications/{application_id}",
    response_model=DeveloperApplicationRead,
    dependencies=[Depends(require_write)],
)
def patch_developer_application(
    application_id: str,
    payload: DeveloperApplicationUpdate,
    db: Session = Depends(get_session),
):
    return update_application(db, application_id, payload)


@router.get(
    "/applications/{application_id}/credentials",
    response_model=list[ApiCredentialRead],
    dependencies=[Depends(require_write)],
)
def get_application_credentials(
    application_id: str,
    db: Session = Depends(get_session),
):
    get_application_or_404(db, application_id)
    return list(
        db.scalars(
            select(ApiCredential)
            .where(ApiCredential.application_id == application_id)
            .order_by(ApiCredential.created_at.desc())
        ).all()
    )


@router.post(
    "/applications/{application_id}/credentials",
    response_model=ApiCredentialIssued,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_application_credential(
    application_id: str,
    payload: ApiCredentialIssue,
    response: Response,
    db: Session = Depends(get_session),
):
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return issue_credential(db, application_id, payload)


@router.post(
    "/credentials/{credential_id}/revoke",
    response_model=ApiCredentialRead,
    dependencies=[Depends(require_write)],
)
def post_revoke_credential(
    credential_id: str,
    payload: CredentialRevoke,
    db: Session = Depends(get_session),
):
    return revoke_credential(db, credential_id, payload.revoked_by)


@router.get(
    "/applications/{application_id}/usage",
    dependencies=[Depends(require_write)],
)
def get_application_usage(
    application_id: str,
    credential_id: str | None = None,
    days: int = Query(default=30, ge=1, le=366),
    db: Session = Depends(get_session),
):
    return usage_summary(
        db,
        application_id=application_id,
        credential_id=credential_id,
        days=days,
    )


@router.get(
    "/events",
    response_model=list[WebhookEventRead],
    dependencies=[Depends(require_write)],
)
def get_webhook_events(
    status_value: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_session),
):
    filters = []
    if status_value:
        filters.append(WebhookEvent.status == status_value)
    return list(
        db.scalars(
            select(WebhookEvent)
            .where(*filters)
            .order_by(WebhookEvent.created_at.desc())
            .limit(limit)
        ).all()
    )


@router.post(
    "/events",
    response_model=WebhookEventRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_write)],
)
def post_webhook_event(
    payload: WebhookEventCreate,
    db: Session = Depends(get_session),
):
    return publish_webhook_event(db, payload)


@router.post(
    "/webhooks/dispatch",
    response_model=WebhookDispatchResult,
    dependencies=[Depends(require_write)],
)
def post_dispatch_webhooks(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_session),
):
    return dispatch_pending_webhooks(
        db,
        master_secret=request.app.state.settings.webhook_signing_secret,
        timeout=request.app.state.settings.webhook_delivery_timeout,
        limit=limit,
    )


@router.get(
    "/stats",
    response_model=DeveloperPlatformStats,
    dependencies=[Depends(require_write)],
)
def developer_platform_stats(db: Session = Depends(get_session)):
    def count(model) -> int:
        return int(db.scalar(select(func.count()).select_from(model)) or 0)

    status_rows = db.execute(
        select(ApiRequestLog.status_code, func.count(ApiRequestLog.id))
        .group_by(ApiRequestLog.status_code)
        .order_by(ApiRequestLog.status_code)
    ).all()
    path_rows = db.execute(
        select(ApiRequestLog.path, func.count(ApiRequestLog.id))
        .group_by(ApiRequestLog.path)
        .order_by(func.count(ApiRequestLog.id).desc())
        .limit(50)
    ).all()

    active_credentials = int(
        db.scalar(
            select(func.count(ApiCredential.id)).where(
                ApiCredential.status == "active"
            )
        )
        or 0
    )
    return DeveloperPlatformStats(
        plans=count(ApiPlan),
        applications=count(DeveloperApplication),
        active_credentials=active_credentials,
        public_api_requests=count(ApiRequestLog),
        webhook_subscriptions=count(WebhookSubscription),
        webhook_events=count(WebhookEvent),
        webhook_deliveries=count(WebhookDelivery),
        requests_by_status={str(key): int(value) for key, value in status_rows},
        requests_by_path={key: int(value) for key, value in path_rows},
    )
