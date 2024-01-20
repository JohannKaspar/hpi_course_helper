document.getElementById('enroll_checkbox').addEventListener('change', function() {
    var isChecked = this.checked;
    var url_trimmed = this.name;
    fetch('/handle_checkbox', {
        method: 'POST',
        body: JSON.stringify({
            checked: isChecked,
            url_trimmed: url_trimmed
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    });
});
