from datetime import date, datetime
from enum import StrEnum
from typing import Annotated, Any, Iterable, Self

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer

from entity.record_interface import RecordInterface


class RecordV2Field(StrEnum):
    """Updatable fields on RecordV2. Values match SQL column names exactly.

    Used by RecordV2QueryBuilder to constrain which columns can appear in
    INSERT/UPDATE statements. Add or remove members here to control access.
    """
    RECORD_ID = "record_id"
    COMPANY_ID = "company_id"
    POLICY_START_DATE = "policy_start_date"
    POLICY_END_DATE = "policy_end_date"
    POLICY_STATUS = "policy_status"
    CREATED_AT = "created_at"
    LAST_UPDATED = "last_updated"
    POLICY_TIER = "policy_tier"
    POLICY_DOMAIN = "policy_domain"

_DATE_FORMATS = ["%Y-%m-%d", "%m-%d-%Y", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"]
_DATETIME_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%m-%d-%Y %H:%M:%S",
    "%m/%d/%Y %H:%M:%S",
]

_ISO_DATE_FMT = "%Y-%m-%d"
_ISO_DATETIME_FMT = "%Y-%m-%dT%H:%M:%S"


def _parse_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse '{value}' as a date. Accepted formats: {_DATE_FORMATS}")


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse '{value}' as a datetime. Accepted formats: {_DATETIME_FORMATS}")


FlexDate = Annotated[
    date,
    BeforeValidator(_parse_date),
    PlainSerializer(lambda d: d.strftime(_ISO_DATE_FMT), return_type=str),
]

FlexDatetime = Annotated[
    datetime,
    BeforeValidator(_parse_datetime),
    PlainSerializer(lambda dt: dt.strftime(_ISO_DATETIME_FMT), return_type=str),
]


class RecordV2(BaseModel, RecordInterface):
    """A v2 policy record with structured fields. Dates and datetimes are normalized to ISO 8601.

    Example:
        record = RecordV2(
            row_id=1,
            record_id=42,
            company_id=7,
            policy_start_date="01-01-2026",
            policy_end_date="2026-07-31",
            policy_status="ACTIVE",
            created_at="2026-01-01T00:00:00",
            last_updated="2026-01-01 12:00:00",
            policy_tier="STANDARD",
            policy_domain="COMMERCIAL",
        )
    """

    model_config = ConfigDict(populate_by_name=True)

    id: int | None = Field(default=None, alias="row_id", description="Identification number in database")
    record_id: int = Field(..., description="Identification number of the policy")
    company_id: int = Field(..., description="Identification number of the company")
    policy_start_date: FlexDate = Field(..., description="Date the policy becomes effective")
    policy_end_date: FlexDate = Field(..., description="Date the policy expires")
    policy_status: str = Field(..., description="Current status of the policy, e.g. ACTIVE, EXPIRED")
    created_at: FlexDatetime | None = Field(default=None, description="Timestamp when the record was created")
    last_updated: FlexDatetime | None = Field(default=None, description="Timestamp of the most recent update")
    policy_tier: str = Field(..., description="Tier level of the policy, e.g. STANDARD, PREMIUM")
    policy_domain: str = Field(..., description="Domain or line of business, e.g. COMMERCIAL, PERSONAL")

    def clone(self) -> Self:
        """Returns a deep copy so mutations don't affect the stored record."""
        return self.model_copy(deep=True)
