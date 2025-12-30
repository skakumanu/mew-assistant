"""
Kid-Friendly Router
Provides simplified, age-appropriate endpoints for children to interact with Mew
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..database.models import RequestType, User
from ..schemas.kid_friendly import (
    EmojiReaction,
    KidActivitySuggestion,
    KidScheduleRequest,
    KidScheduleResponse,
    SimplifiedResponse,
)
from ..services.approval_service import ApprovalService
from ..services.kid_service import KidService
from ..services.notification_service import NotificationService
from ..utils.auth import get_current_user, verify_kid_account
from ..utils.content_filter import ContentFilter

router = APIRouter(prefix="/kid", tags=["Kid-Friendly"])


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
            "Great idea! 🎉 I'll ask "
            + parent_name
            + " about "
            + request.activity_name
            + "!"
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Kid requests to change or skip an activity
    - Simple reason selection (tired, don't feel good, want different activity)
    - Sends request to parent for approval
    - IMPORTANT: Changes are NOT made until parent approves
    - Uses encouraging, supportive language
    """
    verify_kid_account(current_user)

    kid_service = KidService(db)
    approval_service = ApprovalService(db)

    # Get parent
    parent = kid_service.get_parent(current_user.id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No parent account linked"
        )

    # Determine request type based on whether there's an alternative
    request_type = (
        RequestType.SCHEDULE_CHANGE
        if request.alternative
        else RequestType.SKIP_ACTIVITY
    )

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
