import os
import json
import sys
import pytesseract
from PIL import Image
from groq import Groq
from flask import current_app

# Windows-specific Tesseract path configuration
if sys.platform == 'win32':
    # Common Tesseract installation paths on Windows
    tesseract_paths = [
        r'C:\Users\Admin\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'.format(os.getenv('USERNAME'))
    ]
    
    for path in tesseract_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

def extract_text_from_image(image_path):
    """Extract text from nutrition label using Tesseract OCR"""
    try:
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        current_app.logger.error(f"OCR Error: {str(e)}")
        return None


def calculate_daily_guidelines(age, weight):
    """
    Calculate recommended daily nutritional intake based on age and weight
    Returns a dictionary with recommended ranges for various nutrients
    """
    guidelines = {}
    
    # Base calculations
    # BMR (Basal Metabolic Rate) estimation using simplified formula
    # Calories = 10 × weight(kg) + 6.25 × height(cm) - 5 × age + s
    # Since we don't have height, we use a simplified approach
    
    if age < 18:
        # Children and teenagers
        base_calories = weight * 35  # Higher calorie needs for growth
        protein_per_kg = 1.2
    elif age < 50:
        # Adults
        base_calories = weight * 30
        protein_per_kg = 1.0
    else:
        # Older adults
        base_calories = weight * 28
        protein_per_kg = 1.2  # Higher to prevent muscle loss
    
    # Calorie range (±200 for activity level variation)
    guidelines['calories'] = {
        'min': int(base_calories - 200),
        'max': int(base_calories + 200),
        'unit': 'kcal'
    }
    
    # Protein (grams)
    protein = weight * protein_per_kg
    guidelines['protein'] = {
        'min': int(protein * 0.9),
        'max': int(protein * 1.1),
        'unit': 'g'
    }
    
    # Total Fat (20-35% of calories)
    fat_calories_min = base_calories * 0.20
    fat_calories_max = base_calories * 0.35
    guidelines['total_fat'] = {
        'min': int(fat_calories_min / 9),  # 9 cal per gram of fat
        'max': int(fat_calories_max / 9),
        'unit': 'g'
    }
    
    # Saturated Fat (< 10% of calories)
    sat_fat_max = base_calories * 0.10 / 9
    guidelines['saturated_fat'] = {
        'min': 0,
        'max': int(sat_fat_max),
        'unit': 'g'
    }
    
    # Carbohydrates (45-65% of calories)
    carb_calories_min = base_calories * 0.45
    carb_calories_max = base_calories * 0.65
    guidelines['carbohydrates'] = {
        'min': int(carb_calories_min / 4),  # 4 cal per gram of carbs
        'max': int(carb_calories_max / 4),
        'unit': 'g'
    }
    
    # Sugar (< 10% of calories - WHO recommendation)
    sugar_max = base_calories * 0.10 / 4
    guidelines['sugar'] = {
        'min': 0,
        'max': int(sugar_max),
        'unit': 'g'
    }
    
    # Fiber
    if age < 18:
        fiber = age + 5  # Children: age + 5g
    else:
        fiber = 25 if weight < 70 else 30  # Adults
    guidelines['fiber'] = {
        'min': int(fiber * 0.8),
        'max': int(fiber * 1.2),
        'unit': 'g'
    }
    
    # Sodium (mg)
    if age < 14:
        sodium_max = 1900
    elif age < 50:
        sodium_max = 2300
    else:
        sodium_max = 2000  # Lower for older adults
    guidelines['sodium'] = {
        'min': 0,
        'max': sodium_max,
        'unit': 'mg'
    }
    
    # Trans Fat
    guidelines['trans_fat'] = {
        'min': 0,
        'max': 2,  # As low as possible
        'unit': 'g'
    }
    
    # Cholesterol
    guidelines['cholesterol'] = {
        'min': 0,
        'max': 300,
        'unit': 'mg'
    }
    
    return guidelines


def analyze_nutrition_with_groq(ocr_text, age, weight):
    """Analyze nutrition information using Groq API with age and weight"""
    try:
        api_key = current_app.config.get('GROQ_API_KEY')
        if not api_key:
            raise ValueError("GROQ_API_KEY not configured")
        
        # Calculate daily guidelines
        daily_guidelines = calculate_daily_guidelines(age, weight)
        
        client = Groq(api_key=api_key)
        
        # Create guidelines summary for the prompt
        guidelines_text = f"""
Daily Nutritional Guidelines for this person:
- Age: {age} years
- Weight: {weight} kg
- Recommended Daily Calories: {daily_guidelines['calories']['min']}-{daily_guidelines['calories']['max']} kcal
- Recommended Daily Protein: {daily_guidelines['protein']['min']}-{daily_guidelines['protein']['max']}g
- Recommended Daily Carbs: {daily_guidelines['carbohydrates']['min']}-{daily_guidelines['carbohydrates']['max']}g
- Recommended Daily Total Fat: {daily_guidelines['total_fat']['min']}-{daily_guidelines['total_fat']['max']}g
- Maximum Daily Saturated Fat: {daily_guidelines['saturated_fat']['max']}g
- Maximum Daily Sugar: {daily_guidelines['sugar']['max']}g
- Maximum Daily Sodium: {daily_guidelines['sodium']['max']}mg
- Recommended Daily Fiber: {daily_guidelines['fiber']['min']}-{daily_guidelines['fiber']['max']}g
"""
        
        prompt = f"""You are a nutrition expert analyzing food labels for health compliance.

Consumer Profile:
- Age: {age} years old
- Weight: {weight} kg

{guidelines_text}

Nutritional label text extracted from image:
{ocr_text}

Based on the nutritional information extracted from the label and the person's age and weight profile, provide a comprehensive analysis.

Consider these factors:
- How the product's nutritional content compares to daily recommended intake
- Age-specific nutritional needs
- Weight management considerations
- Sugar, sodium, and saturated fat levels
- Protein content adequacy
- Calorie density
- Fiber content
- Trans fats and cholesterol
- Overall nutritional balance

Return your analysis in the following JSON format ONLY:
{{
  "decision": "Recommended" or "Not Recommended",
  "safe_factors": ["list of positive nutritional aspects - be specific with numbers"],
  "risk_factors": ["list of concerning nutritional aspects - be specific with numbers"],
  "reason": "A detailed explanation considering age ({age}), weight ({weight}kg), and how this product fits or doesn't fit their daily nutritional needs. Be specific and personalized."
}}

Be specific, include actual numbers from the label when possible, and relate findings to their personalized daily guidelines."""

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
            temperature=0.3,
            max_tokens=1500,
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Extract JSON from response (handle markdown code blocks)
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0].strip()
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0].strip()
        
        result = json.loads(response_text)
        
        # Add daily guidelines to result
        result['daily_guidelines'] = daily_guidelines
        
        return result
        
    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON parsing error: {str(e)}")
        daily_guidelines = calculate_daily_guidelines(age, weight)
        return {
            "decision": "Not Recommended",
            "safe_factors": [],
            "risk_factors": ["Unable to parse nutrition data properly"],
            "reason": "Analysis could not be completed due to data parsing issues.",
            "daily_guidelines": daily_guidelines
        }
    except Exception as e:
        current_app.logger.error(f"Groq API Error: {str(e)}")
        daily_guidelines = calculate_daily_guidelines(age, weight)
        return {
            "decision": "Not Recommended",
            "safe_factors": [],
            "risk_factors": ["Analysis failed"],
            "reason": f"Unable to analyze nutrition data: {str(e)}",
            "daily_guidelines": daily_guidelines
        }


def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS