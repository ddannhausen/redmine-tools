#!/usr/bin/env python3
from redminelib import Redmine
import csv
import pandas as pd
import numpy as np
import smtplib
import time
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import config as cfg

redmine = Redmine(cfg.redmine['url'], username = cfg.redmine['user'], password = cfg.redmine['password'])
trackers = redmine.tracker.all()
projects = redmine.project.all()

def send_email(data, mail):
    sender = cfg.gmail['email'] 
    recipients = [mail]
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Redmine Email Reminder " + time.strftime("%c")
    msg['From'] = sender
    msg['To'] = ", ".join(recipients)
    
    msg.attach(MIMEText(data, 'html'))

    username = cfg.gmail['email']
    password = cfg.gmail['password']
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login(username,password)
    server.sendmail(sender, recipients, msg.as_string())
    server.quit()        
    print(mail)


#Priority Formating
priority_colors = [ 'background: #d2f0ff;',                  #Low
                    'background: ;',                         #Normal
                    'background: #ffe0ab;font-weight:bold;', #High
                    'background: #fcc5b0;font-weight:bold;', #Urgent
                    'background: #f5acac;font-weight:bold;', #Immediate
                  ]

def filter_issues(key, user, proj_id = 1, track_id = 1):
    
    # Need next Monday's date
    d = datetime.date.today()
    while d.weekday() != 0:
        d += datetime.timedelta(1)
    
    if key == 'High priority':
        issues = redmine.issue.filter( assigned_to_id = user, status_id = 'open', priority_id = '3|4|5')
    elif key == 'Due this week':
        issues = redmine.issue.filter( assigned_to_id = user, status_id = 'open', due_date='><2010-01-01|{}'.format(d))
    elif key == 'Closed last week':
        issues = redmine.issue.filter( assigned_to_id = user, status_id = 'closed', updated_on='><{}|{}'.format(d-7*datetime.timedelta(1), d))
    elif key == 'Watched by me':
        issues = redmine.issue.filter( watcher_id = user, status_id = 'open' )
    elif key == 'Assigned to me':
        issues = redmine.issue.filter( assigned_to_id = user, status_id = 'open' )

    issue_df = pd.DataFrame(columns=['project', 'project_id', 'tracker', 'tracker_id', 'priority', 'priority_id', \
                                     'issue', 'issue_id', 'link', 'due_date', 'status', 'status_id'])
        
    for issue in issues:
        link = '<a href="http://mdm.bitnamiapp.com/redmine/issues/{}">{}</a>'.format(str(issue.id), issue)
        try:
            due_date = issue.due_date
        except:
            due_date = 'None'
        issue_df.loc[len(issue_df)] = [ issue.project, issue.project.id, issue.tracker, issue.tracker.id, \
                                        issue.priority, issue.priority.id, issue, issue.id, \
                                        link, due_date, issue.status, issue.status.id]

    issue_df.set_index(['issue_id'], inplace=True)
    
    if key == 'All Assigned to me':
        issue_df = issue_df.sort_values(by=['project_id', 'tracker_id', 'priority_id','due_date'], ascending=[True, True, False,True])
    else:
        issue_df = issue_df.sort_values(by=['priority_id','due_date'], ascending=[False,True])
    return issue_df

def produce_html(FilterIssues, tbl, user):
    
    df = FilterIssues(tbl, user)

    project_ids = list(map(int, sorted(df.project_id.drop_duplicates().tolist())))

    output = ''
    
    if df.empty:
            output += '<table><tr><td width="600", style="overflow: hidden;">No issues.</td></tr></table>'
    
    elif tbl != 'Assigned to me':
        for row in df.itertuples():
            output += '<table><tr>'
            output += '<td width="400", style="overflow: hidden;{}">{}</td>'.format(str(priority_colors[int(row.priority_id-1)]), str(row.link))
            output += '<td width="100", style="overflow: hidden;{}">{}</td>'.format(str(priority_colors[int(row.priority_id-1)]), str(row.priority))
            output += '<td width="100", style="overflow: hidden;{}">{}</td>'.format(str(priority_colors[int(row.priority_id-1)]), str(row.due_date))
            output += '</tr></table>'
    elif tbl == 'Assigned to me':
        for project in projects:
            if project.id in project_ids:
                output += '<h1 style="position: relative; left: 20px;">' + str(project) + '</h1>'
                for tracker in project.trackers:
                    displayed_tracker = False
                    for row in df.itertuples():
                        if str(row.project) == str(project) and str(row.tracker) == str(tracker):
                            if not displayed_tracker:
                                output += '<h2 style="position: relative; left: 40px;">' + str(tracker) + '</h2>'
                                displayed_tracker = True
                            output += '<table>'
                            output += '<tr>'
                            output += '<td width="400", style="overflow: hidden;{}">{}</td>'.format(str(priority_colors[int(row.priority_id-1)]), str(row.link))
                            output += '<td width="100", style="overflow: hidden;{}">{}</td>'.format(str(priority_colors[int(row.priority_id-1)]), str(row.priority))
                            output += '<td width="100", style="overflow: hidden;{}">{}</td>'.format(str(priority_colors[int(row.priority_id-1)]), str(row.due_date))
                            output += '</tr>'
                            output += '</table>'
    else:
        None
    
    return output



def main():
    
    tables= [
        'High priority',
        'Due this week',
        'Closed last week',
        'Watched by me',
        'Assigned to me'
    ]
    
    user_filter = [1,5] #for u in redmine.user.all(): if (u.id in user_filter): print(u.id, u)
    
    for user in redmine.user.all():
        df_get_all_assigned = filter_issues('Assigned to me', user.id)
        df_get_all_watched = filter_issues('Watched by me', user.id)
        if not df_get_all_assigned.empty and not df_get_all_watched.empty:
            if user.id in user_filter:
                output = '<!DOCTYPE html>'
                output += '<html>'
                output += '<head><style> table, th, td {font-size:16px; border: ; position: relative; left: 40px;}</style></head>'
                output += '<p style="font-size:24px;"> Weekly issue reminder report for {}</p>'.format(user)
                for table in tables: 
                    output += '<p style="font-size:28px;"><u>{}</u></p>'.format(table)
                    output += produce_html(filter_issues, table, user.id)
                output += '</html>'
                send_email(output,user.mail)


main()


