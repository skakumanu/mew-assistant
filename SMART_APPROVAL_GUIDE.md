# Smart Approval System - Parent Guide

## 🎯 Goal: Reduce Parent Overwhelm

The Smart Approval System is designed to help you spend **less time on routine decisions** while maintaining **full control** over your child's schedule.

## How It Works

### 1. **Auto-Approval Rules** ✨
Create rules once, and Mew will automatically approve similar requests:

#### Example Rules:
```
✅ Auto-approve homework sessions under 1 hour
✅ Auto-approve morning activities (6 AM - 12 PM)
✅ Auto-approve short breaks under 30 minutes
✅ Auto-approve activities at home or school
✅ Auto-approve reading time any day
```

### 2. **Learning from Your Patterns** 🧠
Mew watches your approval history and learns:
- Activities you always approve
- Times of day you're comfortable with
- Typical durations you allow
- Safe locations

**After ~10-20 approvals**, Mew will suggest auto-approval rules to save you time.

### 3. **Smart Batching** 📦
Instead of 10 separate notifications, you get organized batches:

```
⚡ URGENT (2 requests) - needs quick decision
   • Piano practice starts in 1 hour
   • Friend visit request for today

📚 HOMEWORK (4 requests) - similar activities
   • Math homework (30 min)
   • Reading assignment (45 min)
   • Science project (1 hour)
   • Spanish practice (20 min)

📅 TUESDAY (3 requests) - all for next Tuesday
   • Soccer practice change
   • Playdate at park
   • Extra tutoring session
```

**Review all 4 homework requests at once** instead of 4 separate interruptions!

## Getting Started

### Step 1: Use Mew Normally
- First week: Review all requests manually
- Mew learns your preferences
- No auto-approvals yet

### Step 2: Review Suggestions (Day 7-10)
```bash
GET /api/v1/smart-approval/suggestions
```

Mew will suggest rules like:
```json
{
  "name": "Auto-approve homework under 1 hour",
  "description": "You've approved 15 similar requests",
  "confidence": 0.92
}
```

### Step 3: Accept Rules You Trust
```bash
POST /api/v1/smart-approval/suggestions/0/accept
```

Now Mew handles routine homework requests automatically!

### Step 4: Create Custom Rules
```bash
POST /api/v1/smart-approval/rules
{
  "name": "Auto-approve morning activities",
  "rule_type": "time_range",
  "time_start": "06:00",
  "time_end": "12:00",
  "max_duration_minutes": 120
}
```

## Safety Features 🛡️

### What's NEVER Auto-Approved:
- ❌ New locations you haven't approved before
- ❌ Activities longer than your rules allow
- ❌ Late night/early morning requests (outside rules)
- ❌ High-risk activities (requires your review)
- ❌ Requests from blocked/restricted times

### You Always Have Control:
- Review auto-approvals anytime
- Override any decision
- Disable rules instantly
- See why Mew auto-approved something

## Example Parent Experience

### Without Smart Approval (Overwhelming):
```
9:00 AM  📱 "Can I do homework now?" → APPROVE
9:15 AM  📱 "Can I take a snack break?" → APPROVE  
9:45 AM  📱 "Can I practice piano?" → APPROVE
10:30 AM 📱 "Can I read?" → APPROVE
11:00 AM 📱 "Can I play outside?" → APPROVE
... 15 more notifications ...
```
**Result: 20 interruptions, constant phone checking**

### With Smart Approval (Peaceful):
```
9:00 AM  ✅ Auto-approved: Homework (30 min)
9:15 AM  ✅ Auto-approved: Snack break (10 min)
9:45 AM  ✅ Auto-approved: Piano practice (45 min)
10:30 AM ✅ Auto-approved: Reading (30 min)
11:00 AM 📱 "Friend wants to come over" → NEEDS YOUR APPROVAL

12:00 PM 📊 Daily summary: "4 auto-approved, 1 needs review"
```
**Result: 1 notification, your approval only when truly needed**

## Confidence Levels

Mew shows confidence for each decision:

- **90-100%** 🟢 Very confident (strong pattern match)
- **80-89%** 🟡 Confident (good pattern match)
- **Below 80%** 🔴 Not confident (requires your review)

## Managing Rules

### View Active Rules
```bash
GET /api/v1/smart-approval/rules
```

### Disable a Rule
```bash
DELETE /api/v1/smart-approval/rules/{rule_id}
```

### Review Batched Requests
```bash
GET /api/v1/smart-approval/batches
```

## Tips for Success

### Start Conservative
- Create narrow rules first (specific activities, times)
- Expand as you gain confidence
- Review auto-approvals weekly at first

### Use Categories
Create rules for different contexts:
- Weekday mornings (strict)
- Weekend afternoons (flexible)  
- School activities (auto-approve)
- Social activities (review required)

### Seasonal Adjustments
- Summer: More flexible rules
- School year: Structured rules
- Holidays: Temporarily disable rules

## Real Parent Stories

> "I went from 30 approval requests per day to 3-5. Game changer!" - Sarah, mom of 2

> "Love the batching! I review all homework requests during my lunch break instead of constant interruptions." - Mike, dad of 3

> "Mew learned that I always approve reading time. Now it just happens, and I get a nice summary at dinner." - Lisa, mom of 1

## FAQ

**Q: What if Mew auto-approves something I don't like?**  
A: Override it immediately! Mew learns from overrides and won't auto-approve that type again.

**Q: Can my child see auto-approval rules?**  
A: No, rules are private to parents. Kids just see "Approved" or "Needs parent review."

**Q: How do I handle exceptions?**  
A: Temporarily disable a rule, or add an expiration date to rules.

**Q: What if I'm on vacation?**  
A: Set "vacation mode" to require all approvals, or designate another adult.

## Next Steps

1. ✅ Use Mew for 1-2 weeks normally
2. ✅ Review suggested auto-approval rules
3. ✅ Accept 1-2 conservative rules
4. ✅ Monitor and adjust
5. ✅ Gradually expand automation
6. ✅ Enjoy less overwhelm! 🎉

---

**Remember**: The goal is to free your time for important decisions, not to remove you from the process. You're always in control! 💙
