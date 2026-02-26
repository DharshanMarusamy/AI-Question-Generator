# 📝🤖 AI Question Paper Generator

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Flask](https://img.shields.io/badge/Flask-Backend-black)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue)
![TailwindCSS](https://img.shields.io/badge/TailwindCSS-Frontend-38B2AC)
![AI](https://img.shields.io/badge/AI-xAI%20Grok--3-purple)
![License](https://img.shields.io/badge/License-Academic-green)
![Status](https://img.shields.io/badge/Status-Active-success)

A **full-stack AI-powered web application** that automates the creation of academic **question papers** using **Generative AI** and **Excel-based bulk processing**, aligned with **Bloom’s Taxonomy** and **Course Outcomes (CO)**.

Designed for **faculty members, academic institutions, and engineering education workflows**.

---

## 🚀 Key Highlights

- 🤖 **AI-Generated Questions** using xAI Grok-3  
- 📊 **Excel Bulk Upload & Smart Filtering**
- 🎓 **Bloom’s Taxonomy & CO Mapping**
- 📄 **Professional PDF Question Paper Export**
- 💾 **Persistent SQLite Storage**
- 🎨 **Modern Responsive UI (Tailwind CSS)**

---

## 🧠 Generation Modes

### 🔹 AI Generator Mode
- Dynamic question generation
- Inputs:
  - Subject
  - Topic
  - Difficulty
  - Bloom’s Level
  - Course Outcome
- Real-time question count tracking

### 🔹 Excel Upload Mode
- Upload `.xlsx` question banks
- Filter questions by:
  - Unit
  - Bloom’s Level
  - CO
  - Question Type
- Automated selection logic

---

## 🎓 Educational Compliance

✔ Bloom’s Taxonomy  
✔ Course Outcomes (CO1–CO6)  
✔ Unit-wise categorization  
✔ Marks distribution  
✔ Exam-ready formatting  

---

## 🛠️ Tech Stack

| Layer | Technology |
|------|-----------|
| Frontend | HTML5, Tailwind CSS, JavaScript (ES6+) |
| Backend | Python, Flask, Flask-CORS |
| Database | SQLite3 |
| AI Engine | xAI API (Grok-3 Model) |
| Data Processing | Pandas, Openpyxl |
| PDF Generation | ReportLab |
| Config | python-dotenv |

---
##🏗️ System Architecture
                        ┌────────────────────────────────┐
                        │        Frontend (Client)       │
                        │   HTML + Tailwind CSS + JS     │
                        └───────────────┬────────────────┘
                                        │
                                        │ HTTP Requests (REST API)
                                        ▼
                        ┌────────────────────────────────┐
                        │         Flask Backend          │
                        │        (REST API Layer)        │
                        └───────────────┬────────────────┘
                                        │
               ┌────────────────────────┼────────────────────────┐
               │                        │                        │
               ▼                        ▼                        ▼
     ┌─────────────────┐     ┌─────────────────┐      ┌────────────────────┐
     │   xAI Grok-3    │     │    SQLite DB    │      │   Excel Processor  │
     │   (AI API)      │     │ (Papers & Qns)  │      │ (Pandas/Openpyxl)  │
     └─────────────────┘     └─────────────────┘      └────────────────────┘
               │
               ▼
     ┌──────────────────────────┐
     │  PDF Generator           │
     │  (ReportLab Engine)      │
     └──────────────────────────┘


## 🔍 Architecture Explanation

### 1️⃣ Frontend Layer
- User interacts through a responsive UI built with HTML, Tailwind CSS, and JavaScript  
- Sends HTTP requests to the Flask backend  
- Displays generated questions, filters, and generation status  

---

### 2️⃣ Flask Backend
- Acts as the central processing unit  
- Handles:
  - 🤖 AI-based question generation  
  - 📊 Excel filtering and validation  
  - 💾 Database storage operations  
  - 📄 PDF generation requests  

---

### 3️⃣ AI Integration
- Sends structured prompts to the xAI Grok-3 API  
- Receives dynamically generated questions  
- Processes and stores AI responses  

---

### 4️⃣ Database Layer
- Stores:
  - 📝 Paper metadata  
  - ❓ Questions  
  - 🎓 Tags (Course Outcome, Bloom’s Level, Unit)  
- Maintains relationships between papers and questions  

---

### 5️⃣ PDF Engine
- Formats the final question paper  
- Structures sections, marks, and instructions  
- Generates a downloadable professional PDF using ReportLab  
