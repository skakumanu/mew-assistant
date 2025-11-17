"""
Smart Approval Router
Endpoints for intelligent approval management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.approval import (
    ApprovalRuleCreate,
    ApprovalRuleResponse,
    ApprovalBatch,
    RuleSuggestion
)
from app.services.smart_approval_service import SmartApprovalService
from app.utils.auth import get_current_user
from app.database.models import User

router = APIRouter(prefix="/api/v1/smart-approval", tags=["Smart Approval"])


@router.get("/batches", response_model=List[ApprovalBatch])
async def get_approval_batches(
    min_batch_size: int = 3,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get intelligently batched approval requests for efficient review.
    
    Reduces overwhelm by grouping similar requests.
    """
    service = SmartApprovalService(db)
    batches = await service.batch_pending_requests(current_user, min_batch_size)
    return batches


@router.post("/rules", response_model=ApprovalRuleResponse)
async def create_auto_approval_rule(
    rule_data: ApprovalRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a custom auto-approval rule.
    
    Example rules:
    - Auto-approve homework requests under 1 hour
    - Auto-approve morning activities
    - Auto-approve specific locations (home, school)
    """
    service = SmartApprovalService(db)
    rule = await service.create_auto_approval_rule(
        current_user,
        rule_data.dict()
    )
    return rule


@router.get("/rules", response_model=List[ApprovalRuleResponse])
async def get_auto_approval_rules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active auto-approval rules."""
    from app.database.models import ApprovalRule
    rules = db.query(ApprovalRule).filter(
        ApprovalRule.user_id == current_user.id,
        ApprovalRule.is_active == True
    ).all()
    return rules


@router.delete("/rules/{rule_id}")
async def delete_auto_approval_rule(
    rule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable an auto-approval rule."""
    from app.database.models import ApprovalRule
    rule = db.query(ApprovalRule).filter(
        ApprovalRule.id == rule_id,
        ApprovalRule.user_id == current_user.id
    ).first()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    rule.is_active = False
    db.commit()
    
    return {"message": "Rule disabled successfully"}


@router.get("/suggestions", response_model=List[RuleSuggestion])
async def get_rule_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered suggestions for auto-approval rules based on your history.
    
    Mew learns from your approval patterns and suggests rules to save you time.
    """
    service = SmartApprovalService(db)
    suggestions = await service.suggest_rules_from_history(current_user)
    return suggestions


@router.post("/suggestions/{index}/accept")
async def accept_rule_suggestion(
    index: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a suggested auto-approval rule."""
    service = SmartApprovalService(db)
    suggestions = await service.suggest_rules_from_history(current_user)
    
    if index >= len(suggestions):
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    suggestion = suggestions[index]
    rule = await service.create_auto_approval_rule(current_user, suggestion)
    
    return {
        "message": "Rule created successfully",
        "rule": rule
    }
