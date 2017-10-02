#!/bin/bash
. /home/bitnami/apps/redmine/redmine-tools/config.sh
. /opt/bitnami/scripts/setenv.sh
cd /opt/bitnami/apps/redmine/htdocs 
bin/rake -f /opt/bitnami/apps/redmine/htdocs/Rakefile redmine:email:receive_imap unknown_user=accept no_permission_check=1 RAILS_ENV="production" host=imap.gmail.com port=993 username=$username password=$password ssl=1 project=household allow_override=project,tracker,status,priority,assigned_to,start_date,due_date,estimated_hours,done_ratio


