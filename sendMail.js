// sendMail.js
require('dotenv').config()
const nodemailer = require('nodemailer')
const fs = require('fs')
const path = require('path')
console.log(process.env.GMAIL_USER, process.env.GMAIL_PASS.length)

// Usage: node sendMail.js <transaction_id>
const txId = process.argv[2]
if (!txId) {
  console.error("Usage: node sendMail.js <transaction_id>")
  process.exit(1)
}

// Report file path
const reportPath = path.join(__dirname, 'reports', `sar_${txId}.txt`)
if (!fs.existsSync(reportPath)) {
  console.error(`Report not found: ${reportPath}`)
  process.exit(1)
}

// Create transporter
const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: process.env.GMAIL_USER,
    pass: process.env.GMAIL_PASS
  }
})

// Mail options
const mailOptions = {
  from: process.env.FROM_EMAIL,
  to: process.env.TO_EMAIL,
  subject: `SAR Report – Transaction ${txId}`,
  text: `Attached the SAR for transaction ID ${txId}.`,
  attachments: [
    {
      filename: `sar_${txId}.txt`,
      path: reportPath
    }
  ]
}

// Send it
transporter.sendMail(mailOptions)
  .then(info => {
    console.log(`✅ Email sent for TX ${txId}: ${info.response}`)
  })
  .catch(err => {
    console.error(`❌ SMTP error for TX ${txId}:`, err.message)
  })

  