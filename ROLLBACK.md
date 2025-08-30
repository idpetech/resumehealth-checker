# 🚨 EMERGENCY ROLLBACK PROCEDURES

## Phase 0 Complete Checkpoint
**Tag:** `phase-0-complete`  
**Commit:** `eeb1267`  
**Date:** August 30, 2025

---

## 🚨 IMMEDIATE ROLLBACK (Emergency)

### If Phase 1 breaks production:
```bash
# 1. Checkout the stable Phase 0 tag
git checkout phase-0-complete

# 2. Create new branch from checkpoint  
git checkout -b emergency-rollback

# 3. Force push to main (EMERGENCY ONLY)
git push --force origin main

# 4. Verify deployment
curl https://web-production-f7f3.up.railway.app/health

# 5. Test payment flow
open https://web-production-f7f3.up.railway.app/
```

### Railway Auto-Deploy Verification:
- Railway will detect the force push within ~2 minutes
- Check Railway dashboard for deployment status
- Verify production URL is responding
- Test file upload and free analysis

---

## 🔄 SELECTIVE ROLLBACK (Specific Features)

### Revert Recent Changes Only:
```bash
# See recent commits
git log --oneline -10

# Revert specific problematic commit
git revert <commit-hash>

# Push the revert
git push origin main
```

### Cherry-Pick Critical Fixes:
```bash
# If rolling back but need to keep critical fixes
git cherry-pick eeb1267  # Premium leakage fix
git cherry-pick b2bba92  # Retry mechanism for slow connections
git cherry-pick 8c505eb  # Premium analysis leakage issues
```

---

## 📋 CONFIGURATION ROLLBACK

### Pricing Configuration:
```bash
# Revert pricing configs to Phase 0 state
git checkout phase-0-complete -- pricing_config.json
git checkout phase-0-complete -- pricing_config_staging.json
git add pricing_config*.json
git commit -m "Rollback: Revert pricing configs to Phase 0"
git push
```

### Environment Variables (Railway):
If environment variables need rollback:
1. Go to Railway dashboard
2. Navigate to project settings
3. Restore these Phase 0 values:
```bash
OPENAI_API_KEY=sk-...
STRIPE_PAYMENT_URL=https://buy.stripe.com/8x2cN4cC823I3qFcPWfMA02
STRIPE_PAYMENT_SUCCESS_TOKEN=payment_success_123
```

### Stripe Payment Link Rollback:
- Payment Link: `https://buy.stripe.com/8x2cN4cC823I3qFcPWfMA02`
- Success URL: `https://web-production-f7f3.up.railway.app/?payment_token=payment_success_123`
- If needed, create new Payment Link with exact same settings

---

## 🧪 POST-ROLLBACK TESTING

### Critical Tests After Rollback:
1. **Health Check**: `curl https://web-production-f7f3.up.railway.app/health`
2. **File Upload**: Test PDF/DOCX upload functionality
3. **Free Analysis**: Verify 3 major issues + upgrade prompt
4. **Payment Flow**: Test Stripe integration end-to-end
5. **Premium Analysis**: Verify comprehensive analysis delivery
6. **Geographic Pricing**: Test different country pricing
7. **Error Handling**: Test retry mechanism for slow connections

### Expected Phase 0 Behavior:
- ✅ Free analysis shows 3 issues + score + teaser
- ✅ Premium upgrade redirects to Stripe Payment Link
- ✅ Payment completion delivers comprehensive analysis
- ✅ Geographic pricing works for all 7 regions
- ✅ Slow connections get retry mechanism (up to 3 minutes)
- ✅ No premium leakage on free requests

---

## 🔐 DATA SAFETY

### What's Safe to Rollback:
- ✅ Application code (main_vercel.py)
- ✅ Pricing configurations
- ✅ UI/UX changes  
- ✅ Payment flow logic

### What Requires Careful Handling:
- ⚠️ Database changes (Phase 1+ only)
- ⚠️ User account data (Phase 1+ only) 
- ⚠️ Stripe webhook configurations
- ⚠️ Environment variable changes

### Rollback Impact:
- **Zero Data Loss**: Phase 0 is stateless (no database)
- **Payment History**: Preserved in Stripe dashboard
- **User Files**: Not stored server-side (in-memory processing)
- **Analytics**: Railway logs preserved

---

## 📞 EMERGENCY CONTACTS

### If Rollback Fails:
1. **Railway Platform**: Check dashboard for deployment errors
2. **GitHub Repository**: Verify commits and branches
3. **Stripe Dashboard**: Ensure Payment Links are active
4. **OpenAI Status**: Check API service status

### Recovery Commands:
```bash
# Nuclear option: Reset to exact Phase 0 state
git reset --hard phase-0-complete
git push --force origin main

# Verify clean state
git status
git log --oneline -5
```

---

## 🎯 PHASE 1 SAFETY STRATEGY

### Recommended Approach:
1. **Branch Development**: All Phase 1 work in `phase-1-development` branch
2. **Feature Flags**: Gradual rollout of new features
3. **Staging Testing**: Full testing before production merge
4. **Database Migrations**: With rollback procedures
5. **Backup Strategy**: Regular backups before major changes

### Pre-Phase 1 Checklist:
- [ ] Phase 0 checkpoint confirmed working
- [ ] Rollback procedures tested
- [ ] Team trained on emergency procedures
- [ ] Monitoring and alerting setup
- [ ] Staging environment ready

---

**🚨 Remember: Phase 0 is your stable fallback. When in doubt, rollback to `phase-0-complete` tag.**