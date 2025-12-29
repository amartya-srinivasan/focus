# focus
A project to help lock in.

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Authors](#authors)

## Features

### Core Functionality
- **Pomodoro Timer**: Customizable focus timer with visual countdown and progress ring
- **Website Blocking**: Automatically blocks distracting websites during focus sessions by modifying the system hosts file
- **Task Management**: Create, track, and complete tasks with persistent storage
- **Analytics Dashboard**: Track daily, weekly, monthly, and all-time productivity statistics
- **Multi-User Support**: Multiple users can maintain separate profiles with individual tasks and blocked sites
- **Session History**: All completed focus sessions are stored in the database for analysis

### Technical Features
- **Secure Authentication**: SHA-256 password hashing for user accounts
- **MySQL Database**: Persistent data storage for users, sessions, tasks, and blocked sites
- **Asynchronous Loading**: Background data loading for responsive UI
- **Video Background**: Animated snowfall background using OpenCV
- **Music Integration**: Background music playback with volume controls

## System Requirements

### Operating System
- Windows 7 or later (required for hosts file modification)
- Administrator privileges (required for website blocking feature)

### Software Dependencies
- Python 3.7 or higher
- MySQL Server 5.7 or higher
- Git (for cloning the repository)

### Hardware Requirements
- Minimum 2GB RAM
- 100MB free disk space
- Display resolution: 1280x720 or higher recommended

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/focus-timer.git
cd focus-timer
```

### Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not present, install the following packages manually:

```bash
pip install pygame==2.6.1
pip install mysql-connector-python
pip install opencv-python
```

### Step 3: Install and Configure MySQL

1. Download and install MySQL Server from [https://dev.mysql.com/downloads/mysql/](https://dev.mysql.com/downloads/mysql/)
2. During installation, set a root password (remember this for later)
3. Ensure MySQL service is running

### Step 4: Verify Installation

Verify Python installation:
```bash
python --version
```

Verify MySQL installation:
```bash
mysql --version
```

## Configuration

### Database Setup

The application will automatically create the database and tables on first run. You will be prompted to enter your MySQL connection details:

- **Host**: localhost (default)
- **User**: root (or your MySQL username)
- **Password**: Your MySQL root password
- **Database**: focus_app (created automatically)
- **Port**: 3306 (default)

These settings are saved in `mysql_config.json` for subsequent runs.

### Manual Database Configuration

If you prefer to configure the database manually, create `mysql_config.json` in the project root:

```json
{
    "host": "localhost",
    "user": "root",
    "password": "your_mysql_password",
    "database": "focus_app",
    "port": 3306
}
```

## Usage

### Starting the Application

#### Method 1: Using the Batch File (Recommended)

Double-click `Focus.bat` to launch the application with administrator privileges.

#### Method 2: Command Line

```bash
python admin_launcher.py
```

Note: You may be prompted for administrator privileges for website blocking functionality.

### First Time Setup

1. **Create a User Account**
   - On first launch, the User Management screen will appear
   - Enter a username (minimum 3 characters)
   - Enter a password (minimum 4 characters)
   - Click "Create User"
   - Click "Continue" to proceed to login

2. **Login**
   - Select your username from the list
   - Enter your password
   - Click "Login"

3. **Main Screen**
   - You will see the FOCUS screen with three options:
     - Click "FOCUS" text to start the timer
     - Click the user icon (bottom right) to access Settings
     - Click the analytics icon (top right) to view Analytics

### Using the Timer

1. **Starting a Focus Session**
   - Click on "FOCUS" from the main screen
   - The default timer is set to 25:00 (25 minutes)
   - To change duration: Click on the time display and type new duration (e.g., "30" for 30 minutes)
   - Press Enter to confirm the new duration
   - Click "START" to begin the timer

2. **During a Focus Session**
   - The timer counts down in MM:SS format
   - A circular progress ring shows elapsed time visually
   - Websites in your blocked list are automatically blocked
   - You can add, check, or uncheck tasks in the task panel

3. **Managing Tasks**
   - Type in the "Add new task..." field and press Enter to add a task
   - Click the checkbox next to a task to mark it complete/incomplete
   - Click "Clear completed" to remove all completed tasks
   - Tasks are automatically saved to the database

4. **Stopping the Timer**
   - Click "STOP" to pause the timer
   - The session is saved to the database with:
     - Duration (in seconds)
     - Number of completed tasks
     - Timestamp
   - Website blocking is automatically deactivated
   - Click "START" again to resume

5. **Returning to Main Screen**
   - Click "BACK" button (top left) to return to the main screen

### Settings

Access settings by clicking the user icon on the main screen.

#### Account Tab
- **Current User**: Displays logged-in username
- **Switch Account**: Click on any username to switch to that account
- **Create New User**: Click "Manage Users" to add more accounts

#### Websites Tab
- **View Blocked Sites**: See all websites currently blocked
- **Add Website**: 
  - Type domain in the input field (e.g., "youtube.com")
  - Click "Add Website"
  - The site will be blocked during focus sessions
- **Remove Website**: Click on any website in the list to remove it

#### Database Tab
- **Connection Status**: Shows if database is connected
- **Configuration**: Displays current MySQL connection settings
- **Reconfigure**: Option to update database credentials if needed

#### About Tab
- Application version and information
- List of features
- Developer credits

### Analytics Dashboard

Access analytics by clicking the analytics icon on the main screen.

#### Statistics Displayed
- **Today**: Focus time and number of sessions completed today
- **This Week**: Total focus time and sessions for the current week
- **This Month**: Monthly productivity statistics
- **All Time**: Lifetime statistics since account creation

#### Viewing Analytics
- Statistics update in real-time as you complete focus sessions
- Time is displayed in hours and minutes format (e.g., "2h 30m")
- Session count shows total number of completed focus sessions

### Website Blocking

The application blocks websites by modifying the Windows hosts file.

#### How It Works
1. When you click "START" on the timer, blocked sites are written to `C:\Windows\System32\drivers\etc\hosts`
2. Each blocked domain is redirected to `127.0.0.1` (localhost)
3. When you click "STOP" or "BACK", the hosts file is restored to its original state
4. A backup of the original hosts file is created as `hosts.bak`

#### Important Notes
- Requires administrator privileges to modify the hosts file
- You may need to restart your browser for blocks to take effect
- The application creates a backup before making changes
- Blocks are automatically removed when the timer stops

### Logging Out

The application automatically logs you out when you close the app. You will need to login again on the next launch.

## Project Structure

```
focus-timer/
│
├── main.py                    # Main application entry point and home screen
├── admin_launcher.py          # Launcher with administrator privilege handling
├── login_screen.py            # User authentication screen
├── user_management.py         # User account creation and management
├── timer.py                   # Focus timer with task management
├── settings.py                # Settings screen with tabs
├── AnalyticsDashboard.py      # Analytics and statistics display
├── database.py                # Database connection and operations
├── Focus.bat                  # Windows batch file to launch app
│
├── mysql_config.json          # MySQL connection configuration (created on first run)
├── current_user.txt           # Current session user (temporary)
├── session_active.flag        # Session state flag (temporary)
├── blocked_sites.txt          # Temporary blocked sites list (created during timer)
│
├── snowfall.mp4               # Background video animation
├── guy.png                    # Settings icon
├── analytics_icon.png         # Analytics button icon
├── start_sound.wav            # Timer start sound effect
├── complete_sound.wav         # Timer completion sound effect
│
└── requirements.txt           # Python dependencies
```

## Database Schema

### Tables

#### users
Stores user account information.

| Column        | Type         | Description                    |
|---------------|--------------|--------------------------------|
| id            | INT          | Primary key, auto-increment    |
| username      | VARCHAR(255) | Unique username                |
| password_hash | VARCHAR(255) | SHA-256 hashed password        |
| created_at    | TIMESTAMP    | Account creation timestamp     |

#### timer_sessions
Records all completed focus sessions.

| Column          | Type      | Description                      |
|-----------------|-----------|----------------------------------|
| id              | INT       | Primary key, auto-increment      |
| user_id         | INT       | Foreign key to users.id          |
| duration        | INT       | Session duration in seconds      |
| completed_tasks | INT       | Number of tasks completed        |
| session_date    | TIMESTAMP | Session completion timestamp     |

#### todos
Stores user tasks.

| Column     | Type         | Description                    |
|------------|--------------|--------------------------------|
| id         | INT          | Primary key, auto-increment    |
| user_id    | INT          | Foreign key to users.id        |
| task       | VARCHAR(500) | Task description               |
| completed  | BOOLEAN      | Completion status              |
| created_at | TIMESTAMP    | Task creation timestamp        |

#### blocked_sites
Stores blocked websites per user.

| Column     | Type         | Description                       |
|------------|--------------|-----------------------------------|
| id         | INT          | Primary key, auto-increment       |
| user_id    | INT          | Foreign key to users.id           |
| site       | VARCHAR(255) | Domain to block                   |
| created_at | TIMESTAMP    | When site was added               |

### Database Operations

The database is automatically initialized on first run with all required tables. All operations include error handling and transaction management.

## Troubleshooting

### Application Won't Start

**Issue**: Application closes immediately after launch

**Solutions**:
- Verify Python is installed: `python --version`
- Check if all dependencies are installed: `pip list`
- Run from command line to see error messages: `python admin_launcher.py`

### Database Connection Errors

**Issue**: "Failed to connect to database" error

**Solutions**:
- Verify MySQL service is running
- Check MySQL credentials in `mysql_config.json`
- Ensure MySQL port 3306 is not blocked by firewall
- Test MySQL connection: `mysql -u root -p`

### Website Blocking Not Working

**Issue**: Websites not being blocked during focus sessions

**Solutions**:
- Ensure application was launched with administrator privileges
- Restart your web browser after clicking START
- Check if `blocked_sites.txt` file is created in the project directory
- Verify hosts file permissions: `C:\Windows\System32\drivers\etc\hosts`
- Some websites may require HTTPS blocking which is not supported

### Tasks Not Saving

**Issue**: Tasks disappear after closing the application

**Solutions**:
- Check database connection status in Settings > Database
- Verify `todos` table exists in the database
- Check console output for error messages
- Ensure database user has write permissions

### Timer Display Issues

**Issue**: Timer screen appears blank or frozen

**Solutions**:
- Check if `snowfall.mp4` video file exists in project directory
- Update graphics drivers
- Try running without admin privileges (website blocking will be disabled)
- Check console for OpenCV errors

### Login Issues

**Issue**: Cannot login with correct password

**Solutions**:
- Passwords are case-sensitive, verify caps lock is off
- Check if user exists in database: `SELECT * FROM focus_app.users;`
- If you forgot your password, update it manually in database:
  ```sql
  UPDATE focus_app.users 
  SET password_hash = SHA2('newpassword', 256) 
  WHERE username = 'yourusername';
  ```

### Administrator Privileges

**Issue**: UAC prompt keeps appearing

**Solutions**:
- Right-click `Focus.bat` and select "Run as administrator"
- Add exception in Windows UAC settings
- Run Command Prompt as administrator, then launch: `python admin_launcher.py`

### Performance Issues

**Issue**: Application runs slowly or freezes

**Solutions**:
- Close other applications to free up RAM
- Check MySQL server performance
- Reduce timer display quality by closing video background
- Check database size: Large number of sessions may slow queries

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature description'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

### Development Setup

1. Clone your fork
2. Install development dependencies
3. Create a test database separate from production
4. Follow PEP 8 style guidelines for Python code
5. Test thoroughly before submitting PR

### Code Style

- Follow PEP 8 conventions
- Use meaningful variable and function names
- Add comments for complex logic
- Update documentation for new features

## License

This project is developed for educational purposes as part of an academic project.

**Academic Year**: 2024-2025

**Course**: Computer Science Project

**Institution**: [Your Institution Name]

## Authors

- **Amartya Srinivasan** - Development, Database Design
- **K Shrivathsan** - Development, UI/UX Design
- **R Vidhyuthram** - Development, Testing

## Acknowledgments

- **Pygame Community** - For comprehensive GUI framework documentation
- **MySQL** - For reliable database management system
- **Francesco Cirillo** - For the Pomodoro Technique methodology
- **Stack Overflow Community** - For problem-solving assistance
- **Open Source Community** - For inspiration and reference implementations

## Support

For issues, questions, or suggestions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review existing GitHub issues
3. Create a new issue with detailed description and error messages
4. Include system information (OS, Python version, MySQL version)

## Version History

### Version 2.0 (Current)
- Multi-user support with secure authentication
- Analytics dashboard with comprehensive statistics
- Asynchronous data loading for improved performance
- Enhanced UI with video background
- Session management system
- Database optimization

### Version 1.0
- Initial release
- Basic timer functionality
- Website blocking
- Task management
- MySQL database integration

## Future Enhancements

Potential improvements for future versions:

- Cross-platform support (macOS, Linux)
- Cloud synchronization
- Mobile companion app
- Advanced analytics with data visualization
- Break timer with automatic Pomodoro cycles
- Integration with external services (Google Calendar, Notion)
- Customizable themes
- Export functionality for reports

---

**Note**: This application modifies system files (hosts file) for website blocking functionality. Always ensure you have backups and understand the changes being made. The application creates automatic backups before modifications.

For detailed technical documentation, please refer to `PROJECT_DOCUMENTATION.md`.
