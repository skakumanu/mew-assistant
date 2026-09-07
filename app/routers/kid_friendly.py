"""
Kid-Friendly Router
Provides simplified, age-appropriate endpoints for children to interact with Mew
"""

from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..database.models import (
    ApprovalRequest,
    ChangeKind,
    RequestType,
    ScheduledSession,
    User,
)
from ..schemas.change_request import ChangeRequestOut, KidCardOut, KidTodayOut
from ..schemas.kid_friendly import (
    EmojiReaction,
    KidActivitySuggestion,
    KidScheduleRequest,
    KidScheduleResponse,
    SimplifiedResponse,
)
from ..services.approval_service import ApprovalService
from ..services.change_request_service import ChangeRequestService
from ..services.kid_service import KidService
from ..services.notification_service import NotificationService
from ..services.presenter import Presenter
from ..services.ruleset_service import RuleSetService
from ..utils.auth import get_current_user, verify_kid_account
from ..utils.content_filter import ContentFilter
from ..utils.locale import from_local, to_local
from ..utils.locale_context import translator_for

router = APIRouter(prefix="/kid", tags=["Kid-Friendly"])

# "Later, please" is one fixed step, so the button means the same thing
# every time it is pressed. Two taps per request, never a time picker.
LATER_STEP_MINUTES = 90

# How far back the "calm days in a row" streak is allowed to count.
MAX_STREAK_DAYS = 60


@router.post("/suggest-activity", response_model=SimplifiedResponse)
async def suggest_activity(
    request: KidActivitySuggestion,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kid suggests a new activity to parent
    - Uses simple, encouraging language
    - Returns emoji-based feedback
    - Creates parent approval request (NO DIRECT CHANGES TO CALENDAR)
    """
    verify_kid_account(current_user)

    # Filter content for appropriateness
    content_filter = ContentFilter()
    if not content_filter.is_kid_safe(request.activity_description):
        return SimplifiedResponse(
            success=False, message="Let's use nice words! 😊 Try again?", emoji="🤔"
        )

    kid_service = KidService(db)
    approval_service = ApprovalService(db)

    # Get parent
    parent = kid_service.get_parent(current_user.id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No parent account linked"
        )

    # Create approval request - DOES NOT change calendar yet
    approval_request = approval_service.create_approval_request(
        kid_id=current_user.id,
        parent_id=parent.id,
        request_type=RequestType.NEW_EVENT,
        requested_activity=request.activity_name,
        requested_time=request.when.value,
        reason=request.activity_description,
        emoji=request.emoji,
    )

    # use fallback if parent's display_name is None
    parent_name = (parent.display_name or "your parent") if parent else "your parent"

    return SimplifiedResponse(
        success=True,
        # keep lines short for flake8 E501
        message=(
            "Great idea! 🎉 I'll ask " + parent_name + " about " + request.activity_name + "!"
        ),
        emoji="✅",
        data={
            "request_id": approval_request.id,
            "suggestion_id": approval_request.id,
            "status": "waiting_for_parent",
            "note": "Your parent will review this soon!",
        },
    )


@router.get("/my-schedule", response_model=KidScheduleResponse)
async def get_my_schedule(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get kid's schedule in simple, visual format
    - Shows activities with emoji
    - Uses simple time descriptions (morning, afternoon, evening)
    - Highlights fun activities
    """
    verify_kid_account(current_user)

    kid_service = KidService(db)
    schedule = kid_service.get_kid_schedule(current_user.id)

    return KidScheduleResponse(
        greeting=f"Hi {current_user.display_name}! 👋",
        today=schedule.get("today", []),
        tomorrow=schedule.get("tomorrow", []),
        this_week=schedule.get("this_week", []),
        fun_fact=kid_service.get_daily_fun_fact(),
    )


@router.post("/react", response_model=SimplifiedResponse)
async def react_to_schedule(
    reaction: EmojiReaction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Let kids react to scheduled activities with emoji
    - Helps parents understand kid's preferences
    - Tracks emotional responses
    - No typing required, just emoji selection
    """
    verify_kid_account(current_user)

    kid_service = KidService(db)
    notification_service = NotificationService(db)

    # Record reaction
    kid_service.record_activity_reaction(
        kid_id=current_user.id,
        activity_id=reaction.activity_id,
        emoji=reaction.emoji,
        feeling=reaction.feeling,
    )

    # If negative reaction, notify parent
    if reaction.emoji in ["😢", "😟", "😰", "😡"]:
        parent = kid_service.get_parent(current_user.id)
        if parent:
            notification_service.notify_parent_of_kid_concern(
                parent_id=parent.id,
                kid_name=current_user.display_name,
                activity_id=reaction.activity_id,
                emoji=reaction.emoji,
            )

    responses = {
        "😊": "I'm so glad you're happy! 🌟",
        "😍": "Yay! That's awesome! 🎉",
        "😢": "I'm sorry you feel sad. Your parent will know. 💙",
        "😟": "It's okay to feel worried. Let's tell your parent. 🤗",
        "😴": "Rest is important! Maybe we can reschedule? 💤",
        "🤩": "Super excited! This will be fun! ✨",
    }

    return SimplifiedResponse(
        success=True,
        message=responses.get(reaction.emoji, "Thanks for sharing! 💕"),
        emoji="💙",
    )


@router.post("/change-request", response_model=SimplifiedResponse)
async def request_schedule_change(
    request: KidScheduleRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kid requests to change or skip an activity.

    When the activity is a scheduled session, the request goes through the
    rule engine: anything that fits the parent's rules is applied right away
    and the kid is told it is done. A cancellation still reaches the parent
    whenever they asked for that (``cancellation_needs_approval``).

    Free-form suggestions that are not tied to a session keep the older
    always-ask behaviour, because there is nothing to evaluate.
    """
    verify_kid_account(current_user)

    kid_service = KidService(db)
    approval_service = ApprovalService(db)

    scheduled = (
        db.query(ScheduledSession)
        .filter(
            ScheduledSession.id == request.activity_id,
            ScheduledSession.child_id == current_user.id,
            ScheduledSession.is_cancelled.is_(False),
        )
        .first()
    )
    if scheduled is not None:
        return await _change_scheduled_session(scheduled, request, http_request, current_user, db)

    # Get parent
    parent = kid_service.get_parent(current_user.id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No parent account linked"
        )

    # Determine request type based on whether there's an alternative
    request_type = RequestType.SCHEDULE_CHANGE if request.alternative else RequestType.SKIP_ACTIVITY

    # Create approval request - DOES NOT change calendar yet
    change_request = approval_service.create_approval_request(
        kid_id=current_user.id,
        parent_id=parent.id,
        request_type=request_type,
        activity_id=request.activity_id,
        requested_activity=request.alternative,
        reason=request.reason.value,
        emoji="🤔",
    )

    parent_name = (parent.display_name or "your parent") if parent else "your parent"

    return SimplifiedResponse(
        success=True,
        # keep lines short for flake8 E501
        message=("Got it! 👍 I'll ask " + parent_name + " about this. No changes yet!"),
        emoji="📝",
        data={
            "request_id": change_request.id,
            "status": "waiting_for_parent",
            "note": "Your schedule won't change until your parent approves!",
        },
    )


async def _change_scheduled_session(
    scheduled: ScheduledSession,
    request: KidScheduleRequest,
    http_request: Request,
    current_user: User,
    db: Session,
) -> SimplifiedResponse:
    """Run a kid's change request through the rule engine."""
    wants_to_skip = request.alternative is None
    kind = ChangeKind.CANCEL if wants_to_skip else ChangeKind.MOVE
    new_start = (
        None if wants_to_skip else scheduled.start_utc + timedelta(minutes=LATER_STEP_MINUTES)
    )

    outcome = await ChangeRequestService(db).submit(
        actor=current_user,
        session_id=scheduled.id,
        kind=kind,
        new_start=new_start,
    )

    translator = translator_for(http_request.headers.get("accept-language"), current_user, db)
    tz_name = RuleSetService(db).timezone_for_child(current_user.id)

    if outcome.auto_applied:
        message = (
            translator.t("kid.parent_yes_skip", title=outcome.session.title)
            if kind is ChangeKind.CANCEL
            else translator.t(
                "kid.done",
                title=outcome.session.title,
                time=translator.time(to_local(outcome.session.start_utc, tz_name)),
            )
        )
        return SimplifiedResponse(
            success=True,
            message=message,
            emoji="",
            data={
                "request_id": outcome.request.id if outcome.request else None,
                "status": "done",
                "session_id": outcome.session.id,
                "start_utc": outcome.session.start_utc.isoformat(),
            },
        )

    return SimplifiedResponse(
        success=True,
        message=translator.t("kid.asked_skip" if wants_to_skip else "kid.asked"),
        emoji="",
        data={
            "request_id": outcome.request.id if outcome.request else None,
            "status": "waiting_for_parent",
            "session_id": outcome.session.id,
        },
    )


class KidAsk(BaseModel):
    """
    The kid's two buttons.

    The same two, every time, in the same place: "Later, please" and
    "Not today". No free text, no time picker, no third option.
    """

    session_id: int
    ask: str = Field(..., description="later | skip")


@router.post("/ask", response_model=ChangeRequestOut)
async def ask_about_a_session(
    ask: KidAsk,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ask for a later time, or to skip today.

    Asking is always okay. If the request fits the parent's rules it simply
    happens and the kid is told so; if it does not, the parent gets a card
    and the kid is told an answer is coming. The kid never sees a rule.
    """
    verify_kid_account(current_user)

    if ask.ask not in ("later", "skip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ask must be 'later' or 'skip'",
        )

    service = ChangeRequestService(db)
    session = db.query(ScheduledSession).filter(ScheduledSession.id == ask.session_id).first()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if ask.ask == "later":
        kind = ChangeKind.MOVE
        new_start = session.start_utc + timedelta(minutes=LATER_STEP_MINUTES)
    else:
        kind = ChangeKind.CANCEL
        new_start = None

    outcome = await service.submit(
        actor=current_user,
        session_id=ask.session_id,
        kind=kind,
        new_start=new_start,
    )

    translator = translator_for(http_request.headers.get("accept-language"), current_user, db)
    presenter = Presenter(translator, db)
    tz_name = RuleSetService(db).timezone_for_child(current_user.id)

    if outcome.auto_applied:
        message = (
            translator.t("kid.parent_yes_skip", title=outcome.session.title)
            if kind is ChangeKind.CANCEL
            else translator.t(
                "kid.done",
                title=outcome.session.title,
                time=translator.time(to_local(outcome.session.start_utc, tz_name)),
            )
        )
        return ChangeRequestOut(
            auto_applied=True,
            session=presenter.session(outcome.session),
            request_id=outcome.request.id if outcome.request else None,
            message=message,
        )

    # Reason codes are deliberately NOT rendered for the kid: they are
    # returned so the parent's card can show them, never the kid's screen.
    return ChangeRequestOut(
        auto_applied=False,
        session=presenter.session(outcome.session),
        request_id=outcome.request.id if outcome.request else None,
        reason_codes=outcome.reason_codes,
        alternatives=[],
        message=translator.t("kid.asked_skip" if kind is ChangeKind.CANCEL else "kid.asked"),
    )


@router.get("/today", response_model=KidTodayOut)
async def get_today(
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Today's cards, in one column, in plain sentences.

    One reading order, no emoji, and the two ask buttons on every card that
    can still be changed. A card whose request is still open shows a status
    strip in place of the buttons rather than moving anything.
    """
    verify_kid_account(current_user)

    translator = translator_for(http_request.headers.get("accept-language"), current_user, db)
    presenter = Presenter(translator, db)
    service = ChangeRequestService(db)
    tz_name = RuleSetService(db).timezone_for_child(current_user.id)

    # "Today" is the kid's own day, not UTC's - an evening class stored as
    # past-midnight UTC is still this evening for them.
    now_utc = datetime.utcnow()
    now_local = to_local(now_utc, tz_name)
    day_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end_local = day_start_local + timedelta(days=1)
    day_start = from_local(day_start_local, tz_name)
    day_end = from_local(day_end_local, tz_name)
    sessions = service.sessions_for_child(current_user.id, day_start, day_end)

    cards: List[KidCardOut] = []
    for session in sessions:
        pending = service.pending_for_session(session.id)
        status_text = None
        if pending is not None:
            status_text = translator.t(
                "kid.asked_skip" if pending.change_kind == ChangeKind.CANCEL.value else "kid.asked"
            )
        cards.append(
            KidCardOut(
                session_id=session.id,
                title=session.title,
                time_label=translator.time(to_local(session.start_utc, tz_name)),
                person=session.person.display_name if session.person else "",
                initial=(session.title or "?")[:1].upper(),
                tile_index=presenter.tile_index(session),
                can_ask=pending is None and session.start_utc > now_utc,
                status_text=status_text,
                symbols=presenter.kid_card_symbols(session),
            )
        )

    count = len(cards)
    return KidTodayOut(
        greeting=translator.t("kid.my_day"),
        day_label=f"{translator.day_name(now_local)}, {translator.date_label(now_local)}",
        count_label=translator.t("kid.things_today", count=count),
        streak_label=translator.t(
            "kid.calm_days", count=_calm_streak(db, current_user.id, tz_name)
        ),
        cards=cards,
        note=translator.t("kid.note"),
        locale=translator.code,
        dir=translator.dir,
    )


def _calm_streak(db: Session, kid_id: int, tz_name: str) -> int:
    """
    Consecutive days back from today with nothing parked for a parent.

    The design maps the old sticker collection onto this: a calm day is a
    day where every request cleared the rules on its own. Days are the
    kid's own calendar days, not UTC's, so a request parked late in the
    evening still counts against the day it happened for them.
    """
    parked_days = {
        to_local(row.created_at, tz_name).date()
        for row in db.query(ApprovalRequest)
        .filter(
            ApprovalRequest.kid_id == kid_id,
            ApprovalRequest.auto_applied.is_(False),
            ApprovalRequest.created_at >= datetime.utcnow() - timedelta(days=MAX_STREAK_DAYS),
        )
        .all()
        if row.created_at is not None
    }

    today = to_local(datetime.utcnow(), tz_name).date()
    streak = 0
    while streak < MAX_STREAK_DAYS:
        if (today - timedelta(days=streak)) in parked_days:
            break
        streak += 1
    return streak


@router.get("/stickers", response_model=dict)
async def get_sticker_collection(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Gamification: Kids earn stickers for completing activities
    - Visual rewards for task completion
    - Encourages participation
    - Makes scheduling fun
    """
    verify_kid_account(current_user)

    kid_service = KidService(db)
    stickers = kid_service.get_sticker_collection(current_user.id)

    return {
        "total_stickers": stickers["count"],
        "stickers": stickers["collection"],
        "next_reward": stickers["next_reward"],
        # shorten long line to avoid E501
        "message": ("You have " + str(stickers["count"]) + " stickers! Keep it up! 🌟"),
    }


@router.post("/help", response_model=SimplifiedResponse)
async def ask_for_help(
    message: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kid can ask for help in simple language
    - Content filtered for safety
    - Alerts parent if help is needed
    - Provides immediate, supportive response
    """
    verify_kid_account(current_user)

    content_filter = ContentFilter()
    notification_service = NotificationService(db)
    kid_service = KidService(db)

    # Check for safety concerns
    if content_filter.detect_distress(message):
        parent = kid_service.get_parent(current_user.id)
        if parent:
            notification_service.alert_parent_urgent(
                parent_id=parent.id,
                kid_name=current_user.display_name,
                message=message,
                priority="high",
            )

        return SimplifiedResponse(
            success=True,
            message="I'm here for you. Your parent will help you right away. 💙",
            emoji="🤗",
        )

    # Regular help request
    parent = kid_service.get_parent(current_user.id)
    if parent:
        notification_service.notify_parent_help_request(
            parent_id=parent.id, kid_name=current_user.display_name, message=message
        )

    return SimplifiedResponse(
        success=True,
        message="I let your parent know you need help! They'll be with you soon. 💕",
        emoji="👍",
    )
