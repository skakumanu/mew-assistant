# Mew Assistant Non-Profit Organization Setup Guide

## Executive Summary
This guide outlines the steps to establish Mew Assistant as a non-profit organization focused on supporting special needs families through technology.

---

## Phase 1: Organization Formation (Weeks 1-4)

### 1.1 Choose Organization Name
**Recommended Options:**
- **Mew Foundation** (Simple, memorable)
- **Special Families Technology Foundation**
- **Accessible Care Foundation**
- **Mew Special Needs Foundation**

**Action Items:**
- [ ] Check name availability at Secretary of State
- [ ] Check domain availability (.org preferred)
- [ ] Trademark search (optional but recommended)

### 1.2 Select Organization Type
**Recommended: 501(c)(3) Public Charity**

**Benefits:**
- Tax-exempt status
- Donors can deduct contributions
- Grants and foundation funding eligible
- Public trust and credibility

**Requirements:**
- Serve charitable purpose
- Primarily serve public benefit
- File Form 1023 or 1023-EZ with IRS
- Annual Form 990 filing

### 1.3 Form Incorporation
**Steps:**
1. File Articles of Incorporation with your state
2. Draft Bylaws (template provided below)
3. Obtain EIN from IRS
4. Register with state Attorney General

**Cost Estimate:** $100-500 (varies by state)

---

## Phase 2: IRS Tax-Exempt Status (Weeks 5-16)

### 2.1 Prepare Form 1023-EZ or 1023
**1023-EZ (Streamlined) - $275**
- For organizations with <$50k annual revenue
- Assets <$250k
- Faster processing (2-4 weeks)

**1023 (Standard) - $600**
- Detailed application
- For larger organizations
- Processing: 3-6 months

**Recommendation:** Start with 1023-EZ

### 2.2 Required Documentation
- [ ] Mission statement
- [ ] Program descriptions
- [ ] Financial projections (3 years)
- [ ] Governance policies
- [ ] Conflict of interest policy
- [ ] Bylaws

---

## Phase 3: Governance Structure

### 3.1 Board of Directors
**Minimum Requirements:**
- 3 board members (most states)
- Independent members (not related/employed)
- Diverse expertise recommended

**Recommended Initial Board:**
1. **Founder/President** - Technology & product vision
2. **Special Needs Advocate** - Parent or professional
3. **Legal/Compliance Expert** - Attorney or compliance professional
4. **Financial Officer** - CPA or financial professional
5. **Medical/Therapy Expert** - Therapist, doctor, or special ed professional

### 3.2 Advisory Board (Optional)
- Technical advisors
- Medical professionals
- Special needs educators
- Parent representatives
- Funding experts

### 3.3 Officers
**Required:**
- President/Executive Director
- Secretary
- Treasurer

**Responsibilities:**
- Strategic direction
- Financial oversight
- Legal compliance
- Fundraising
- Community engagement

---

## Phase 4: GitHub Organization Setup

### 4.1 Create GitHub Organization
```bash
# 1. Create organization at github.com/organizations/new
Organization name: mew-foundation (or chosen name)
Contact email: info@mew-foundation.org
Plan: Free (or Team for private repos)

# 2. Transfer repository
# Settings → Transfer ownership → mew-foundation
```

### 4.2 Organization Settings
```yaml
# Recommended settings:
- Base permissions: Read
- Two-factor authentication: Required
- Default branch protection: Enabled
- Code review requirements: 1 approval minimum
- Status checks: Required
```

### 4.3 Team Structure
```
mew-foundation/
├── Owners (Board members)
├── Core Maintainers (Write access)
├── Contributors (Triage access)
└── Community (Read access)
```

### 4.4 Update Repository Settings
- [ ] Update organization in README.md
- [ ] Update LICENSE copyright holder
- [ ] Update CONTRIBUTING.md
- [ ] Update CODE_OF_CONDUCT.md
- [ ] Update security contact
- [ ] Update funding links

---

## Phase 5: Operations Setup

### 5.1 Financial Infrastructure
**Bank Account:**
- [ ] Open non-profit bank account
- [ ] Requires EIN
- [ ] Consider online options (Mercury for Nonprofits, Bluevine)

**Accounting:**
- [ ] QuickBooks Nonprofit (free/discounted)
- [ ] Wave Accounting (free)
- [ ] Hire bookkeeper (as needed)

### 5.2 Insurance
**Recommended Coverage:**
- General Liability: $1-2M
- Directors & Officers (D&O): $1M+
- Cyber Liability: $1M+ (critical for health data)
- Professional Liability: $1M+

**Estimated Cost:** $2,000-5,000/year

### 5.3 Legal Infrastructure
- [ ] Obtain legal counsel (pro bono options available)
- [ ] Draft contractor agreements
- [ ] Create volunteer agreements
- [ ] Data processing agreements (for vendors)
- [ ] Business associate agreements (HIPAA)

---

## Phase 6: Compliance & Policies

### 6.1 Required Policies
1. **Conflict of Interest Policy** ✓ (Already created)
2. **Whistleblower Policy** ✓ (Already created)
3. **Document Retention Policy** ✓ (Already created)
4. **Privacy Policy** ✓ (Already in app)
5. **Data Security Policy** ✓ (Already created)
6. **Investment Policy** (if holding reserves)
7. **Gift Acceptance Policy** (for donations)

### 6.2 Annual Compliance
- [ ] Form 990 (IRS) - Due 5.5 months after fiscal year end
- [ ] State annual report/renewal
- [ ] State charitable solicitation registration
- [ ] Business licenses (if required)
- [ ] Insurance renewals

### 6.3 Ongoing Governance
- [ ] Quarterly board meetings (minimum)
- [ ] Annual financial audit (if >$750k revenue)
- [ ] Annual conflict of interest disclosures
- [ ] Regular policy reviews

---

## Phase 7: Fundraising Setup

### 7.1 Online Donation Platform
**Options:**
- **GitHub Sponsors** (0% fee for non-profits)
- **Open Collective** (Fiscal host option)
- **Donorbox** (1.75% + payment processing)
- **Stripe/PayPal** (Direct integration)

### 7.2 Grant Opportunities
**Foundation Grants:**
- Robert Wood Johnson Foundation (health)
- Autism Speaks (if autism focus)
- United Cerebral Palsy (if applicable)
- Local community foundations

**Corporate Grants:**
- Microsoft Nonprofit Grants ($3,500+)
- Google.org Impact Challenge
- AWS Nonprofit Credits ($2,000+)
- GitHub Sponsors Matching Fund

**Government Grants:**
- SBIR/STTR programs
- State disability services grants
- Health department grants

### 7.3 Fundraising Registration
- [ ] Register in home state
- [ ] Register in states where soliciting (varies)
- [ ] Some states require audit/financial disclosure

---

## Phase 8: Community Building

### 8.1 Website & Branding
- [ ] Register domain (.org)
- [ ] Create professional website
- [ ] Develop brand guidelines
- [ ] Create social media presence

### 8.2 Communication Channels
- [ ] Mailing list (Mailchimp Nonprofit - free up to 15k subscribers)
- [ ] Discord/Slack for community
- [ ] Twitter/X for updates
- [ ] LinkedIn for professional network
- [ ] YouTube for demos/education

### 8.3 Partnerships
- [ ] Special needs organizations
- [ ] Therapy providers
- [ ] Schools and education systems
- [ ] Healthcare organizations
- [ ] Technology companies

---

## Phase 9: Technology Infrastructure

### 9.1 Domain & Email
```bash
# Register domain
Domain: mew-foundation.org
Registrar: Namecheap, Google Domains, Cloudflare

# Email setup (free options)
- Google Workspace for Nonprofits (free)
- Microsoft 365 for Nonprofits (free/discounted)

# Email structure
info@mew-foundation.org
contact@mew-foundation.org
security@mew-foundation.org
board@mew-foundation.org
```

### 9.2 Cloud Infrastructure
**Azure for Nonprofits:**
- Apply through TechSoup
- $3,500/year in Azure credits
- Additional enterprise licenses

**AWS Nonprofit Credits:**
- $2,000 promotional credits
- Additional credits through programs

### 9.3 Software & Tools
**Free/Discounted for Nonprofits:**
- GitHub Team/Enterprise (free)
- Atlassian (75% discount)
- Slack (85% discount)
- Zoom (free upgrade)
- Canva (free)
- Adobe Creative Cloud (discounted)

---

## Phase 10: Launch & Operations

### 10.1 Soft Launch Checklist
- [ ] 501(c)(3) status approved
- [ ] Bank account opened
- [ ] Insurance in place
- [ ] Website live
- [ ] GitHub org transferred
- [ ] Board established
- [ ] Policies adopted
- [ ] Donation system live

### 10.2 Public Launch
- [ ] Press release
- [ ] Social media announcement
- [ ] Community outreach
- [ ] Partner announcements
- [ ] Grant applications
- [ ] Conference submissions

### 10.3 Sustainability Plan
**Year 1 Focus:**
- Build core team
- Establish product-market fit
- Secure initial funding ($50k-100k)
- Onboard 100-500 families

**Year 2-3 Focus:**
- Scale to 1,000+ families
- Hire staff (1-3 FTE)
- Diversify funding sources
- Build partnerships

---

## Budget Estimates

### Setup Costs (One-Time)
| Item | Cost |
|------|------|
| State incorporation | $100-500 |
| IRS 1023-EZ filing | $275 |
| Legal consultation | $500-2,000 (or pro bono) |
| Initial insurance | $2,000-5,000 |
| Website development | $500-2,000 |
| Domain registration | $20/year |
| **Total Setup** | **$3,395-9,795** |

### Annual Operating Costs (Year 1)
| Item | Cost |
|------|------|
| Insurance renewal | $2,000-5,000 |
| Cloud hosting (Azure credits) | $0-500 |
| Domain/email | $100-500 |
| Accounting/bookkeeping | $500-2,000 |
| Legal (ongoing) | $1,000-3,000 |
| Marketing/outreach | $500-2,000 |
| State compliance | $100-500 |
| **Total Year 1** | **$4,200-13,500** |

### Scaling Costs (Year 2-3)
| Item | Cost |
|------|------|
| Executive Director (PT) | $30,000-50,000 |
| Developer (PT/FT) | $40,000-80,000 |
| Operations overhead | $10,000-20,000 |
| **Total Year 2-3** | **$80,000-150,000** |

---

## Funding Strategy

### Phase 1: Bootstrap ($10k-25k)
- Personal investment
- Friends & family
- Small grants (<$10k)
- GitHub Sponsors
- Crowdfunding (GoFundMe, Kickstarter)

### Phase 2: Foundation Grants ($25k-100k)
- Local community foundations
- Health-focused foundations
- Technology for good grants
- Corporate giving programs

### Phase 3: Major Funding ($100k+)
- Government grants
- Large foundations
- Corporate partnerships
- Individual major donors

---

## Sample Bylaws Template

```markdown
# BYLAWS OF MEW FOUNDATION

## ARTICLE I - NAME AND PURPOSE

**Section 1.1 Name**
The name of this corporation is Mew Foundation ("Corporation").

**Section 1.2 Purpose**
The Corporation is organized exclusively for charitable and educational 
purposes under Section 501(c)(3) of the Internal Revenue Code, specifically 
to provide accessible technology solutions for special needs families.

## ARTICLE II - BOARD OF DIRECTORS

**Section 2.1 Powers**
The Board of Directors shall manage the affairs of the Corporation.

**Section 2.2 Number**
The Board shall consist of no fewer than three (3) and no more than 
eleven (11) directors.

**Section 2.3 Terms**
Directors shall serve staggered three-year terms.

**Section 2.4 Meetings**
The Board shall meet at least quarterly.

## ARTICLE III - OFFICERS

**Section 3.1 Officers**
Officers shall include President, Secretary, and Treasurer.

**Section 3.2 Duties**
[Standard officer duties]

## ARTICLE IV - CONFLICTS OF INTEREST

[Conflict of interest policy]

## ARTICLE V - AMENDMENTS

These bylaws may be amended by two-thirds vote of the Board.
```

---

## Resources & Next Steps

### Legal Resources
- **NOLO** - Legal forms and guides
- **Pro Bono Net** - Free legal help
- **Lawyers Alliance for New York** - Free services
- **Your state's volunteer lawyers program**

### Formation Services
- **Harbor Compliance** - Nonprofit formation ($499+)
- **LegalZoom** - Nonprofit formation ($299+)
- **DIY** - File yourself (cheapest)

### Recommended Reading
- "Starting & Building a Nonprofit" by Peri Pakroo
- "Nonprofit Kit For Dummies" by Stan Hutton
- IRS Publication 557 "Tax-Exempt Status"

### Support Organizations
- **National Council of Nonprofits** - ncnonprofits.org
- **Foundation Center** - foundationcenter.org
- **TechSoup** - techsoup.org (discounted software)
- **Nonprofit Hub** - nonprofithub.org

---

## Immediate Action Items

### Week 1-2: Planning
- [ ] Choose organization name
- [ ] Research state requirements
- [ ] Draft mission statement
- [ ] Identify potential board members
- [ ] Budget approval

### Week 3-4: Formation
- [ ] File Articles of Incorporation
- [ ] Draft Bylaws
- [ ] Obtain EIN
- [ ] Open bank account
- [ ] First board meeting

### Week 5-8: IRS Application
- [ ] Prepare Form 1023-EZ
- [ ] Gather supporting documents
- [ ] Submit application
- [ ] Wait for approval

### Week 9-12: Infrastructure
- [ ] Create GitHub organization
- [ ] Transfer repository
- [ ] Setup website
- [ ] Establish donation system
- [ ] Launch communications

---

## Transition Plan for Current Repository

### Step 1: Prepare Repository
```bash
# Update all references
find . -type f -name "*.md" -exec sed -i 's/skakumanu/mew-foundation/g' {} +
find . -type f -name "*.py" -exec sed -i 's/skakumanu/mew-foundation/g' {} +

# Update LICENSE
# Change copyright holder to "Mew Foundation"

# Update README.md
# Add foundation information
```

### Step 2: Create GitHub Organization
1. Go to github.com/organizations/new
2. Choose "Create a free organization"
3. Organization name: `mew-foundation`
4. Contact email: Your current email
5. This organization belongs to: "A nonprofit"

### Step 3: Transfer Repository
1. Go to repository Settings
2. Scroll to "Danger Zone"
3. Click "Transfer ownership"
4. Enter: `mew-foundation`
5. Confirm transfer

### Step 4: Update Settings
```bash
# Clone from new location
git clone git@github.com:mew-foundation/mew-assistant.git

# Update remotes in existing clone
git remote set-url origin git@github.com:mew-foundation/mew-assistant.git
```

### Step 5: Communicate Change
- Post announcement in README
- Update social media
- Notify contributors
- Update documentation

---

## Timeline Summary

| Phase | Duration | Key Milestones |
|-------|----------|----------------|
| Planning | 2 weeks | Name, board, budget |
| Formation | 2 weeks | Incorporation, EIN |
| IRS Application | 4-16 weeks | 501(c)(3) approval |
| Infrastructure | 4 weeks | GitHub, website, systems |
| Soft Launch | 2 weeks | Testing, validation |
| Public Launch | Ongoing | Growth, funding |

**Total Timeline: 3-6 months to full operation**

---

## Questions? Need Help?

Feel free to reach out for guidance on any of these steps. This is a significant undertaking, but incredibly rewarding for the special needs community you'll serve.

**Remember:** Start small, stay focused on mission, and build sustainably!
