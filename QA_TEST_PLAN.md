# 🧪 PhotoVault QA Test Plan

## 🔐 Authentication Tests

### Test Case: User Registration
**Steps**:
1. POST `/api/auth/register/` with valid data
2. Check email for verification link
3. Verify email via link or API

**Expected**: 201 Created, user created with `email_verified=false`  
**Status**: ✅ PASS  

### Test Case: Login with Unverified Email
**Steps**:
1. Attempt login with unverified account
2. Check error message

**Expected**: 400 with clear "Email not verified" message  
**Status**: ✅ PASS  

### Test Case: Login with Verified Email
**Steps**:
1. Verify email first
2. Login with correct credentials

**Expected**: 200 with access_token and refresh_token  
**Status**: ✅ PASS  

### Test Case: Token Refresh
**Steps**:
1. Use refresh token to get new access token

**Expected**: 200 with new access_token  
**Status**: ⏳ PENDING  

### Test Case: Logout & Token Blacklist
**Steps**:
1. Logout with refresh token
2. Try to use blacklisted token

**Expected**: Token should be blacklisted and unusable  
**Status**: ⏳ PENDING (requires migration)  

### Test Case: Account Lockout
**Steps**:
1. Make 5 failed login attempts
2. Try correct password

**Expected**: Account should be locked temporarily  
**Status**: ⏳ PENDING  

## 📸 Media Management Tests

### Test Case: Image Upload
**Steps**:
1. Upload valid image file
2. Check file storage and database entry

**Expected**: File stored, MediaAsset created  
**Status**: ⏳ PENDING  

### Test Case: Upload Validation
**Steps**:
1. Try uploading non-image file
2. Try uploading oversized file

**Expected**: Proper validation errors  
**Status**: ⏳ PENDING  

### Test Case: Thumbnail Generation
**Steps**:
1. Upload image
2. Check if thumbnail is generated

**Expected**: Thumbnail created automatically  
**Status**: ⏳ PENDING  

## 📁 Album Management Tests

### Test Case: Create Album
**Steps**:
1. Create new album
2. Add images to album

**Expected**: Album created, images associated  
**Status**: ⏳ PENDING  

### Test Case: Album RBAC
**Steps**:
1. Create album as Owner
2. Add member as Viewer
3. Try to delete image as Viewer

**Expected**: Viewer should be blocked from deletion  
**Status**: ⏳ PENDING  

## 🔗 Sharing System Tests

### Test Case: Create Share Token
**Steps**:
1. Create share token for album
2. Access via token

**Expected**: Token provides access to album  
**Status**: ⏳ PENDING  

### Test Case: Share Token Expiry
**Steps**:
1. Create token with short expiry
2. Wait for expiry
3. Try to access

**Expected**: Access should be denied after expiry  
**Status**: ⏳ PENDING  

### Test Case: View Limit
**Steps**:
1. Create token with view limit
2. Exceed view limit

**Expected**: Access denied after limit reached  
**Status**: ⏳ PENDING  

## 🔒 Security Tests

### Test Case: Rate Limiting
**Steps**:
1. Make rapid requests to auth endpoints
2. Check if rate limiting kicks in

**Expected**: Requests should be throttled  
**Status**: ⏳ PENDING  

### Test Case: Unauthorized Access
**Steps**:
1. Try accessing protected endpoints without token
2. Try accessing other user's data

**Expected**: 401/403 errors  
**Status**: ⏳ PENDING  

## 📊 Test Summary
- **Total Test Cases**: 15
- **Passed**: 3
- **Pending**: 12
- **Failed**: 0

## 🎯 Priority Testing Queue
1. **HIGH**: Token blacklist (requires migration)
2. **HIGH**: Media upload & validation
3. **MEDIUM**: Album RBAC permissions
4. **MEDIUM**: Share token functionality
5. **LOW**: Rate limiting verification