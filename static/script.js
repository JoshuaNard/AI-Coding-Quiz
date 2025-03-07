function submitCode() {
    let userCode = editor.getValue();
    let outputElement = document.getElementById("output");
    let loader = document.getElementById("submission-animation");

    // Show animation
    loader.style.display = "flex";

    axios.post('/submit_solution', { code: userCode })
        .then(response => {
            // Hide animation after receiving response
            setTimeout(() => {
                loader.style.display = "none";
                typeWriterEffect(outputElement, "Feedback: " + response.data.feedback, 30);
            }, 1000);
        })
        .catch(error => {
            loader.style.display = "none";
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
