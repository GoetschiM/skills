# Content-Based Email Categorization

Keyword-based category detection used by `dispatch_approval.py` to auto-classify
unknown sender emails before creating a Notion Approval entry.

## Detection Method

`detect_category(subject, full_body)` concatenates subject + first 1000 chars of
body, lowercases, and checks for keyword presence. First match wins (priority order).

## 1. Security (highest — auto-ticket)
Keywords: `threat, detected, security, alert, warning, intrusion, admin accessed,
login attempt, brute force, malware, vulnerability, breach, compromise,
unauthorized, suspend, suspicious, unusual, critical, attack, firewall, blocked,
exploit, phishing, ransomware, access denied, authentication failure`

## 2. Rechnung (invoice/bill)
Keywords: `rechnung, invoice, bill, zahlung, payment, receipt, quittung,
abrechnung, kosten, gebühr, fee, charge, transaction, bestätigung,
auftragsbestätigung, order confirmation, kauf, subscription, abo, mitgliedschaft,
membership`

## 3. Newsletter (promotional)
Keywords: `newsletter, news, weekly, monthly digest, update, rundbrief, mailing,
promotion, angebot, sale, rabatt, discount, coupon, gutschein, werbung,
sponsored, partner, blog, artikel, article, entdecken, recommendation`

## 4. Notification (status/delivery)
Keywords: `notification, benachrichtigung, status, delivery, lieferung, shipped,
versand, tracking, sendungs, update verfügbar, new version, maintenance, wartung,
outage, störung, downtime, scheduled, planned, information, info, hinweis`

## 5. Other (fallback)

## Known Issues

- LinkedIn connection notifications (e.g. "Martin Geidl – Vertreter von...")
  can miscategorize when subject is short. Full-body fetch helps but manual
  review in Notion may be needed.
- Short snippets (<100 chars) miscategorize more often. Always fetch full body.
- Security keywords are intentionally broad — a newsletter about "security update"
  may trigger auto-ticket, which is acceptable (quickly closable Jira issue).
