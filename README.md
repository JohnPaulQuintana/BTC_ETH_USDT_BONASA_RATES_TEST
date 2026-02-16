# BTC, ETH, USDT & BONASA Rates Automation

## Overview

This system automates the retrieval, processing, and updating of **BTC**, **ETH**, **USDT**, and **BONASA** conversion rates into a designated **Google Sheet**.

It is designed to run continuously or on a schedule, ensuring rate data is kept accurate, consistent, and up to date without manual intervention.

---

## Problem the System Solves

* Manual rate checking and Google Sheet updates are repetitive and error-prone
* Missed or delayed updates lead to inaccurate reporting and operational issues
* Failures are difficult to detect without constant monitoring

This automation solves these issues by:

* Running rate updates automatically based on predefined schedules
* Retrying failed updates until data is successfully written
* Providing real-time visibility through alerting

---

## Core System Functionality

### Rate Processing

* Collects conversion rates for:

  * **BTC**
  * **ETH**
  * **USDT**
  * **BONASA**
* Processes and validates retrieved data
* Updates the connected **Google Sheet** with the latest computed rates

### Execution Behavior

#### BONASA Rates

* Executed **once per day** within a defined time window
* If the rate is not successfully updated:

  * The system automatically retries at fixed intervals
  * Monitoring alerts are triggered on each failed attempt
* Retry cycle stops automatically once the update succeeds

#### BTC, ETH, USDT Rates

* Executed on a recurring **hourly** basis
* Runs independently from BONASA processing
* Ensures crypto rates remain current throughout the day

---

## Monitoring & Alerts

* Integrated alerting provides real-time status updates
* Notifications are sent for:

  * Successful rate updates
  * Failed update attempts
  * Repeated retry conditions
* This allows issues to be identified immediately without checking logs or sheets manually

---

## Branch Behavior Overview

* **`main`**

  * Full production automation
  * Includes all supported payment methods

* **`bank_filters`**

  * Same automation logic as `main`
  * Excludes bank transfer payment methods from rate computation

* **`docker`**

  * Containerized version of the system
  * Intended for server-based or CI/CD deployments

---

## Additional Information

* https://docs.google.com/document/d/1UKu9Yp9o77hdkm2Z4Hdoia81W-aPS0F_QZAnicmU2Ag/edit?tab=t.0#heading=h.sxmz56c5xh5b>

* https://app.eraser.io/workspace/QnPsfbTN2B1KlFWjtPi1?origin=share

---

## Summary

This automation system ensures reliable, scheduled, and monitored updates of BONASA and cryptocurrency rates into Google Sheets. By removing manual processes and adding automated retries and alerts, it reduces operational risk and improves data reliability.
