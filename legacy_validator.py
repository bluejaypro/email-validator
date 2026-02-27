import re
import smtplib
import dns.resolver

# Address used for SMTP MAIL FROM command
fromAddress = 'Info@firstmaid.com'

# Updated Regex for syntax checking (allows uppercase letters in the domain)
regex = r'^[_a-zA-Z0-9-]+(\.[_a-z0-9-]+)*@([a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,})$'

# Function to verify an email address
def verify_email(email):
    # Syntax check
    match = re.match(regex, email)
    if match is None:
        return False

    # Get domain for DNS lookup
    splitAddress = email.split('@')
    domain = splitAddress[1]

    # MX record lookup
    try:
        records = dns.resolver.query(domain, 'MX')
        mxRecord = str(records[0].exchange)

        # SMTP lib setup (use debug level for full output)
        server = smtplib.SMTP()
        server.set_debuglevel(0)

        # SMTP Conversation
        server.connect(mxRecord)
        server.helo(server.local_hostname)
        server.mail(fromAddress)
        code, message = server.rcpt(email)
        server.quit()

        # Assume SMTP response 250 is success
        if code == 250:
            return True

    except Exception:
        pass

    return False

# Read email addresses from the input file and save valid emails to the output file
input_file = "input_emails.txt"
output_file = "valid_emails.txt"

with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        email = line.strip()
        if verify_email(email):
            print(f"Valid Email: {email}")
            outfile.write(email + "\n")

print("Validation complete. Valid email addresses saved to", output_file)

