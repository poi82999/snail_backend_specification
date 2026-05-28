from enum import StrEnum


class ActorType(StrEnum):
    USER = "user"
    OWNER = "owner"
    ADMIN = "admin"
    SYSTEM = "system"


class VerificationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Visibility(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    HIDDEN = "hidden"


class PaymentMethod(StrEnum):
    ON_SITE = "on_site"
    BANK_TRANSFER_GUIDE = "bank_transfer_guide"


class AiAnalysisStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class ReservationStatus(StrEnum):
    PENDING = "pending"
    PAYMENT_PENDING = "payment_pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CANCELLED_BY_USER = "cancelled_by_user"
    CANCELLED_BY_SHOP = "cancelled_by_shop"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class AssignedBy(StrEnum):
    USER = "user"
    AUTO = "auto"
    OWNER = "owner"


class LlmJobType(StrEnum):
    TRANSFORM = "transform"
    CLASSIFY = "classify"
    EMBED = "embed"
    REANALYZE = "reanalyze"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class NotificationChannel(StrEnum):
    APNS = "apns"
    KAKAO_ALIMTALK = "kakao_alimtalk"
    OWNER_INBOX = "owner_inbox"


class NotificationStatus(StrEnum):
    QUEUED = "queued"
    RETRYING = "retrying"
    SENT = "sent"
    FAILED = "failed"


class ReportTargetType(StrEnum):
    SNAP = "snap"
    COMMENT = "comment"
    REVIEW = "review"
    USER = "user"
    SHOP = "shop"


class ReportStatus(StrEnum):
    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"


class ReportAction(StrEnum):
    NONE = "none"
    HIDE = "hide"
    DELETE = "delete"
    BAN = "ban"


class UploadTargetType(StrEnum):
    PROFILE = "profile"
    SHOP = "shop"
    DESIGN = "design"
    SNAP = "snap"
    REVIEW = "review"
    BUSINESS_LICENSE = "business_license"
