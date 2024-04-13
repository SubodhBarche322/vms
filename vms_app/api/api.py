from __future__ import unicode_literals
import frappe
from datetime import date
from frappe.utils.file_manager import save_url
import requests
import json
from frappe.utils.background_jobs import enqueue
from frappe import _
import sched
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart 
from email.message import EmailMessage
import fitz
import os
from frappe.utils.file_manager import get_files_path

#****************************************************Login API******************************************************************************

@frappe.whitelist( allow_guest=True )
def login(usr, pwd):

    try:

        login_manager = frappe.auth.LoginManager()
        login_manager.authenticate(user=usr, pwd=pwd)
        login_manager.post_login()
    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key":0,
            "message":"Authentication Error!"
        }

        return

    api_generate = generate_keys(frappe.session.user)
    user = frappe.get_doc('User', frappe.session.user)
    frappe.response["message"] = {

        "success_key":1,
        "message":"Authentication success",
        "sid":frappe.session.sid,
        "api_key":user.api_key,
        "api_secret":api_generate,
        "username":user.username,
        "email":user.email

    }

def generate_keys(user):

    user_details = frappe.get_doc('User', user)
    api_secret = frappe.generate_hash(length=15)
    if not user_details.api_key:
        api_key = frappe.generate_hash(length=15)
        user_details.api_key = api_key
    user_details.api_secret = api_secret
    user_details.save()

    return api_secret

#****************************************************Login API Closed************************************************************************************

@frappe.whitelist(allow_guest=True)
def send_email(data, method):
    frappe.db.sql(""" update `tabVendor Master` set status='In Process' """ )
    frappe.db.commit()
    print("*********************Hi from Docevents*****************")
    print(frappe.session.user)
    current_user = frappe.session.user
    current_user_email = frappe.db.get_value("User", filters={'full_name': current_user}, fieldname='email')
    print(current_user_email)
    frappe.db.sql(" update `tabVendor Master` set registered_by=%s ",(current_user_email))
    frappe.db.commit()
    reciever_email = data.get("office_email_primary")
    print(reciever_email)
    smtp_server = "smtp.transmail.co.in"
    smtp_port = 587
    smtp_user = "emailapikey"  
    smtp_password = "PHtE6r1cF7jiim598RZVsPW9QMCkMN96/uNveQUTt4tGWPNRTk1U+tgokDO0rRx+UKZAHKPInos5tbqZtbiHdz6/Z2dED2qyqK3sx/VYSPOZsbq6x00as1wSc0TfUILscdds1CLfutnYNA=="  
    from_address = current_user_email 
    to_address = reciever_email  
    subject = "Test email"
    body = "You have been Successfully Registered on the VMS Portal. PLease complete the On boarding process ."
    msg = MIMEMultipart()
    msg["From"] = from_address
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  
            server.login(smtp_user, smtp_password)  
            server.sendmail(from_address, to_address, msg.as_string()) 
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

@frappe.whitelist(allow_guest=True)
def send_email_on_onboarding(data, method):

    print("***********Details filled***********")
    current_user_email = data.get('office_email_primary')
    print(current_user_email)
    company_name = data.get('company_name')
    print(company_name)
    reciever_email = frappe.db.get_value("Vendor Master", filters={'company_name': company_name}, fieldname=['registered_by'])
    print(reciever_email)
    smtp_server = "smtp.transmail.co.in"
    smtp_port = 587
    smtp_user = "emailapikey"  
    smtp_password = "PHtE6r1cF7jiim598RZVsPW9QMCkMN96/uNveQUTt4tGWPNRTk1U+tgokDO0rRx+UKZAHKPInos5tbqZtbiHdz6/Z2dED2qyqK3sx/VYSPOZsbq6x00as1wSc0TfUILscdds1CLfutnYNA=="  
    from_address = current_user_email 
    to_address = reciever_email  
    subject = "Test email"
    body = "This is a Test email ...!"
    msg = MIMEMultipart()
    msg["From"] = from_address
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  
            server.login(smtp_user, smtp_password)  
            server.sendmail(from_address, to_address, msg.as_string()) 
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")



@frappe.whitelist(allow_guest=True)
def hit():
    print("****************Hi there!*******************")
    purchase_head_key = frappe.db.get_value("Designation Master", {"designation_name": "Purchase Head"}, "name")
    accounts_team_key = frappe.db.get_value("Designation Master", {"designation_name": "Accounts Team"}, "name")
    purchase_head_users = frappe.db.get_list("User", filters={"designation": purchase_head_key}, fields=["email"])
    accounts_team_users = frappe.db.get_list("User", filters={"designation": accounts_team_key}, fields=["email"])
    all_emails = [user["email"] for user in accounts_team_users] + [user["email"] for user in purchase_head_users]
    print(all_emails)
    smtp_server = "smtp.transmail.co.in"
    smtp_port = 587
    smtp_user = "emailapikey"  
    smtp_password = "PHtE6r1cF7jiim598RZVsPW9QMCkMN96/uNveQUTt4tGWPNRTk1U+tgokDO0rRx+UKZAHKPInos5tbqZtbiHdz6/Z2dED2qyqK3sx/VYSPOZsbq6x00as1wSc0TfUILscdds1CLfutnYNA=="  
    from_address = "noreply@merillife.com" 
    subject = "Test email"
    body = "This is a Test email ...!"
    for to_address in all_emails:
        msg = MIMEMultipart()
        msg["From"] = from_address
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  
                server.login(smtp_user, smtp_password)  
                server.sendmail(from_address, to_address, msg.as_string()) 
                print(f"Email sent successfully to {to_address}!")
        except Exception as e:
            print(f"Failed to send email to {to_address}: {e}")





@frappe.whitelist(allow_guest=True)
def hitt(data, method):
    print("****************Hi there!*******************")
    vendor_type_id = data.get('select_service')
    vendors = frappe.db.sql(""" select office_email_primary from `tabVendor Onboarding` where vendor_type=%s """,(vendor_type_id))
    email_addresses = [vendor[0] for vendor in vendors]
    print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&",email_addresses)
    smtp_server = "smtp.transmail.co.in"
    smtp_port = 587
    smtp_user = "emailapikey"  
    smtp_password = "PHtE6r1cF7jiim598RZVsPW9QMCkMN96/uNveQUTt4tGWPNRTk1U+tgokDO0rRx+UKZAHKPInos5tbqZtbiHdz6/Z2dED2qyqK3sx/VYSPOZsbq6x00as1wSc0TfUILscdds1CLfutnYNA=="  
    from_address = "noreply@merillife.com" 
    subject = "Test email"
    body = "This is a Test email to Vendor regarding RFQ ...!"
    for to_address in email_addresses:
        msg = MIMEMultipart()
        msg["From"] = from_address
        msg["To"] = to_address
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  
                server.login(smtp_user, smtp_password)  
                server.sendmail(from_address, to_address, msg.as_string()) 
                print(f"Email sent successfully to {to_address}!")
        except Exception as e:
            print(f"Failed to send email to {to_address}: {e}")
   




@frappe.whitelist(allow_guest=True)
def calculate(data, method):
    print("***********Calculated**********************")
    chargable_weight = data.get("chargable_weight")
    ratekg = data.get("ratekg")
    fuel_sur_charge = data.get("fuel_sur_charge")
    sur_charge = data.get("sur_charge")
    xray = data.get("xray")
    pickuporigin = data.get("pickuporigin")
    xrxecom = data.get("xrxecom")
    destination_charges_inr = data.get("destination_charges_inr")
    freight_mode = data.get("freight_mode")
    shipping_line_charges = data.get("shipping_line_charges")
    total_freight = chargable_weight * (ratekg + fuel_sur_charge + sur_charge) + xray + pickuporigin
    ex_works = xray + pickuporigin
    total_freight_inr = total_freight * xrxecom
    frappe.db.sql(""" update `tabImport Entry` set total_freight=%s, ex_works=%s, xrxecom=%s """,(total_freight, ex_works, xrxecom))
    frappe.db.commit()
    if freight_mode == "Air":
        total_landing_priceinr = total_freight_inr + destination_charges_inr
        frappe.db.sql(""" update `tabImport Entry` set total_landing_priceinr=%s """,(total_landing_priceinr))
        frappe.db.commit()
    elif freight_mode == "Ocean":
        total_landing_priceinr = total_freight_inr + destination_charges_inr + shipping_line_charges
        frappe.db.sql(""" update `tabImport Entry` set total_landing_priceinr=%s """,(total_landing_priceinr))
        frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def calculate_export_entry(data, method):

    parent = data.get("parent")
    shipment_mode = data.get("shipment_mode")
    ratekg = data.get("ratekg")
    fuel_surcharge = data.get("fuel_surcharge")
    sc = data.get("sc")
    xray = data.get("xray")
    name = data.get("name")
    other_charges_in_total = data.get("other_charges_in_total")
    chargeable_weight = data.get("chargeable_weight")
    total_freight = (ratekg + fuel_surcharge + sc + xray) * chargeable_weight + other_charges_in_total
    frappe.db.sql(""" update `tabExport Entry Vendor` set total_freight=%s where name=%s""",(total_freight, name))
    frappe.db.commit()



# @frappe.whitelist(allow_guest=True)
# def test_method(self, method):
#     if self.file_name:
#         file_doc = frappe.get_doc("File", {"file_url": self.file_name})
#         frappe.msgprint(f"File URL: {file_doc.file_url}")
            


@frappe.whitelist(allow_guest=True)
def test_method(self, method):
    if self.file_name:
       
        file_path = frappe.get_site_path(self.file_name.lstrip("/"))

    
        if os.path.exists(file_path):
            frappe.msgprint("File exists.")
        else:
            frappe.msgprint("File does not exist.")

        
        file_doc = frappe.get_doc("File", {"file_url": self.file_name})
        frappe.msgprint(f"File URL: {file_doc.file_url}")


# @frappe.whitelist(allow_guest=True)
# def main_function(data, method):
#     #time.sleep(3)
#     print("*****************************Hi From Main**************************************")
#     name = data.get("name")
#     file = frappe.db.sql(""" select file_name from `tabImport Entry` where name=%s """,(name))
#     print(file)
#     with fitz.open(file) as doc:
#         text = ""
#         for page in doc:
#             text += page.get_text()
#         print(text)

@frappe.whitelist(allow_guest=True)
def extract_text_from_pdf(data, method):
    pdf_path = data.get("file_name")
    #pdf_path = frappe.request.files.get("file_name")
    
    with fitz.open(pdf_path) as doc:
        text = ""
        for page in doc:
            text += page.get_text()
   

    lines = text.split('\n')
    resume_dict = {}

    current_section = None
    for line in lines:
        if line.strip() == "":
            continue
        if ":" in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
           
            if current_section is not None:
               
                if current_section not in resume_dict or isinstance(resume_dict[current_section], list):
                    resume_dict[current_section] = {}
                resume_dict[current_section][key] = value
            else:
                resume_dict[key] = value
        else:
           
            if current_section is None or isinstance(resume_dict.get(current_section, None), dict):
                current_section = line.strip()
              
                if current_section in resume_dict and isinstance(resume_dict[current_section], list):
                    continue
                else:
                    resume_dict[current_section] = []  
            else:
                resume_dict[current_section].append(line.strip())
   
    text = extract_text_from_pdf(pdf_path)
    resume_dict = parse_resume_text(text)
    for key, value in resume_dict.items():
        if isinstance(value, dict):
            print(f"{key}:")
        for sub_key, sub_value in value.items():
            print(f"  {sub_key}: {sub_value}")
        if isinstance(value, list):
            print(f"{key}:")
        for item in value:
            print(f"  - {item}")
    else:
        print(f"{key}: {value}")
    print()  
    print(type(resume_dict))










