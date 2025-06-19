# Authentication System Documentation

## Overview
The GB-APP now includes a complete authentication system with user login, registration, and password management capabilities.

## Components Implemented

### 1. Database Model
- **File**: `models/user.py`
- **Table**: `users`
- **Fields**:
  - `id` (Primary Key)
  - `username` (Unique, required)
  - `email` (Unique, required)
  - `password_hash` (hashed passwords using Werkzeug)
  - `is_active` (Boolean, default True)
  - `created_at` (DateTime)
  - `updated_at` (DateTime)
  - `last_login` (DateTime)

### 2. Controller
- **File**: `controllers/login_controller.py`
- **Routes**:
  - `/login` - Login page with username/password
  - `/register` - User registration
  - `/change-password` - Change password for logged-in users
  - `/logout` - Logout and clear session
  - `/check-username` - AJAX endpoint for username availability
  - `/check-email` - AJAX endpoint for email availability

### 3. Templates
- **Login**: `templates/auth/login.html`
  - Modern gradient design
  - Username/password fields
  - Link to registration
  - Flash message support

- **Registration**: `templates/auth/register.html`
  - Real-time validation
  - Username availability check
  - Email format validation
  - Password strength indicator
  - Confirm password matching

- **Change Password**: `templates/auth/change_password.html`
  - Current password verification
  - New password with strength indicator
  - Confirm new password
  - User info display

### 4. Authentication Middleware
- **File**: `app.py`
- **Function**: `require_login()`
- **Behavior**:
  - Protects all routes except login/register/static
  - Redirects unauthenticated users to login page
  - Maintains user session

### 5. User Interface Integration
- **Header**: Updated `templates/index.html`
- **Features**:
  - User dropdown menu in header
  - Change password link
  - Logout option
  - Current user display

## Default Users Created

### Admin User
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@gb-app.com`
- **Note**: Change password immediately after first login

### Test User
- **Username**: `testuser`
- **Password**: `test123`
- **Email**: `test@gb-app.com`

## Security Features

### Password Security
- Passwords are hashed using Werkzeug's `generate_password_hash()`
- Minimum password length: 6 characters
- Password strength indicator in registration
- Secure password verification

### Session Management
- Flask sessions for user authentication
- Session data includes `user_id` and `username`
- Automatic session cleanup on logout

### Input Validation
- Username: Minimum 3 characters, uniqueness check
- Email: Format validation, uniqueness check
- Password: Minimum length, confirmation matching
- Real-time AJAX validation on registration

### CSRF Protection
- Flask's built-in CSRF protection via forms
- Session-based security

## Database Setup

### Migration Script
- **File**: `create_users_table.py`
- **Purpose**: Creates users table and default users
- **Usage**: `python create_users_table.py`

### Manual Database Query
```sql
-- Create users table manually if needed
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME
);
```

## Usage Instructions

### For Administrators
1. **First Login**:
   - Navigate to `/login`
   - Login with `admin` / `admin123`
   - Immediately change password via user dropdown

2. **Create New Users**:
   - Direct users to `/register`
   - Or create users programmatically

3. **User Management**:
   - Monitor user activity via `last_login` field
   - Deactivate users by setting `is_active = False`

### For Users
1. **Registration**:
   - Go to `/register`
   - Fill in username, email, password
   - Real-time validation provides feedback
   - Submit when all fields are valid

2. **Login**:
   - Go to `/login`
   - Enter username and password
   - Redirect to main dashboard on success

3. **Password Change**:
   - Click username dropdown in header
   - Select "Change Password"
   - Enter current and new passwords
   - Confirm changes

## API Endpoints

### Authentication Routes
```
GET  /login              - Display login page
POST /login              - Process login
GET  /register           - Display registration page
POST /register           - Process registration
GET  /change-password    - Display change password page
POST /change-password    - Process password change
GET  /logout             - Logout user
GET  /check-username     - Check username availability (AJAX)
GET  /check-email        - Check email availability (AJAX)
```

### Protected Routes
All other routes require authentication:
- `/` - Dashboard
- `/item-master/*` - Item management
- `/recipe/*` - Recipe management
- `/joining/*` - Joining management
- etc.

## Customization Options

### Styling
- All templates use Bootstrap 5.1.3
- Custom gradient themes (blue to purple)
- Font Awesome icons
- Responsive design

### Validation Rules
Modify in `controllers/login_controller.py`:
- `is_valid_password()` - Change password requirements
- `is_valid_email()` - Modify email validation
- Username length requirements

### Session Configuration
In `app.py`:
- Session timeout settings
- Cookie security options
- Remember me functionality

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure `database.py` is properly configured
2. **Table Not Found**: Run `python create_users_table.py`
3. **Login Loops**: Check session configuration and secret key
4. **AJAX Validation**: Verify jQuery is loaded

### Debugging
- Enable Flask debug mode: `app.run(debug=True)`
- Check browser console for AJAX errors
- Monitor Flask logs for authentication issues

## Future Enhancements

### Planned Features
- Password reset via email
- Two-factor authentication
- User roles and permissions
- Account lockout after failed attempts
- Password expiration policies
- User activity logging

### Database Migrations
When adding new fields to User model:
1. Create migration script
2. Update model definition
3. Run database migration
4. Test thoroughly

## Files Modified/Created

### New Files
- `models/user.py`
- `controllers/login_controller.py`
- `templates/auth/login.html`
- `templates/auth/register.html`
- `templates/auth/change_password.html`
- `create_users_table.py`
- `AUTHENTICATION_SYSTEM.md`

### Modified Files
- `app.py` - Added authentication middleware and login blueprint
- `models/__init__.py` - Added User model import
- `templates/index.html` - Added user dropdown menu

## Security Considerations

### Production Deployment
- Change default admin password
- Use strong SECRET_KEY
- Enable HTTPS
- Configure secure session cookies
- Implement rate limiting
- Regular security audits

### Best Practices
- Regular password updates
- Monitor failed login attempts
- Audit user access logs
- Backup user data securely
- Keep dependencies updated 