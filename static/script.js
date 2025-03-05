function submitCode() {
    let userCode = editor.getValue();

    axios.post('/submit', { code: userCode })
        .then(response => {
            document.getElementById("output").innerText = "Output: " + response.data.output;
        })
        .catch(error => {
            document.getElementById("output").innerText = "Error: " + 
                (error.response ? error.response.data.error : "Something went wrong.");
        });
}

