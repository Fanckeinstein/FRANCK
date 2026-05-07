# API Documentation - Unissons la Main

## Authentication Endpoints

### POST /auth/register
Register a new user
```json
{
  "username": "newuser",
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "+250789123456",
  "password": "password123",
  "confirm_password": "password123"
}
```
**Response**: 201 Created

### POST /auth/login
Login user
```json
{
  "username": "user1",
  "password": "password123",
  "remember": true
}
```
**Response**: 200 OK with redirect or `{ok: true, role: "member"}`

### POST /auth/logout
Logout current user
**Response**: Redirect to login

### GET /auth/profile
Get current user profile
**Auth**: Required

### POST /auth/profile
Update current user profile
```json
{
  "full_name": "New Name",
  "email": "newemail@example.com",
  "phone": "+250789000000",
  "old_password": "oldpass",
  "new_password": "newpass"
}
```

## Common Endpoints

### GET /
Home page
**Auth**: Not required

### GET /dashboard
Redirect to role-specific dashboard
**Auth**: Required

### GET /api/stats
Get general statistics
**Auth**: Required
**Response**:
```json
{
  "total_members": 10,
  "total_contributions": 50000.0,
  "total_loans": 20000.0,
  "treasury_balance": 30000.0
}
```

### GET /api/transactions
Get transaction history
**Auth**: Required
**Query params**: `limit` (default: 50), `offset` (default: 0)
**Response**:
```json
{
  "total": 100,
  "limit": 50,
  "offset": 0,
  "transactions": [
    {
      "id": 1,
      "type": "contribution_paid",
      "user": "John Doe",
      "amount": 1000.0,
      "description": "Contribution 2024-05",
      "date": "2024-05-01T10:00:00"
    }
  ]
}
```

## Member Endpoints

### GET /member/dashboard
Member dashboard
**Auth**: Required (Member)

### GET /member/contributions
View contribution history
**Auth**: Required (Member)

### GET /member/loans
View loans
**Auth**: Required (Member)

### GET /member/request-loan
Request loan form
**Auth**: Required (Member)

### POST /member/request-loan
Submit loan request
```json
{
  "amount": 50000,
  "reason": "Medical emergency"
}
```
**Response**: 201 Created or redirect

### POST /member/api/pay-contribution
Mark contribution as paid (Treasurer only)
```json
{
  "contribution_id": 1,
  "payment_method": "mobile_money"
}
```

## President Endpoints

### GET /president/dashboard
President dashboard
**Auth**: Required (President)

### GET /president/loans
View all loan requests
**Auth**: Required (President)
**Query params**: `status` (all, pending, approved, rejected)

### POST /president/api/loan/<id>/approve
Approve a loan
```json
{
  "repayment_days": 30,
  "approval_notes": "Approved - good standing"
}
```

### POST /president/api/loan/<id>/reject
Reject a loan
```json
{
  "reason": "Insufficient funds"
}
```

### GET /president/members
View all members
**Auth**: Required (President)

### GET /president/reports
View financial reports
**Auth**: Required (President)

## Treasurer Endpoints

### GET /tresorier/dashboard
Treasurer dashboard
**Auth**: Required (Treasurer)

### GET /tresorier/contributions
Manage contributions
**Auth**: Required (Treasurer)
**Query params**: `status` (all, pending, paid), `month` (YYYY-MM)

### POST /tresorier/api/contribution/validate
Validate a contribution
```json
{
  "contribution_id": 1,
  "payment_method": "cash",
  "payment_proof": "receipt_path"
}
```

### GET /tresorier/api/member/<member_id>/monthly-contribution
Get member monthly contribution
**Auth**: Required (Treasurer)
**Query params**: `month` (YYYY-MM)

### POST /tresorier/api/member/<member_id>/monthly-contribution
Create monthly contribution for member
**Auth**: Required (Treasurer)

### GET /tresorier/repayments
View loan repayments
**Auth**: Required (Treasurer)

### POST /tresorier/api/loan/<id>/record-repayment
Record loan repayment
```json
{
  "amount": 10000
}
```

## Secretary Endpoints

### GET /secretaire/dashboard
Secretary dashboard
**Auth**: Required (Secretary)

### GET /secretaire/monthly-report
View monthly reports
**Auth**: Required (Secretary)

### GET /secretaire/api/report/<month>
Get report for specific month
**Auth**: Required (Secretary)
**Response**:
```json
{
  "month": "2024-05",
  "contributions": [
    {
      "status": "paid",
      "count": 8,
      "amount": 8000.0
    }
  ],
  "loans_approved": 2,
  "loans_pending": 1,
  "treasury_balance": 30000.0
}
```

### GET /secretaire/history
View transaction history
**Auth**: Required (Secretary)
**Query params**: `page` (default: 1)

### GET /secretaire/api/export/<format>
Export report
**Auth**: Required (Secretary)
**Query params**: `month` (YYYY-MM)
**Formats**: csv
**Response**: CSV file download

### GET /secretaire/announcements
View announcements
**Auth**: Required (Secretary)

## Error Responses

### 400 Bad Request
```json
{
  "ok": false,
  "error": "Field is required"
}
```

### 401 Unauthorized
```json
{
  "ok": false,
  "error": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "error": "Unauthorized"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

## Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **500**: Server Error

## Authentication

All protected endpoints require:
- User to be logged in (Flask-Login session)
- Appropriate role for endpoint

## Rate Limiting

No rate limiting implemented in development mode. Implement in production.

## Pagination

Endpoints returning lists support:
- `limit`: Number of items per page (default: 50)
- `offset`: Starting position (default: 0)

Example: `/api/transactions?limit=25&offset=50`

## Data Types

- Amounts in FCFA (Francs)
- Dates in ISO 8601 format
- Roles: president, tresorier, secretaire, member
- Statuses: pending, paid, approved, rejected, overdue, repaid
