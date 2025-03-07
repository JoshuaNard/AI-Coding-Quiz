from flask import Flask, render_template, request, jsonify
import subprocess
import random
import uuid
import os
import openai


app = Flask(__name__, template_folder="templates")

# 🔒 Use environment variable for API key (safer than hardcoding)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ensure API key is set
if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key! Set OPENAI_API_KEY as an environment variable.")

# ✅ Generate test cases dynamically
def generate_test_cases():
    """Generates random test cases for a simple problem."""
    cases = []
    for _ in range(3):  # Generate 3 test cases
        a, b = random.randint(1, 100), random.randint(1, 100)
        cases.append({"input": f"{a} {b}", "expected_output": str(a + b)})
    return cases

@app.route('/')
def index():
    """Returns the main page with the problem statement."""
    problem = {
        "title": "Sum of Two Numbers",
        "description": "Write a function that takes two numbers and returns their sum.",
        "test_cases": generate_test_cases()
    }
    return render_template('index.html', problem=problem)

@app.route('/submit_solution', methods=['POST'])
def submit_solution():
    """Receives and evaluates user code."""
    data = request.json
    user_code = data.get("code", "")
    problem = generate_test_cases()

    if not user_code:
        return jsonify({"error": "No code provided"}), 400

    # ✅ Securely execute the user’s code and check results
    result, error = execute_code(user_code, problem)

    if error:
        return jsonify({"error": error}), 400

    # ✅ AI Feedback using OpenAI API
    feedback = analyze_code(user_code)

    return jsonify({"score": result["score"], "feedback": feedback, "output": result["outputs"]})

def execute_code(user_code, test_cases):
    """Runs the user-submitted code securely and checks correctness."""
    file_id = str(uuid.uuid4())[:8]  # Unique temp file ID
    file_name = f"temp_{file_id}.py"
    try:
        with open(file_name, "w") as f:
            f.write(user_code)

        correct = 0
        outputs = []

        for case in test_cases:
            input_data = case["input"]
            expected_output = case["expected_output"]

            process = subprocess.run(
                ["python", file_name],
                input=str(input_data),  # Ensure input is passed as a string
                capture_output=True,
                text=True,
                timeout=2  # Prevent infinite loops
            )
            output = process.stdout.strip()
            outputs.append({"input": input_data, "output": output, "expected": expected_output})

            if output == expected_output:
                correct += 1

        score = round((correct / len(test_cases)) * 5)  # Convert to 1-5 star rating

        return {"score": score, "outputs": outputs}, None

    except Exception as e:
        return None, str(e)

    finally:
        if os.path.exists(file_name):
            os.remove(file_name)

def analyze_code(user_code):
    """Analyzes the submitted code using OpenAI API for structured feedback."""
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)  # ✅ Correct way to initialize OpenAI client

        prompt = f"""
        You are an AI code grader. Evaluate the following Python code based on these criteria:

        **Correctness:** ✅ Does the code work as expected?
        **Efficiency:** ⚡ Is the code optimized and efficient?
        **Best Practices:** 📝 Is the code well-structured and readable?
        **Final Score:** ⭐⭐⭐⭐⭐ (1-5 stars)

        **User Code:**
        ```
        {user_code}
        ```

        Your response must strictly follow this format:

        ---
        **Correctness:** [Your feedback]
        **Efficiency:** [Your feedback]
        **Best Practices:** [Your feedback]
        **Final Score:** ⭐⭐⭐⭐⭐ (1-5 stars)
        ---
        """

        response = client.chat.completions.create(  # ✅ Updated method call
            model="gpt-3.5-turbo",  # ✅ Use latest available model
            messages=[
                {"role": "system", "content": "You are a strict AI code grader. Provide structured feedback in the given format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        feedback = response.choices[0].message.content.strip()

        # ✅ Ensure AI response contains all required sections
        required_sections = ["**Correctness:**", "**Efficiency:**", "**Best Practices:**", "**Final Score:**"]
        if not all(section in feedback for section in required_sections):
            return "Error: AI did not return structured feedback. Please try again."

        return feedback

    except Exception as e:
        return f"Error analyzing code: {str(e)}"


if __name__ == '__main__':
    app.run(debug=True)
