from flask import Flask, render_template, request, jsonify
import subprocess
import uuid
import os
import openai
import json
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, template_folder="templates")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Stores user attempt times
time_tracking = {}

def generate_question():
    """Generates a simple Python coding question, function signature, and test cases using OpenAI."""
    prompt = """
    Generate a basic Python coding question for beginners.
    Provide a function signature in Python format and 3 test cases as JSON with "input" and "expected_output".
    Also, include a difficulty level (Easy, Medium, Hard).
    Format it exactly like this:
    ---
    Question: <Your generated question>
    Function Signature: <Python function signature>
    Test Cases: <JSON array>
    Difficulty: <Easy/Medium/Hard>
    ---
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an AI generating beginner coding problems and test cases."},
            {"role": "user", "content": prompt}
        ]
    )
    
    text = response.choices[0].message.content.strip()
    print("Raw AI Response:\n", text)  # Debug log
    
    try:
        # Extracting sections using markers
        question_start = text.find("Question:") + len("Question:")
        function_start = text.find("Function Signature:") + len("Function Signature:")
        test_cases_start = text.find("Test Cases:") + len("Test Cases:")
        difficulty_start = text.find("Difficulty:") + len("Difficulty:")
        
        question = text[question_start:function_start-len("Function Signature:")].strip()
        function_signature = text[function_start:test_cases_start-len("Test Cases:")].strip()
        test_cases = json.loads(text[test_cases_start:difficulty_start-len("Difficulty:")].strip())
        difficulty = text[difficulty_start:].strip()
        
        if not question or not function_signature or not test_cases or not difficulty:
            raise ValueError("Incomplete AI response")
        
        return question, function_signature, test_cases, difficulty
    except Exception as e:
        print("Error parsing AI response:", str(e))  # Debug log
        return "Failed to generate a coding challenge.", "def placeholder_function():\n    return None", [], "Easy"

@app.route('/')
def index():
    """Returns the main page with a dynamically generated simple question."""
    question, function_signature, test_cases, difficulty = generate_question()
    
    # Start tracking the time spent on the problem
    problem_id = str(uuid.uuid4())[:8]
    time_tracking[problem_id] = time.time()

    print("Test Cases Sent to Frontend:", test_cases)
    
    problem = {
        "id": problem_id,
        "title": "AI-Generated Beginner Coding Challenge",
        "description": question,
        "function_signature": function_signature,
        "test_cases": test_cases,
        "difficulty": difficulty
    }
    return render_template('index.html', problem=problem)

@app.route('/submit_solution', methods=['POST'])
def submit_solution():
    """Receives and evaluates user code."""
    data = request.json
    user_code = data.get("code", "")
    problem_id = data.get("problem_id", "")
    test_cases = data.get("test_cases", [])
    
    if not user_code:
        return jsonify({"error": "No code provided"}), 400
    
    result, error = execute_code(user_code, test_cases)
    if error:
        return jsonify({"error": error}), 400
    
    elapsed_time = round(time.time() - time_tracking.get(problem_id, time.time()), 2)
    
    feedback = analyze_code(user_code, result["score"])
    
    return jsonify({"score": result["score"], "feedback": feedback, "output": result["outputs"], "time_spent": elapsed_time})

def execute_code(user_code, test_cases):
    """Runs the user-submitted code securely and checks correctness."""
    file_id = str(uuid.uuid4())[:8]
    file_name = f"temp_{file_id}.py"
    
    try:
        with open(file_name, "w") as f:
            f.write(user_code)
            
        correct = 0
        outputs = []
        
        for case in test_cases:
            input_data = json.loads(case.get("input", ""))
            expected_output = case.get("expected_output", "")
            
            process = subprocess.run(
                ["python", file_name],
                input=str(input_data),
                capture_output=True,
                text=True,
                timeout=2
            )
            output = process.stdout.strip()
            outputs.append({"input": input_data, "output": output, "expected": expected_output})
            
            if output == str(expected_output):
                correct += 1
        
        score = round((correct / len(test_cases)) * 5) if test_cases else 0
        return {"score": score, "outputs": outputs}, None
    
    except Exception as e:
        return None, str(e)
    
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

def analyze_code(user_code, correctness_score):
    """Analyzes submitted code using AI for structured feedback."""
    try:
        prompt = f"""
        You are an AI code grader grading this code{user_code}. The correctness score is {correctness_score}/5.
        Provide structured feedback in this format:
        ---
        **Correctness:** [Your feedback]
        **Efficiency:** [Your feedback]
        **Best Practices:** [Your feedback]
        **Final Score:** (1-5 stars)
        ---
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are an AI code grader."},
                      {"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"Error analyzing code: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)