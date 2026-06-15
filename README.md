Project Overview

NutriGuard AI is a smart healthcare and nutrition platform designed to help consumers make informed dietary decisions.

The system allows users to upload food nutrition labels. Using OCR technology, the platform extracts nutritional information such as calories, protein, sugar, sodium, fats, cholesterol, and fiber.

The extracted data is then analyzed against personalized nutritional requirements calculated from the user's age and body weight. An LLM-powered nutrition engine generates recommendations indicating whether the product is suitable for consumption.

The platform also stores historical analyses and sends health alerts for potentially unhealthy products.

User Module
👤 User Features
Registration & Login
Nutrition Label Upload
Personalized Nutrition Analysis
Food Recommendation Engine
Health History Tracking
Risk Assessment Reports
Email Alerts
Dashboard Analytics
AI Components
OCR Engine

Uses:

Tesseract OCR
Pillow (PIL)

Function:

Food Label Image
↓
OCR Extraction
↓
Raw Nutrition Data

Personalized Nutrition Engine

Inputs:

Age
Weight
Extracted Nutritional Values

Calculates:

Daily Calorie Requirements
Protein Intake Limits
Carbohydrate Requirements
Fat Recommendations
Sugar Limits
Sodium Limits
Fiber Requirements
Generative AI Analysis

Powered By:

Groq API
Llama 3.1

The AI evaluates:

Nutritional Safety
Health Risks
Dietary Suitability
Personalized Recommendations
AI Workflow
Step 1: Nutrition Label Upload

User uploads food package image.

Food Label Image
↓
Flask Application

Step 2: OCR Extraction

Image
↓
Tesseract OCR
↓
Nutrition Text

Step 3: Personalized Health Profile

User Inputs:

Age
Weight

System Calculates:

Recommended Calories
Protein Limits
Sugar Limits
Fat Limits
Sodium Limits
Step 4: Nutrition Analysis

OCR Data
+
User Profile
↓
Nutrition Engine

Step 5: Generative AI Evaluation

Nutrition Data
↓
Groq LLM
↓
Health Assessment

Step 6: Risk Identification

Examples:

Excess Sugar
High Sodium
Excess Calories
High Saturated Fat
Low Protein
Poor Fiber Content
Step 7: Decision Generation

Output:

Recommended

or

Not Recommended
Step 8: Health Report

Generated Results:

Safe Factors
Risk Factors
Personalized Reasoning
Daily Nutrition Guidelines
Key Features
OCR-Based Label Reading
Nutrition Label Extraction
Automated Text Recognition
Image-Based Analysis
Personalized Health Analysis
Age-Based Recommendations
Weight-Based Recommendations
Nutritional Requirement Calculation
AI Nutrition Advisor
LLM-Powered Insights
Personalized Health Suggestions
Food Suitability Assessment
Alert System
Email Notifications
Unhealthy Product Warnings
Risk Alerts
Health Tracking
Nutrition History
Previous Analysis Records
User Dashboard Statistics
Technologies Used
Backend
Python
Flask
Artificial Intelligence
Groq API
Llama 3.1
OCR
Tesseract OCR
Image Processing
Pillow (PIL)
Database
SQLite
SQLAlchemy
Authentication
Flask Login
Communication
Flask Mail
Frontend
HTML5
CSS3
JavaScript
Bootstrap
