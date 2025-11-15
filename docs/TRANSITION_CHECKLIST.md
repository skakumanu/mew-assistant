# Repository Transition Checklist

## Pre-Transition (Do This First)

### Legal Setup
- [ ] Choose organization name
- [ ] File Articles of Incorporation
- [ ] Obtain EIN from IRS
- [ ] Apply for 501(c)(3) status (can operate while pending)
- [ ] Open nonprofit bank account
- [ ] Obtain insurance

### Governance
- [ ] Recruit board members (minimum 3)
- [ ] Adopt bylaws
- [ ] Hold first board meeting
- [ ] Pass resolution to accept repository transfer
- [ ] Adopt all required policies

### Infrastructure
- [ ] Register domain (e.g., mew-foundation.org)
- [ ] Setup nonprofit email (Google/Microsoft)
- [ ] Create website
- [ ] Setup donation platform

## GitHub Organization Setup

### Create Organization
- [ ] Create GitHub organization
- [ ] Choose organization name (e.g., mew-foundation)
- [ ] Select "Nonprofit" organization type
- [ ] Add organization profile picture/logo
- [ ] Fill in organization bio
- [ ] Add website URL
- [ ] Add contact email

### Configure Organization Settings
- [ ] Enable two-factor authentication requirement
- [ ] Set base permissions to "Read"
- [ ] Enable dependency graph
- [ ] Enable Dependabot alerts
- [ ] Enable Dependabot security updates
- [ ] Configure branch protection rules
- [ ] Setup team structure

### Team Structure
```
Owners
├── Board members
└── Executive director

Core Maintainers
├── Lead developer(s)
└── Senior contributors

Contributors
├── Regular contributors
└── Community moderators

Community
└── All members (read access)
```

## Repository Updates (Before Transfer)

### Code Updates
- [ ] Update all hardcoded references
  ```bash
  # Find all references
  grep -r "skakumanu" .
  
  # Update Python files
  find . -name "*.py" -exec sed -i 's/skakumanu/mew-foundation/g' {} +
  
  # Update markdown files
  find . -name "*.md" -exec sed -i 's/skakumanu/mew-foundation/g' {} +
  
  # Update YAML files
  find . -name "*.yml" -o -name "*.yaml" -exec sed -i 's/skakumanu/mew-foundation/g' {} +
  ```

### Documentation Updates
- [ ] Update README.md
  - [ ] Add foundation information
  - [ ] Update repository URLs
  - [ ] Update contact information
  - [ ] Add governance section
- [ ] Update CONTRIBUTING.md
  - [ ] Update maintainer info
  - [ ] Add foundation contact
- [ ] Update LICENSE
  - [ ] Change copyright holder to foundation name
  - [ ] Update year
- [ ] Update CODE_OF_CONDUCT.md
  - [ ] Update contact email
- [ ] Update SECURITY.md
  - [ ] Update security contact
  - [ ] Add foundation security policy link

### Configuration Updates
- [ ] Update package.json (if applicable)
  - [ ] Update repository URL
  - [ ] Update author/organization
  - [ ] Update homepage
  - [ ] Update bugs URL
- [ ] Update setup.py/pyproject.toml
  - [ ] Update author
  - [ ] Update maintainer
  - [ ] Update URL
- [ ] Update docker-compose.yml
  - [ ] Update image names
  - [ ] Update labels
- [ ] Update GitHub Actions workflows
  - [ ] Update secrets references
  - [ ] Update deployment targets
  - [ ] Update notification channels

### GitHub Repository Settings
- [ ] Update repository description
- [ ] Add topics/tags
- [ ] Update website URL
- [ ] Setup GitHub Sponsors
- [ ] Configure issue templates
- [ ] Configure PR templates
- [ ] Add funding.yml
- [ ] Update social preview image

## Transfer Process

### Backup Everything
```bash
# Create full backup
git clone --mirror https://github.com/skakumanu/mew-assistant.git
cd mew-assistant.git
git bundle create mew-assistant-backup.bundle --all

# Backup issues, PRs, wiki (use GitHub CLI)
gh issue list --limit 1000 --json number,title,body > issues-backup.json
gh pr list --limit 1000 --json number,title,body > prs-backup.json
```

### Transfer Repository
1. Go to repository Settings
2. Scroll to "Danger Zone"
3. Click "Transfer ownership"
4. Enter organization name: `mew-foundation`
5. Type repository name to confirm
6. Click "I understand, transfer this repository"

### Post-Transfer Verification
- [ ] Verify all files transferred
- [ ] Check all branches present
- [ ] Verify issues transferred
- [ ] Verify pull requests transferred
- [ ] Check GitHub Actions still work
- [ ] Verify webhooks updated
- [ ] Test CI/CD pipeline
- [ ] Verify deployments work

## Update External Services

### Cloud Services
- [ ] Update Azure subscriptions
  - [ ] Transfer ownership to nonprofit account
  - [ ] Apply for Azure nonprofit credits
  - [ ] Update resource group ownership
  - [ ] Update Key Vault access policies
- [ ] Update AWS (if using)
  - [ ] Apply for AWS nonprofit credits
- [ ] Update monitoring services
  - [ ] Update Sentry organization
  - [ ] Update logging services

### Integration Services
- [ ] Update webhook URLs
- [ ] Update API callback URLs
- [ ] Update OAuth redirect URLs
- [ ] Update email service (SendGrid/Twilio)
- [ ] Update SMS service (Twilio)
- [ ] Update payment processor (Stripe)
- [ ] Update analytics (Google Analytics)

### Domain & DNS
- [ ] Update DNS records
- [ ] Update SSL certificates
- [ ] Update email forwarding
- [ ] Setup new domain
- [ ] Redirect old URLs (if applicable)

### Communication Platforms
- [ ] Update Slack organization
- [ ] Update Discord server
- [ ] Update mailing lists
- [ ] Update social media handles

## Update Contributors

### Notify Current Contributors
```markdown
Subject: Important: Repository Transfer to Mew Foundation

Dear Contributors,

We're excited to announce that the mew-assistant repository is 
transitioning to the Mew Foundation, a 501(c)(3) nonprofit 
organization dedicated to supporting special needs families.

**What's Changing:**
- Repository location: github.com/mew-foundation/mew-assistant
- All contribution rights and licenses remain the same
- Project governance moving to nonprofit board

**What's NOT Changing:**
- Open source license (MIT)
- Project mission and goals
- Your contributions and credit
- Community guidelines

**Action Required:**
- Update your git remotes:
  git remote set-url origin git@github.com:mew-foundation/mew-assistant.git
- Update any bookmarks
- Join our new community channels

**Questions?**
Email: info@mew-foundation.org

Thank you for your continued support!
The Mew Foundation Team
```

### Update Contributor Agreements
- [ ] Create Contributor License Agreement (CLA)
- [ ] Setup CLA bot (CLA Assistant)
- [ ] Grandfather existing contributors
- [ ] Document contribution process

## Update Access & Permissions

### GitHub Permissions
- [ ] Add board members as Owners
- [ ] Add maintainers to Core team
- [ ] Review all collaborator access
- [ ] Remove former owner (keep as emeritus?)
- [ ] Setup branch protections
- [ ] Configure required reviews

### Secrets & Credentials
- [ ] Rotate all API keys
- [ ] Update GitHub secrets
- [ ] Update deployment keys
- [ ] Transfer Azure Key Vault ownership
- [ ] Update service principal credentials
- [ ] Rotate database passwords
- [ ] Update OAuth secrets

### Access Management
- [ ] Document who has access to what
- [ ] Create access control matrix
- [ ] Setup MFA requirements
- [ ] Configure SSO (if needed)
- [ ] Setup audit logging

## Financial Transition

### Costs & Billing
- [ ] Transfer Azure subscription
- [ ] Transfer domain registration
- [ ] Transfer hosting services
- [ ] Setup nonprofit billing
- [ ] Apply for nonprofit discounts
- [ ] Update payment methods

### Apply for Credits/Grants
- [ ] Azure nonprofit credits ($3,500/year)
- [ ] AWS nonprofit credits
- [ ] GitHub Sponsors
- [ ] Google for Nonprofits
- [ ] Microsoft nonprofit programs
- [ ] Twilio nonprofit credits

## Communication Plan

### Internal Communication
- [ ] Announce to core team
- [ ] Brief board members
- [ ] Update staff (if any)
- [ ] Notify advisors

### External Communication
- [ ] Post announcement in README
- [ ] Create blog post
- [ ] Update website
- [ ] Social media announcement
- [ ] Email newsletter
- [ ] Press release (optional)

### Community Engagement
- [ ] Host community call
- [ ] Q&A session
- [ ] Update FAQ
- [ ] Create transition guide

## Legal & Compliance

### Update Legal Documents
- [ ] Review all contracts
- [ ] Update terms of service
- [ ] Update privacy policy
- [ ] Update data processing agreements
- [ ] Update vendor agreements
- [ ] Update employment agreements (if any)

### Intellectual Property
- [ ] Transfer trademarks (if any)
- [ ] Update copyright notices
- [ ] Document IP ownership
- [ ] Review patent applications (if any)
- [ ] Update domain ownership

### Compliance Documentation
- [ ] Update HIPAA documentation
- [ ] Update COPPA compliance
- [ ] Update GDPR policies
- [ ] Update state privacy laws compliance
- [ ] Review accessibility compliance

## Post-Transition

### Week 1
- [ ] Monitor for issues
- [ ] Respond to community questions
- [ ] Fix any broken links
- [ ] Update search engine listings
- [ ] Verify all services working

### Week 2-4
- [ ] Conduct post-mortem
- [ ] Document lessons learned
- [ ] Update procedures
- [ ] Thank contributors
- [ ] Plan celebration/launch event

### Month 2-3
- [ ] Review analytics
- [ ] Assess impact
- [ ] Gather feedback
- [ ] Optimize processes
- [ ] Plan next steps

## Rollback Plan (If Needed)

### If Transfer Fails
1. Contact GitHub support
2. Use backup bundle to restore
3. Re-transfer issues/PRs if needed
4. Restore configurations

### If Major Issues Arise
1. Document issues
2. Assess impact
3. Consider temporary revert
4. Fix issues
5. Re-attempt transfer

## Success Criteria

- [ ] Repository fully functional at new location
- [ ] All CI/CD pipelines working
- [ ] No broken links or references
- [ ] Contributors can access and contribute
- [ ] Services and integrations working
- [ ] Community informed and supportive
- [ ] Legal compliance maintained
- [ ] Zero downtime for users

## Timeline

| Week | Activities |
|------|------------|
| -4 | Legal setup begins |
| -2 | Update documentation |
| -1 | Notify community |
| 0 | Execute transfer |
| +1 | Monitor and fix issues |
| +2 | Post-mortem and celebration |

## Emergency Contacts

```yaml
GitHub Support: support@github.com
Azure Support: [your azure contact]
Domain Registrar: [support contact]
Legal Counsel: [attorney contact]
Board Chair: [email]
Technical Lead: [email]
```

## Notes

- Keep original owner as emeritus contributor
- Maintain credit for all historical contributions
- Preserve project history and documentation
- Be transparent about the transition
- Celebrate this milestone with community!

---

**Remember:** This is a significant positive step for the project. 
Take your time, communicate clearly, and ensure a smooth transition 
for everyone involved.

Good luck! 🎉
