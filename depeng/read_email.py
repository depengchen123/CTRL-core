import os
import re

from email import policy
from email.parser import BytesParser
from os import listdir
from os.path import isfile, join
#extract text from html
from bs4 import BeautifulSoup
#


path = '../../spam'


def caption(origin):
    """Extracts: To, From, Subject and Date from email.Message() or mailbox.Message()
    origin -- Message() object
    Returns tuple(From, To, Subject, Date)
    If message doesn't contain one/more of them, the empty strings will be returned.
    """
    # print(origin)
    Date = ""
    if "date" in origin: Date = origin["date"].strip()
    From = ""
    if "from" in origin: From = origin["from"].strip()
    To = ""
    if "to" in origin: To = origin["to"].strip()
    Subject = ""
    if "subject" in origin: Subject = origin["subject"].strip()
    return From, To, Subject, Date


def file_exists(f):
    """Checks whether extracted file was extracted before."""
    return os.path.exists(os.path.join(path, f))


def save_file(fn, cont):
    """Saves cont to a file fn"""
    file = open(os.path.join(path, fn), "wb")
    file.write(cont)
    file.close()


def construct_name(id, fn):
    """Constructs a file name out of messages ID and packed file name"""
    id = id.split(".")
    id = id[0] + id[1]
    return id + "." + fn


def disqo(s):
    """Removes double or single quotations."""
    s = s.strip()
    if s.startswith("'") and s.endswith("'"): return s[1:-1]
    if s.startswith('"') and s.endswith('"'): return s[1:-1]
    return s


def disgra(s):
    """Removes < and > from HTML-like tag or e-mail address or e-mail ID."""
    s = s.strip()
    if s.startswith("<") and s.endswith(">"): return s[1:-1]
    return s


def pullout(m, key):
    """Extracts content from an e-mail message.
    This works for multipart and nested multipart messages too.
    m   -- email.Message() or mailbox.Message()
    key -- Initial message ID (some string)
    Returns tuple(Text, Html, Files, Parts)
    Text  -- All text from all parts.
    Html  -- All HTMLs from all parts
    Files -- Dictionary mapping extracted file to message ID it belongs to.
    Parts -- Number of parts in original message.
    """
    Html = ""
    Text = ""
    Files = {}
    Parts = 0
    if not m.is_multipart():
        if m.get_filename():  # It's an attachment
            fn = m.get_filename()
            cfn = construct_name(key, fn)
            Files[fn] = (cfn, None)
            if file_exists(cfn): return Text, Html, Files, 1
            save_file(cfn, m.get_payload(decode=True))
            return Text, Html, Files, 1
        # Not an attachment!
        # See where this belongs. Text, Html or some other data:
        cp = m.get_content_type()
        if cp == "text/plain":
            Text += str(m.get_payload(decode=True))
        elif cp == "text/html":
            Html += str(m.get_payload(decode=True))
        else:
            # Something else!
            # Extract a message ID and a file name if there is one:
            # This is some packed file and name is contained in content-type header
            # instead of content-disposition header explicitly
            cp = m.get("content-type")
            try:
                id = disgra(m.get("content-id"))
            except:
                id = None
            # Find file name:
            o = cp.find("name=")
            if o == -1: return Text, Html, Files, 1
            ox = cp.find(";", o)
            if ox == -1: ox = None
            o += 5;
            fn = cp[o:ox]
            fn = disqo(fn)
            cfn = construct_name(key, fn)
            Files[fn] = (cfn, id)
            if file_exists(cfn): return Text, Html, Files, 1
            save_file(cfn, m.get_payload(decode=True))
        return Text, Html, Files, 1
    # This IS a multipart message.
    # So, we iterate over it and call pullout() recursively for each part.
    y = 0
    while 1:
        # If we cannot get the payload, it means we hit the end:
        try:
            pl = m.get_payload(y)
        except:
            break
        # pl is a new Message object which goes back to pullout
        t, h, f, p = pullout(pl, key)
        Text += t;
        Html += h;
        Files.update(f);
        Parts += p
        y += 1
    return Text, Html, Files, Parts


def extract_body(msgfile):
    m = BytesParser(policy=policy.default).parse(msgfile)
    if m.is_multipart():
        for part in m.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Diposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body = part.get_payload(decode=True)
                break
    else:
        body = m.get_payload(decode=True)

    return body


def extract(msgfile, key):
    """Extracts all data from e-mail, including From, To, etc., and returns it as a dictionary.
    msgfile -- A file-like readable object
    key     -- Some ID string for that particular Message. Can be a file name or anything.
    Returns dict()
    Keys: from, to, subject, date, text, html, parts[, files]
    Key files will be present only when message contained binary files.
    For more see __doc__ for pullout() and caption() functions.
    """
    m = BytesParser(policy=policy.default).parse(msgfile)
    if m.is_multipart():
        for part in m.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Diposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                body = part.get_payload(decode=True)
                # print('plaintext******')
                body_plain = re.sub('https?:\/\/.*[\r\n]*', '', body.decode())
                return body_plain.replace('\n', ' ')
    else:
        body = m.get_payload(decode=True)
        htmlfile = body.decode()
        soup = BeautifulSoup(htmlfile, features="html.parser")
        # print('body is***\n', soup.get_text(" ", strip=True))
        # get the text without blank space and http link
        # print('html file')
        body_plain = re.sub('https?:\/\/.*[\r\n]*', '', soup.get_text(" ", strip=True), flags=re.MULTILINE)
        return body_plain.replace('\n', ' ')

    From, To, Subject, Date = caption(m)
    Text, Html, Files, Parts = pullout(m, key)
    Text = Text.strip();
    Html = Html.strip()
    msg = {"subject": Subject, "from": From, "to": To, "date": Date,
           "text": Text, "html": Html, "parts": Parts}
    if Files: msg["files"] = Files
    return msg


def get_email_body_from_directory(path):
    data = {}
    file_list = listdir(path)
    # script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    # rel_path = "email/b'2'.eml"
    for f in file_list:
        if(f.find(".eml")==False):
            continue
        abs_file = join(path, f)
        with open(abs_file, 'rb') as fp:
            # print(f,"**********",self.extract(fp,fp.name))
            # print(fp.name)
            data.update({fp.name.replace(path, ""): (extract(fp, fp.name))})
            fp.close()

    return data

# abs_file_path = os.path.join(script_dir, rel_path)
# with open(abs_file_path, 'rb') as fp:  # select a specific email file from the list
#   print(extract_body(fp))

# print('you are not alone')  # print the email content
