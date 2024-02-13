document.getElementById('enroll_checkbox').addEventListener('change', function() {
    var isChecked = this.checked;
    var url_trimmed = this.name;
    var alertElement = document.getElementById('queryAlert');

    fetch('/handle_checkbox', {
        method: 'POST',
        body: JSON.stringify({
            checked: isChecked,
            url_trimmed: url_trimmed
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            return response.text();
        }
        throw new Error('Network response was not ok.');
    })
    .then(data => {
        // Define the message and class based on the checkbox state
        var message = isChecked ? 'Checkbox is checked. Query completed successfully!' : 'Checkbox is unchecked. Query reverted successfully!';
        var alertClass = isChecked ? 'alert-success' : 'alert-warning';
        
        // Get the alert text span and update its text
        var alertText = document.getElementById('alertText');
        alertText.textContent = message;
    
        // Update the class for the alert
        var alertElement = document.getElementById('queryAlert');
        alertElement.className = `alert ${alertClass} alert-dismissible fade show`;
        alertElement.style.display = 'block'; // Make the alert visible
    })      
    .catch(error => {
        console.error('There has been a problem with your fetch operation:', error);
    });
});
