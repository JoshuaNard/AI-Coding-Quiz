from flask import Flask, render_template, request, jsonify
import subprocess
import uuid 
import os

app = Flask(__name__)

problems= {
    1: {
        "title": "Sum of Two Numbers",
        "description": "Write a function that takes two numbers and returns their sum.",
        "input_format": "Two integers a & b",
        "output_format": "An integer representing the sum of a & b",
        "test_cases":[
            {"input": "2 3", "expected_output": 5},
            {"input": "-1 1", "expected_output": 0},
            {"input": "10 20", "expected_output": 30}

        ]
    }   
}

@app.route('/')
def home():
    return render_template("index.html", problem=problems[1])


@app.route('/submit', methods=['POST'])
def sumbit():
    """Returns & evaluates user code"""
    data = request.json
    if not data or "code" not in data:
        return jsonify({"error": "No code provided"}), 400
    
    user_code = data["code"]
    result, error = execute_code(user_code)

    if error:
        return jsonify({"error": error}), 400

    return jsonify(result)



def execute_code(user_code):
    """Runs the users code safely"""
    file_id = str(uuid.uuid4())[:8]
    file_name = f"temp_{file_id}.py"

    try:
        with open(file_name, "w") as f:
            f.write(user_code)

        process = subprocess.run(["python", file_name], capture_output= True, text=True, timeout=2 )
        output = process.stdout.strip()
        error = process.stderr.strip()

        return{"output": output}, error if error else None 
    except Exception as e:
        return None, str(e)
    finally:

        if os.path.exists(file_name):
            os.remove(file_name)
if __name__ == '__main__':
    app.run(debug=True)