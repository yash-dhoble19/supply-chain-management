import { workflow, node, trigger } from '@n8n/workflow-sdk';

const receiveInquiryRequest = trigger({
  id: '4b6edecd-d363-4750-8ee3-7dacdea39fe4',
  type: 'n8n-nodes-base.webhook',
  version: 2.1,
  config: {
    name: "Receive Inquiry Request",
    parameters: {
      httpMethod: "POST",
      path: "supplier-inquiry",
      options: {
      },
    },
    position: [
      240,
      416,
    ],
  }
});

const getSupplierInfo = node({
  id: '75167559-c88a-484a-9b52-7b30a0fad734',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Get Supplier Info",
    parameters: {
      operation: "select",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "suppliers",
      },
      limit: 1,
      where: {
        values: [
          {
            column: "id",
            value: "={{ $json.body.supplierId }}",
          },
        ],
      },
      options: {
      },
    },
    position: [
      464,
      416,
    ],
  }
});

const generateInquiryEmail = node({
  id: 'cebfab5a-60bd-4d9e-a476-21f0f459bec6',
  type: '@n8n/n8n-nodes-langchain.agent',
  version: 3.1,
  config: {
    name: "Generate Inquiry Email",
    parameters: {
      promptType: "define",
      text: "=Generate a professional supplier inquiry email with the following details:\n\nSupplier: {{ $(\"Get Supplier Info\").item.json.company_name }}\nContact: {{ $(\"Get Supplier Info\").item.json.contact_name }}\nProduct: {{ $(\"Receive Inquiry Request\").item.json.body.productName }}\nQuantity: {{ $(\"Receive Inquiry Request\").item.json.body.quantity }}\nDeadline: {{ $(\"Receive Inquiry Request\").item.json.body.deadline }}\nBudget: ${{ $(\"Receive Inquiry Request\").item.json.body.budget }}\n\nRequest the following information:\n- Price per unit\n- Minimum Order Quantity (MOQ)\n- Lead time for delivery\n- Payment terms\n- Quality certifications\n\nSign as Marcus Chen, Procurement Manager at ChainMind Supply Intelligence.\nUse a professional, courteous tone. Return only the email body text without subject line.",
      options: {
        systemMessage: "You are a professional procurement manager writing supplier inquiry emails. Generate clear, concise, and professional emails.",
      },
    },
    position: [
      688,
      304,
    ],
  }
});

const groqAIModel = node({
  id: 'e6649362-a361-4ef6-baf2-a125d74bd0c4',
  type: '@n8n/n8n-nodes-langchain.lmChatGroq',
  version: 1,
  config: {
    name: "Groq AI Model",
    parameters: {
      model: "llama3-70b-8192",
      options: {
        maxTokensToSample: 2048,
        temperature: 0.7,
      },
    },
    position: [
      768,
      528,
    ],
  }
});

const sendInquiryEmail = node({
  id: '0df94ec5-dfa1-4dd9-b32d-8c93b4f6c34b',
  type: 'n8n-nodes-base.gmail',
  version: 2.2,
  config: {
    name: "Send Inquiry Email",
    parameters: {
      sendTo: "={{ $(\"Get Supplier Info\").item.json.contact_email }}",
      subject: "=Inquiry: {{ $(\"Receive Inquiry Request\").item.json.body.productName }} - ChainMind Supply Intelligence",
      emailType: "text",
      message: "={{ $json.output }}",
      options: {
        senderName: "Marcus Chen - ChainMind Supply Intelligence",
      },
      resource: "message",
      operation: "send",
    },
    position: [
      1040,
      416,
    ],
  }
});

const logSentEmail = node({
  id: 'acfa8a63-2401-462a-83db-5496366fa77e',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Log Sent Email",
    parameters: {
      operation: "insert",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "email_interactions",
      },
      columns: {
        mappingMode: "defineBelow",
        value: {
          supplier_id: "={{ $(\"Receive Inquiry Request\").item.json.body.supplierId }}",
          message_id: "={{ $(\"Send Inquiry Email\").item.json.id }}",
          thread_id: "={{ $(\"Send Inquiry Email\").item.json.threadId }}",
          status: "sent",
          email_type: "inquiry",
          sent_at: "={{ $now.toISO() }}",
          recipient_email: "={{ $(\"Get Supplier Info\").item.json.contact_email }}",
          subject: "=Inquiry: {{ $(\"Receive Inquiry Request\").item.json.body.productName }} - ChainMind Supply Intelligence",
          body: "={{ $(\"Generate Inquiry Email\").item.json.output }}",
          inquiry_details: "={{ JSON.stringify($(\"Receive Inquiry Request\").item.json.body) }}",
        },
      },
      options: {
      },
    },
    position: [
      1328,
      416,
    ],
  }
});

const wait24Hours = node({
  id: 'f8e237eb-4d57-4b35-b312-b1920c6eb446',
  type: 'n8n-nodes-base.wait',
  version: 1.1,
  config: {
    name: "Wait 24 Hours",
    parameters: {
      amount: 24,
      unit: "hours",
    },
    position: [
      1616,
      416,
    ],
  }
});

const checkForReply = node({
  id: '6dd3106b-225e-49fd-a0dd-9d7f5ed724ab',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Check For Reply",
    parameters: {
      operation: "select",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "email_interactions",
      },
      limit: 1,
      where: {
        values: [
          {
            column: "thread_id",
            value: "={{ $(\"Send Inquiry Email\").item.json.threadId }}",
          },
          {
            column: "status",
            value: "reply_received",
          },
        ],
      },
      options: {
      },
    },
    position: [
      1840,
      416,
    ],
  }
});

const replyReceived = node({
  id: '5b0d3588-d708-49dd-a84e-05b8befcaa10',
  type: 'n8n-nodes-base.if',
  version: 2.3,
  config: {
    name: "Reply Received?",
    parameters: {
      conditions: {
        conditions: [
          {
            leftValue: "={{ $json.thread_id }}",
            operator: {
              type: "string",
              operation: "exists",
            },
          },
        ],
      },
      options: {
      },
    },
    position: [
      2064,
      416,
    ],
  }
});

const sendDashboardConfirmation = node({
  id: 'db58994a-e64a-444d-b3f3-ecd3fb1c9476',
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: "Send Dashboard Confirmation",
    parameters: {
      method: "POST",
      url: "https://unreplevined-meritorious-darline.ngrok-free.dev/api/webhooks/inquiry-sent",
      sendBody: true,
      specifyBody: "json",
      jsonBody: "={{ {\n  \"status\": \"success\",\n  \"messageId\": $(\"Send Inquiry Email\").item.json.id,\n  \"threadId\": $(\"Send Inquiry Email\").item.json.threadId,\n  \"recipient\": $(\"Get Supplier Info\").item.json.contact_email,\n  \"timestamp\": $(\"Log Sent Email\").item.json.sent_at,\n  \"replyReceived\": $(\"Check For Reply\").item.json.thread_id ? true : false,\n  \"followUpSent\": $(\"Check For Reply\").item.json.thread_id ? false : true,\n  \"nextReminderTime\": $(\"Check For Reply\").item.json.thread_id ? null : $now.plus({ days: 1 }).toISO()\n} }}",
      options: {
      },
    },
    position: [
      3088,
      416,
    ],
  }
});

const generateFollowupEmail = node({
  id: '02fa90fe-8855-46a3-b9e4-8476fa0f903c',
  type: '@n8n/n8n-nodes-langchain.agent',
  version: 3.1,
  config: {
    name: "Generate Follow-up Email",
    parameters: {
      promptType: "define",
      text: "=Generate a friendly follow-up email for the supplier inquiry sent 24 hours ago.\n\nOriginal inquiry details:\nSupplier: {{ $(\"Get Supplier Info\").item.json.company_name }}\nProduct: {{ $(\"Receive Inquiry Request\").item.json.body.productName }}\nQuantity: {{ $(\"Receive Inquiry Request\").item.json.body.quantity }}\n\nPolitely remind them of the inquiry and request a response. Mention the deadline is approaching. Sign as Marcus Chen, Procurement Manager at ChainMind Supply Intelligence. Keep it brief and professional. Return only the email body text.",
      options: {
        systemMessage: "You are a professional procurement manager writing follow-up emails. Be polite, brief, and professional.",
      },
    },
    position: [
      2288,
      656,
    ],
  }
});

const sendFollowupEmail = node({
  id: '0cf67bac-d53a-4ed7-9115-b3c8e3736d15',
  type: 'n8n-nodes-base.gmail',
  version: 2.2,
  config: {
    name: "Send Follow-up Email",
    parameters: {
      sendTo: "={{ $(\"Get Supplier Info\").item.json.contact_email }}",
      subject: "=Re: Inquiry: {{ $(\"Receive Inquiry Request\").item.json.body.productName }} - ChainMind Supply Intelligence",
      emailType: "text",
      message: "={{ $json.output }}",
      options: {
        senderName: "Marcus Chen - ChainMind Supply Intelligence",
      },
      resource: "message",
      operation: "send",
    },
    position: [
      2640,
      656,
    ],
  }
});

const logFollowupEmail = node({
  id: 'e6ddb041-2a96-4f79-94f7-884ea0251822',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Log Follow-up Email",
    parameters: {
      operation: "insert",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "email_interactions",
      },
      columns: {
        mappingMode: "defineBelow",
        value: {
          supplier_id: "={{ $(\"Receive Inquiry Request\").item.json.body.supplierId }}",
          message_id: "={{ $(\"Send Follow-up Email\").item.json.id }}",
          thread_id: "={{ $(\"Send Follow-up Email\").item.json.threadId }}",
          status: "follow_up_sent",
          email_type: "follow_up",
          sent_at: "={{ $now.toISO() }}",
          recipient_email: "={{ $(\"Get Supplier Info\").item.json.contact_email }}",
          subject: "=Re: Inquiry: {{ $(\"Receive Inquiry Request\").item.json.body.productName }} - ChainMind Supply Intelligence",
          body: "={{ $(\"Generate Follow-up Email\").item.json.output }}",
        },
      },
      options: {
      },
    },
    position: [
      2864,
      656,
    ],
  }
});

const checkGmailEvery5Minutes = trigger({
  id: '9a9977c1-5781-468b-b763-c38a95bc65db',
  type: 'n8n-nodes-base.gmailTrigger',
  version: 1.3,
  config: {
    name: "Check Gmail Every 5 Minutes",
    parameters: {
      pollTimes: {
        item: [
          {
            mode: "everyX",
            value: 5,
            unit: "minutes",
          },
        ],
      },
      simple: false,
      filters: {
        includeSpamTrash: false,
        q: "",
        readStatus: "unread",
        sender: "",
      },
      options: {
        downloadAttachments: false,
      },
    },
    position: [
      240,
      704,
    ],
  }
});

const matchSupplier = node({
  id: '424aed07-0d24-440b-9d4c-ed0202d81992',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Match Supplier",
    parameters: {
      operation: "select",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "suppliers",
      },
      limit: 1,
      where: {
        values: [
          {
            column: "contact_email",
            value: "={{ $json.from.value[0].address }}",
          },
        ],
      },
      options: {
      },
    },
    position: [
      464,
      704,
    ],
  }
});

const extractQuoteInformation = node({
  id: 'a1dbfd83-4f8c-4976-b1dd-ef5641d813dc',
  type: '@n8n/n8n-nodes-langchain.agent',
  version: 3.1,
  config: {
    name: "Extract Quote Information",
    parameters: {
      promptType: "define",
      text: "=Extract the following information from this supplier email:\n\nEmail: {{ $(\"Check Gmail Every 5 Minutes\").item.json.text }}\n\nExtract and return ONLY a JSON object with these fields:\n- pricePerUnit: number (extract the unit price)\n- deliveryDate: string (ISO date format if mentioned)\n- moq: number (minimum order quantity)\n- paymentTerms: string (e.g., \"Net 30\", \"50% upfront\")\n- contactDetails: string (phone or additional contact info)\n\nIf any field is not mentioned, use null. Return ONLY valid JSON, no other text.",
      options: {
        systemMessage: "You are a data extraction assistant. Extract structured information from emails and return only valid JSON.",
      },
    },
    position: [
      688,
      704,
    ],
  }
});

const saveReceivedEmail = node({
  id: '128e068b-57b4-4b97-884a-0c5b9bdd88cd',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Save Received Email",
    parameters: {
      operation: "insert",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "email_interactions",
      },
      columns: {
        mappingMode: "defineBelow",
        value: {
          supplier_id: "={{ $(\"Match Supplier\").item.json.id }}",
          message_id: "={{ $(\"Check Gmail Every 5 Minutes\").item.json.id }}",
          thread_id: "={{ $(\"Check Gmail Every 5 Minutes\").item.json.threadId }}",
          status: "reply_received",
          email_type: "reply",
          received_at: "={{ $(\"Check Gmail Every 5 Minutes\").item.json.date }}",
          sender_email: "={{ $(\"Check Gmail Every 5 Minutes\").item.json.from.value[0].address }}",
          subject: "={{ $(\"Check Gmail Every 5 Minutes\").item.json.subject }}",
          body: "={{ $(\"Check Gmail Every 5 Minutes\").item.json.text }}",
          extracted_data: "={{ $(\"Extract Quote Information\").item.json.output }}",
        },
      },
      options: {
      },
    },
    position: [
      1040,
      704,
    ],
  }
});

const updateSupplierRecord = node({
  id: '4f6b9a9b-3bcc-4886-97e6-3bb62d09e1ff',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Update Supplier Record",
    parameters: {
      operation: "update",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "suppliers",
      },
      columns: {
        mappingMode: "defineBelow",
        value: {
          last_reply_at: "={{ $(\"Check Gmail Every 5 Minutes\").item.json.date }}",
          latest_quote_price: "={{ JSON.parse($(\"Extract Quote Information\").item.json.output).pricePerUnit }}",
          latest_quote_delivery: "={{ JSON.parse($(\"Extract Quote Information\").item.json.output).deliveryDate }}",
        },
      },
      options: {
      },
    },
    position: [
      1328,
      704,
    ],
  }
});

const notifyDashboard = node({
  id: '3bd09c9f-cbf8-4a5a-aa68-ea7100b124c5',
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: "Notify Dashboard",
    parameters: {
      method: "POST",
      url: "https://unreplevined-meritorious-darline.ngrok-free.dev/api/webhooks/supplier-replied",
      sendBody: true,
      specifyBody: "json",
      jsonBody: "={{ {\n  \"supplierId\": $(\"Match Supplier\").item.json.id,\n  \"companyName\": $(\"Match Supplier\").item.json.company_name,\n  \"senderEmail\": $(\"Check Gmail Every 5 Minutes\").item.json.from.value[0].address,\n  \"subject\": $(\"Check Gmail Every 5 Minutes\").item.json.subject,\n  \"receivedAt\": $(\"Check Gmail Every 5 Minutes\").item.json.date,\n  \"emailBody\": $(\"Check Gmail Every 5 Minutes\").item.json.text,\n  \"extractedQuote\": JSON.parse($(\"Extract Quote Information\").item.json.output)\n} }}",
      options: {
      },
    },
    position: [
      1616,
      704,
    ],
  }
});

const markEmailasRead = node({
  id: '23e55157-8b14-4f18-8db4-92344031f5d8',
  type: 'n8n-nodes-base.gmail',
  version: 2.2,
  config: {
    name: "Mark Email as Read",
    parameters: {
      operation: "send",
      messageId: "={{ $(\"Check Gmail Every 5 Minutes\").item.json.id }}",
      resource: "message",
    },
    position: [
      1840,
      704,
    ],
  }
});

const runEveryHour = trigger({
  id: '66637d69-386e-426e-9526-d5da37547d0e',
  type: 'n8n-nodes-base.scheduleTrigger',
  version: 1.3,
  config: {
    name: "Run Every Hour",
    parameters: {
      rule: {
        interval: [
          {
            field: "hours",
          },
        ],
      },
    },
    position: [
      240,
      992,
    ],
  }
});

const findPendingEmails = node({
  id: 'c69c3b08-f34a-4c9c-afb3-f3b0220e2f55',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Find Pending Emails",
    parameters: {
      operation: "executeQuery",
      query: "SELECT ei.*, s.company_name, s.contact_email, s.contact_name\nFROM email_interactions ei\nJOIN suppliers s ON ei.supplier_id = s.id\nWHERE ei.status = 'sent'\nAND ei.sent_at < NOW() - INTERVAL '24 hours'\nAND NOT EXISTS (\n  SELECT 1 FROM email_interactions ei2\n  WHERE ei2.thread_id = ei.thread_id\n  AND ei2.status IN ('reply_received', 'follow_up_sent')\n)",
      options: {
      },
    },
    position: [
      464,
      992,
    ],
  }
});

const doubleCheckReply = node({
  id: '390ef0af-1743-487e-833b-8c3eb8b231bc',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Double Check Reply",
    parameters: {
      operation: "select",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "email_interactions",
      },
      limit: 1,
      where: {
        values: [
          {
            column: "thread_id",
            value: "={{ $json.thread_id }}",
          },
          {
            column: "status",
            value: "reply_received",
          },
        ],
      },
      options: {
      },
    },
    position: [
      752,
      992,
    ],
  }
});

const shouldSendFollowup = node({
  id: 'c0970c3b-293a-433c-b3b6-f838bf69ea75',
  type: 'n8n-nodes-base.if',
  version: 2.3,
  config: {
    name: "Should Send Follow-up?",
    parameters: {
      conditions: {
        conditions: [
          {
            leftValue: "={{ $json.thread_id }}",
            operator: {
              type: "string",
              operation: "notExists",
            },
          },
        ],
      },
      options: {
      },
    },
    position: [
      1040,
      992,
    ],
  }
});

const generateFollowupEmail1 = node({
  id: '2ba21380-4d12-4d48-a715-30f1e774e345',
  type: '@n8n/n8n-nodes-langchain.agent',
  version: 3.1,
  config: {
    name: "Generate Follow-up Email 1",
    parameters: {
      promptType: "define",
      text: "=Generate a friendly follow-up email for a supplier inquiry that has not received a response.\n\nSupplier: {{ $(\"Find Pending Emails\").item.json.company_name }}\nContact: {{ $(\"Find Pending Emails\").item.json.contact_name }}\nOriginal Subject: {{ $(\"Find Pending Emails\").item.json.subject }}\nInquiry Details: {{ $(\"Find Pending Emails\").item.json.inquiry_details }}\nDays Since Sent: {{ Math.floor(($now.toMillis() - new Date($(\"Find Pending Emails\").item.json.sent_at).getTime()) / (1000 * 60 * 60 * 24)) }}\n\nWrite a polite follow-up that:\n- References the original inquiry\n- Restates the key requirements\n- Requests an urgent response within 2-3 days\n- Maintains a professional and courteous tone\n\nSign as Marcus Chen, Procurement Manager at ChainMind Supply Intelligence. Return only the email body text.",
      options: {
        systemMessage: "You are a professional procurement manager writing follow-up emails. Be polite, clear, and professional.",
      },
    },
    position: [
      1264,
      1088,
    ],
  }
});

const sendFollowupEmail1 = node({
  id: '510327f4-2e60-4e26-bdef-a292a288910d',
  type: 'n8n-nodes-base.gmail',
  version: 2.2,
  config: {
    name: "Send Follow-up Email 1",
    parameters: {
      sendTo: "={{ $(\"Find Pending Emails\").item.json.contact_email }}",
      subject: "=Re: {{ $(\"Find Pending Emails\").item.json.subject }}",
      emailType: "text",
      message: "={{ $json.output }}",
      options: {
        senderName: "Marcus Chen - ChainMind Supply Intelligence",
      },
      resource: "message",
      operation: "send",
    },
    position: [
      1616,
      1088,
    ],
  }
});

const markFollowupSent = node({
  id: 'f1a17d77-7500-409b-b055-6e56de2e29d3',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Mark Follow-up Sent",
    parameters: {
      operation: "update",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "email_interactions",
      },
      columns: {
        mappingMode: "defineBelow",
        value: {
          status: "follow_up_sent",
          follow_up_sent_at: "={{ $now.toISO() }}",
        },
      },
      options: {
      },
    },
    position: [
      1840,
      1088,
    ],
  }
});

const logFollowupEmail1 = node({
  id: 'd852137e-b3fa-43e7-9a45-bf025eab5088',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Log Follow-up Email 1",
    parameters: {
      operation: "insert",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "email_interactions",
      },
      columns: {
        mappingMode: "defineBelow",
        value: {
          supplier_id: "={{ $(\"Find Pending Emails\").item.json.supplier_id }}",
          message_id: "={{ $(\"Send Follow-up Email 1\").item.json.id }}",
          thread_id: "={{ $(\"Send Follow-up Email 1\").item.json.threadId }}",
          status: "follow_up_sent",
          email_type: "follow_up",
          sent_at: "={{ $now.toISO() }}",
          recipient_email: "={{ $(\"Find Pending Emails\").item.json.contact_email }}",
          subject: "=Re: {{ $(\"Find Pending Emails\").item.json.subject }}",
          body: "={{ $(\"Generate Follow-up Email 1\").item.json.output }}",
        },
      },
      options: {
      },
    },
    position: [
      2064,
      1088,
    ],
  }
});

const notifyDashboardFollowupSent = node({
  id: '09c90ac6-99a2-4756-8b00-0128c38ee8d7',
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: "Notify Dashboard - Follow-up Sent",
    parameters: {
      method: "POST",
      url: "https://unreplevined-meritorious-darline.ngrok-free.dev/api/webhooks/followup-sent",
      sendBody: true,
      specifyBody: "json",
      jsonBody: "={{ {\n  \"supplierId\": $(\"Find Pending Emails\").item.json.supplier_id,\n  \"companyName\": $(\"Find Pending Emails\").item.json.company_name,\n  \"followUpSent\": true,\n  \"sentAt\": $now.toISO(),\n  \"responseDeadline\": $now.plus({ days: 3 }).toISO(),\n  \"threadId\": $(\"Find Pending Emails\").item.json.thread_id\n} }}",
      options: {
      },
    },
    position: [
      2352,
      1088,
    ],
  }
});

const check48HourEscalation = node({
  id: '014a6b6e-5bdd-4c01-a016-89722bcc66cd',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Check 48-Hour Escalation",
    parameters: {
      operation: "executeQuery",
      query: "SELECT ei.*, s.company_name, s.contact_email\nFROM email_interactions ei\nJOIN suppliers s ON ei.supplier_id = s.id\nWHERE ei.status IN ('sent', 'follow_up_sent')\nAND ei.sent_at < NOW() - INTERVAL '48 hours'\nAND NOT EXISTS (\n  SELECT 1 FROM email_interactions ei2\n  WHERE ei2.thread_id = ei.thread_id\n  AND ei2.status = 'reply_received'\n)",
      options: {
      },
    },
    position: [
      1328,
      896,
    ],
  }
});

const markLowResponsiveness = node({
  id: 'b148a7d6-6828-49b7-b0e1-d582ab4506bb',
  type: 'n8n-nodes-base.postgres',
  version: 2.6,
  config: {
    name: "Mark Low Responsiveness",
    parameters: {
      operation: "update",
      schema: {
        __rl: true,
        mode: "list",
        value: "public",
      },
      table: {
        __rl: true,
        mode: "list",
        value: "suppliers",
      },
      columns: {
        mappingMode: "defineBelow",
        value: {
          responsiveness_status: "low_responsiveness",
          last_escalation_at: "={{ $now.toISO() }}",
        },
      },
      options: {
      },
    },
    position: [
      1616,
      896,
    ],
  }
});

const sendEscalationAlert = node({
  id: '3a160cae-f0c4-4e5c-9a9d-5a4b33cce679',
  type: 'n8n-nodes-base.httpRequest',
  version: 4.4,
  config: {
    name: "Send Escalation Alert",
    parameters: {
      method: "POST",
      url: "https://unreplevined-meritorious-darline.ngrok-free.dev/api/webhooks/escalation-alert",
      sendBody: true,
      specifyBody: "json",
      jsonBody: "={{ {\n  \"alertType\": \"NO_RESPONSE_48H\",\n  \"supplierId\": $json.supplier_id,\n  \"companyName\": $json.company_name,\n  \"threadId\": $json.thread_id,\n  \"hoursSinceInquiry\": 48,\n  \"recommendation\": \"Consider alternative suppliers\",\n  \"escalatedAt\": $now.toISO()\n} }}",
      options: {
      },
    },
    position: [
      1840,
      896,
    ],
  }
});

export default workflow('FJogRQZQSNViU8y5', 'Supplier Inquiry Automation - Workflow 1')
  .add(receiveInquiryRequest).to(getSupplierInfo)
  .add(getSupplierInfo).to(generateInquiryEmail)
  .add(generateInquiryEmail).to(sendInquiryEmail)
  .add(groqAIModel).to(generateInquiryEmail)
  .add(groqAIModel).to(generateFollowupEmail)
  .add(groqAIModel).to(extractQuoteInformation)
  .add(groqAIModel).to(generateFollowupEmail1)
  .add(sendInquiryEmail).to(logSentEmail)
  .add(logSentEmail).to(wait24Hours)
  .add(wait24Hours).to(checkForReply)
  .add(checkForReply).to(replyReceived)
  .add(replyReceived).to(sendDashboardConfirmation)
  .add(replyReceived).to(generateFollowupEmail)
  .add(generateFollowupEmail).to(sendFollowupEmail)
  .add(sendFollowupEmail).to(logFollowupEmail)
  .add(logFollowupEmail).to(sendDashboardConfirmation)
  .add(checkGmailEvery5Minutes).to(matchSupplier)
  .add(matchSupplier).to(extractQuoteInformation)
  .add(extractQuoteInformation).to(saveReceivedEmail)
  .add(saveReceivedEmail).to(updateSupplierRecord)
  .add(updateSupplierRecord).to(notifyDashboard)
  .add(notifyDashboard).to(markEmailasRead)
  .add(runEveryHour).to(findPendingEmails)
  .add(findPendingEmails).to(doubleCheckReply)
  .add(doubleCheckReply).to(shouldSendFollowup)
  .add(shouldSendFollowup).to(generateFollowupEmail1)
  .add(shouldSendFollowup).to(check48HourEscalation)
  .add(generateFollowupEmail1).to(sendFollowupEmail1)
  .add(sendFollowupEmail1).to(markFollowupSent)
  .add(markFollowupSent).to(logFollowupEmail1)
  .add(logFollowupEmail1).to(notifyDashboardFollowupSent)
  .add(check48HourEscalation).to(markLowResponsiveness)
  .add(markLowResponsiveness).to(sendEscalationAlert)
;
// anything
