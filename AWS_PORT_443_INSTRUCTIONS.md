# How to Open Port 443 in AWS Security Group

## Quick Steps:

1. **Log into AWS Console**
   - Go to https://console.aws.amazon.com/
   - Navigate to EC2 Dashboard

2. **Find Your Instance**
   - Click on "Instances"
   - Find the instance with IP: 54.203.54.74
   - Click on the instance ID

3. **Open Security Group**
   - In the instance details, click on the "Security" tab
   - Click on the security group link (usually something like sg-xxxxxxxx)

4. **Add HTTPS Rule**
   - Click "Edit inbound rules"
   - Click "Add rule"
   - Configure the new rule:
     - Type: HTTPS
     - Protocol: TCP
     - Port: 443
     - Source: 0.0.0.0/0 (or "Anywhere-IPv4")
   - Click "Save rules"

5. **Verify**
   - The change takes effect immediately
   - Test by visiting: https://54.203.54.74/
   - You'll see a certificate warning (click "Advanced" → "Proceed")

## What This Does:
- Allows HTTPS traffic (port 443) to reach your server
- Your nginx server is already configured and waiting
- The frontend at huntsightings.com will be able to connect

## Current Status:
- ✅ HTTPS server configured and running
- ✅ SSL certificate installed (self-signed)
- ❌ Port 443 blocked by security group (needs your action)
- ✅ Frontend configured to use HTTPS endpoint

Once you open port 443, huntsightings.com will work properly!