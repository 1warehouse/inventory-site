#!/usr/bin/env python3
"""Provision the GA4 property for the website stream — the console work, as code.

Everything js/analytics.js sends is useless in the UI until the parameters are
registered as custom dimensions: GA4 collects unregistered params but will not
report on them, and it does not backfill, so a dimension registered late is
blind to everything before it. Hence doing this once, early, and in writing.

Idempotent. It lists what exists and only creates what is missing, so running
it twice is harmless.

    python3 tools/ga4_setup.py            # dry run — prints the plan, changes nothing
    python3 tools/ga4_setup.py --apply    # makes the changes

Needs a token carrying the analytics.edit scope. Getting one as a human does not
work: `gcloud auth login` has no --scopes flag, and routing round that via
`gcloud auth application-default login --scopes=...analytics.edit` is refused by
Google with "This app is blocked", because gcloud's OAuth client may only ask
for its own allowlisted scopes. So use a service account:

    gcloud auth login alexander.minko@1inventory.io        # plain: no --scopes, not blocked

    gcloud iam service-accounts create ga4-admin \\
      --project=oneinventory-462908 --display-name="GA4 admin automation"

    gcloud services enable iamcredentials.googleapis.com --project=oneinventory-462908

    gcloud iam service-accounts add-iam-policy-binding \\
      ga4-admin@oneinventory-462908.iam.gserviceaccount.com \\
      --member="user:alexander.minko@1inventory.io" \\
      --role="roles/iam.serviceAccountTokenCreator" \\
      --project=oneinventory-462908

Then grant that service account access to the GA4 property — the one step with
no API, since granting access needs access. In Google Analytics: Admin →
Property access management → + → add the service account's email with the
Editor role.

    GA4_IMPERSONATE=ga4-admin@oneinventory-462908.iam.gserviceaccount.com \\
      python3 tools/ga4_setup.py

A downloaded key works too (`GA4_SA_KEY=/path/key.json`), but impersonation is
preferred: it leaves no long-lived credential on disk.

Schemas, enums and scopes below were taken from the v1beta discovery document
rather than from memory. One thing genuinely is not in the API: internal traffic
filters have no resource in v1beta, so that step still needs the GA4 UI.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

ACCOUNT = "alexander.minko@1inventory.io"
PROPERTY = "493431840"
MEASUREMENT_ID = "G-96ZNX5D52Q"
BASE = "https://analyticsadmin.googleapis.com/v1beta"
# Enhanced Measurement is only exposed on v1alpha. Same scope, same auth.
ALPHA = "https://analyticsadmin.googleapis.com/v1alpha"

# Event-scoped. parameterName must match exactly what analytics.js sends.
DIMENSIONS = [
    ("store_name",      "Store name",          "app_store or google_play, on store_click."),
    ("placement",       "CTA placement",       "Which data-cta was clicked: hero-ios, sticky, home-android, ..."),
    ("device_platform", "Device platform",     "ios / android / desktop, detected client-side."),
    ("page_language",   "Page language",       "Language build in use: en, de, es, fr, pt."),
    ("page_type",       "Page type",           "Page normalised across languages: home, plans, faq, support, legal, 404."),
    ("target",          "Anchor target",       "In-page anchor id clicked — on the FAQ, which topic was sought."),
    ("percent",         "Scroll depth percent", "Scroll mark reached: 25, 50, 75, 100."),
]

KEY_EVENT = "store_click"
RETENTION = "FOURTEEN_MONTHS"  # the 2-month default quietly destroys year-over-year


SCOPE = "https://www.googleapis.com/auth/analytics.edit"


def impersonated_token(sa):
    """Mint an analytics.edit token for `sa`, using your own gcloud login.

    This is the route gcloud itself recommends when it refuses a scope. Your
    user credential (cloud-platform scope, which the default login does give)
    authorises the call; IAM Credentials hands back a short-lived token for the
    service account carrying the scope we actually need. Nothing long-lived is
    written to disk, which is why this is preferred over a downloaded key."""
    try:
        base = subprocess.run(["gcloud", "auth", "print-access-token"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except subprocess.CalledProcessError as e:
        sys.exit("Could not get your own gcloud token.\n%s" % (e.stderr or "").strip())

    url = ("https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
           "%s:generateAccessToken" % sa)
    req = urllib.request.Request(
        url, data=json.dumps({"scope": [SCOPE], "lifetime": "3600s"}).encode(),
        method="POST")
    req.add_header("Authorization", "Bearer " + base)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())["accessToken"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        if e.code == 403:
            detail += ("\n\nLikely missing roles/iam.serviceAccountTokenCreator on the "
                       "service account, or iamcredentials.googleapis.com is not "
                       "enabled. See this file's docstring.")
        sys.exit("Impersonating %s failed -> HTTP %s\n%s" % (sa, e.code, detail))


def token():
    """Impersonation first, then a service-account key, then plain ADC.

    The obvious route — `gcloud auth application-default login --scopes=...
    analytics.edit` — does not work. gcloud's own OAuth client is only
    allowlisted for a fixed set of scopes, and asking it for analytics.edit is
    refused with "This app is blocked"."""
    sa = os.environ.get("GA4_IMPERSONATE")
    if sa:
        return impersonated_token(sa)

    key = os.environ.get("GA4_SA_KEY")
    if key:
        key = os.path.expanduser(key)
        if not os.path.exists(key):
            sys.exit("GA4_SA_KEY points at %s, which does not exist." % key)
        try:
            from google.oauth2 import service_account
            from google.auth.transport.requests import Request
        except ImportError:
            sys.exit("GA4_SA_KEY is set but google-auth is not installed.\n"
                     "  python3 -m pip install --user google-auth requests")
        creds = service_account.Credentials.from_service_account_file(key, scopes=[SCOPE])
        creds.refresh(Request())
        return creds.token

    try:
        out = subprocess.run(
            ["gcloud", "auth", "application-default", "print-access-token"],
            capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except subprocess.CalledProcessError as e:
        sys.exit("Set GA4_IMPERSONATE (preferred) or GA4_SA_KEY — plain ADC has no "
                 "analytics.edit scope and cannot get one.\n%s\n"
                 "See this file's docstring for the setup."
                 % (e.stderr or "").strip())


def check_token(tok):
    """Confirm whose token this is and that it carries analytics.edit.

    Cheaper to fail here than to half-apply changes to the wrong property, or
    to get an opaque 403 twenty lines later."""
    url = "https://oauth2.googleapis.com/tokeninfo?access_token=" + tok
    try:
        with urllib.request.urlopen(url) as r:
            info = json.loads(r.read())
    except urllib.error.HTTPError:
        print("WARNING: could not introspect the token; continuing anyway.")
        return
    email = info.get("email", "(unknown)")
    scopes = info.get("scope", "").split()
    # Impersonated tokens carry no email in tokeninfo, so trust the env var we
    # were given rather than reporting the identity as unknown and crying wolf.
    is_sa = email.endswith(".iam.gserviceaccount.com") or bool(os.environ.get("GA4_IMPERSONATE"))
    if email == "(unknown)" and os.environ.get("GA4_IMPERSONATE"):
        email = os.environ["GA4_IMPERSONATE"]
    print("Token    : %s%s" % (email, " (service account)" if is_sa else ""))
    if not is_sa and email.lower() != ACCOUNT.lower():
        print("WARNING: expected %s. You may have picked the wrong account on the "
              "consent screen." % ACCOUNT)
    if SCOPE not in scopes:
        sys.exit("Token lacks the analytics.edit scope — the Admin API will reject "
                 "every write.\nSee this file's docstring for the service-account "
                 "setup.")


def api(tok, method, path, body=None, params="", ok_if_exists=False, base=None):
    """ok_if_exists swallows 409. Listing then creating is not atomic — two
    runs at once, or a half-finished earlier run, will race — and for a
    create that is idempotent by intent, "someone already made it" is the
    outcome we wanted, not an error worth dying on."""
    url = "%s/%s%s" % (base or BASE, path, params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + tok)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        if e.code == 409 and ok_if_exists:
            return {"_already_existed": True}
        detail = e.read().decode(errors="replace")
        if e.code == 403 and "SERVICE_DISABLED" in detail:
            detail += ("\n\nEnable the API once, then re-run:\n"
                       "  gcloud services enable analyticsadmin.googleapis.com "
                       "--project=oneinventory-462908")
        sys.exit("%s %s -> HTTP %s\n%s" % (method, url, e.code, detail))


def main():
    apply = "--apply" in sys.argv
    tok = token()
    check_token(tok)

    # Preflight. Proves the token works and that we are pointed at the right
    # property before anything is written.
    prop = api(tok, "GET", "properties/" + PROPERTY)
    print("Property : %s (%s)" % (prop.get("displayName"), prop.get("name")))

    streams = api(tok, "GET", "properties/%s/dataStreams" % PROPERTY).get("dataStreams", [])
    web = [s for s in streams if s.get("type") == "WEB_DATA_STREAM"]
    print("Streams  : %d total, %d web" % (len(streams), len(web)))
    for s in web:
        mid = s.get("webStreamData", {}).get("measurementId")
        flag = "  <-- the site" if mid == MEASUREMENT_ID else ""
        print("           %s  %s%s" % (mid, s.get("displayName"), flag))
    if not any(s.get("webStreamData", {}).get("measurementId") == MEASUREMENT_ID for s in web):
        print("WARNING: %s not found on this property. Check the ID before applying."
              % MEASUREMENT_ID)

    print("\nMode     : %s\n" % ("APPLY" if apply else "dry run (pass --apply to execute)"))

    # 1. Custom dimensions.
    existing = {d["parameterName"] for d in
                api(tok, "GET", "properties/%s/customDimensions" % PROPERTY)
                .get("customDimensions", [])}
    for param, label, desc in DIMENSIONS:
        if param in existing:
            print("  dimension  %-16s already registered" % param)
            continue
        if not apply:
            print("  dimension  %-16s WOULD CREATE" % param)
            continue
        r = api(tok, "POST", "properties/%s/customDimensions" % PROPERTY,
                {"parameterName": param, "displayName": label,
                 "description": desc, "scope": "EVENT"}, ok_if_exists=True)
        print("  dimension  %-16s %s" % (
            param, "already existed" if r.get("_already_existed") else "created"))

    # 2. Key event — the conversion.
    keys = {k["eventName"] for k in
            api(tok, "GET", "properties/%s/keyEvents" % PROPERTY).get("keyEvents", [])}
    if KEY_EVENT in keys:
        print("  key event  %-16s already marked" % KEY_EVENT)
    elif not apply:
        print("  key event  %-16s WOULD CREATE" % KEY_EVENT)
    else:
        r = api(tok, "POST", "properties/%s/keyEvents" % PROPERTY,
                {"eventName": KEY_EVENT, "countingMethod": "ONCE_PER_EVENT"},
                ok_if_exists=True)
        print("  key event  %-16s %s" % (
            KEY_EVENT, "already existed" if r.get("_already_existed") else "created"))

    # 3. Retention.
    cur = api(tok, "GET", "properties/%s/dataRetentionSettings" % PROPERTY)
    now = cur.get("eventDataRetention")
    if now == RETENTION:
        print("  retention  %-16s already %s" % ("", RETENTION))
    elif not apply:
        print("  retention  %-16s WOULD CHANGE %s -> %s" % ("", now, RETENTION))
    else:
        api(tok, "PATCH", "properties/%s/dataRetentionSettings" % PROPERTY,
            {"eventDataRetention": RETENTION}, "?updateMask=eventDataRetention")
        print("  retention  %-16s %s -> %s" % ("", now, RETENTION))

    # 4. Enhanced Measurement. GA4's built-in outbound-click and scroll
    #    tracking duplicate what analytics.js already sends, with less
    #    detail: its click event carries no placement, and its scroll fires
    #    only at 90%. Leaving both on means every store click is counted
    #    twice by two events that disagree.
    for s_ in web:
        if s_.get("webStreamData", {}).get("measurementId") != MEASUREMENT_ID:
            continue
        ems = api(tok, "GET", s_["name"] + "/enhancedMeasurementSettings", base=ALPHA)
        off = [f for f in ("outboundClicksEnabled", "scrollsEnabled") if ems.get(f)]
        label = {"outboundClicksEnabled": "outbound clicks", "scrollsEnabled": "scroll"}
        if not off:
            print("  enhanced   %-16s outbound clicks + scroll already off" % "")
        elif not apply:
            print("  enhanced   %-16s WOULD DISABLE %s"
                  % ("", ", ".join(label[f] for f in off)))
        else:
            api(tok, "PATCH", s_["name"] + "/enhancedMeasurementSettings",
                {f: False for f in off},
                "?updateMask=" + ",".join(off), base=ALPHA)
            print("  enhanced   %-16s disabled %s"
                  % ("", ", ".join(label[f] for f in off)))

    print("\nStill needs the GA4 UI (no API resource exists in v1beta or v1alpha):")
    print("  · Internal traffic filter for your own IP")


if __name__ == "__main__":
    main()
