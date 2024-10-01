#!/bin/bash

# Get user inputs for username and password
read -p "Enter the new username: " new_username
read -p "Enter the new password: " new_password

sed -i "166s/'username'/'$new_username'/" app.py
sed -i "168s/'username'/'$new_username'/" app.py
sed -i "167s/'password'/'$new_password'/" app.py

sed -i "6s/'username'/'$new_username'/" create_user.py
sed -i "8s/'username'/'$new_username'/" create_user.py
sed -i "7s/'password'/'$new_password'/" create_user.py

echo "Username and password have been updated successfully."
