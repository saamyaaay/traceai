const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  service: 'gmail',
  auth: {
    user: "sarthakjm2284@gmail.com", 
    pass: "rfpajgdrveaivgbr" 
  }
});

transporter.sendMail({
  from: "sarthakjm2284@gmail.com",  
  to: "sarthakjm2284@gmail.com",  
  subject: "✅ Gmail SMTP Test",
  text: "This is a test email from your AML system."
})
.then(() => console.log("✅ Test email sent successfully!"))
.catch(err => console.error("❌ Test email failed:", err.message));
