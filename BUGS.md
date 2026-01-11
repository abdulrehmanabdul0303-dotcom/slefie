# 🐛 Bug Tracking Log

## Bug #001: Duplicate Password Reset Function
**Status**: ✅ FIXED  
**Impact**: HIGH - Password reset emails had wrong URLs  
**Root Cause**: `send_password_reset_email()` function defined twice in `apps/users/services.py`, second definition overwrote the first  
**Fix**: Removed duplicate function, kept feature-complete version with proper FRONTEND_URL  
**Proof**: Password reset now generates correct frontend URLs  
**Fixed By**: External review  
**Date**: January 10, 2026  

## Bug #002: Token Blacklist Not Working
**Status**: ✅ FIXED  
**Impact**: MEDIUM - Logout didn't properly blacklist refresh tokens  
**Root Cause**: `rest_framework_simplejwt.token_blacklist` missing from INSTALLED_APPS  
**Fix**: Added to INSTALLED_APPS, requires migration  
**Proof**: Logout now properly blacklists tokens  
**Fixed By**: External review  
**Date**: January 10, 2026  

## Bug #003: Login 400 Error Poor UX
**Status**: ✅ FIXED  
**Impact**: HIGH - Users confused by generic 400 errors on login  
**Root Cause**: Frontend not properly handling email verification error responses  
**Fix**: Enhanced error parsing and added resend verification functionality  
**Proof**: Users now see clear "Email not verified" message with resend option  
**Fixed By**: Internal development  
**Date**: January 10, 2026  

---

## 🔍 Bug Report Template
```
## Bug #XXX: [Title]
**Status**: 🔍 INVESTIGATING / 🔧 IN PROGRESS / ✅ FIXED  
**Impact**: LOW/MEDIUM/HIGH - [Description]  
**Root Cause**: [What caused it]  
**Fix**: [What was changed]  
**Proof**: [How we verified the fix]  
**Fixed By**: [Team member]  
**Date**: [Date]  
```

## 📊 Bug Statistics
- **Total Bugs**: 3
- **Fixed**: 3
- **Open**: 0
- **Critical**: 0
- **High Impact**: 2
- **Medium Impact**: 1