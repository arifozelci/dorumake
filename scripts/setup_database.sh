#!/bin/bash
# DoruMake Database Setup Script
# Run this script on the server to setup MySQL database

set -e

echo "=== DoruMake Database Setup ==="
echo ""

# Check if MySQL is installed
if ! command -v mysql &> /dev/null; then
    echo "MySQL is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y mysql-server mysql-client
    sudo systemctl start mysql
    sudo systemctl enable mysql
    echo "MySQL installed successfully"
else
    echo "MySQL is already installed"
fi

# MySQL credentials
DB_NAME="dorumake"
DB_USER="dorumake"
DB_PASS="dorumake2024"

echo ""
echo "Creating database and user..."

# Create database and user
sudo mysql -e "CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';"
sudo mysql -e "GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

echo "Database '${DB_NAME}' created successfully"
echo "User '${DB_USER}' created with full privileges"

# Test connection
echo ""
echo "Testing connection..."
mysql -u${DB_USER} -p${DB_PASS} -e "SELECT 1;" ${DB_NAME} > /dev/null 2>&1 && echo "Connection successful!" || echo "Connection failed!"

# Install Python MySQL driver
echo ""
echo "Installing Python MySQL drivers..."
cd /opt/dorumake/apps/robot
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install aiomysql pymysql

echo ""
echo "=== Database Setup Complete ==="
echo ""
echo "Database: ${DB_NAME}"
echo "User: ${DB_USER}"
echo "Password: ${DB_PASS}"
echo "Host: localhost"
echo "Port: 3306"
echo ""
echo "Next steps:"
echo "1. Run 'python -m src.db.init_db' to create tables"
echo "2. Restart the API: pm2 restart dorumake-api"
