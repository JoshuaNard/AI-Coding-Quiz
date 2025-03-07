function submitCode() {
    let userCode = editor.getValue();
    let outputElement = document.getElementById("output");

    // Display "AI is thinking..." animation
    let thinkingText = "AI is analyzing your code";
    outputElement.innerText = thinkingText;
    let dots = 0;
    let thinkingInterval = setInterval(() => {
        dots = (dots + 1) % 4; // Cycle between 0-3 dots
        outputElement.innerText = thinkingText + ".".repeat(dots);
    }, 500);

    axios.post('/submit_solution', { code: userCode })
        .then(response => {
            clearInterval(thinkingInterval); // Stop animation
            typeWriterEffect(outputElement, "Feedback: " + response.data.feedback, 30);
        })
        .catch(error => {
            clearInterval(thinkingInterval); // Stop animation
            outputElement.innerText = "Error: " + 
                (error.response ? error.response.data.error : "Something went wrong.");
        });
}

// Typewriter Effect Function
function typeWriterEffect(element, text, speed) {
    let i = 0;
    element.innerText = ""; // Clear previous text
    function type() {
        if (i < text.length) {
            element.innerText += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    type();
}
