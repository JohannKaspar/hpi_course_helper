// Listen for the close event on the alert
$('#queryAlert').on('closed.bs.alert', function () {
    // Reset the alert's display style to none after it has been closed.
    this.style.display = 'none';
});
